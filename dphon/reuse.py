#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for analyzing text reuse."""

from functools import cached_property
from itertools import combinations, groupby
from typing import Callable, Iterable, Iterator

from networkx import MultiGraph, create_empty_copy
from rich.console import Console, ConsoleOptions, RenderResult
from rich.progress import BarColumn, Progress, SpinnerColumn
from spacy.tokens import Doc, Span

from .align import Aligner
from .console import err_console
from .extend import Extender, extend_matches
from .match import Match


class MatchGroup:
    """A group of matches with common bounds in a single document."""

    def __init__(
        self, doc: Doc, start: int, end: int, matches: Iterable[Match]
    ) -> None:
        self.doc = doc
        self.start = start
        self.end = end
        self.matches = list(matches)

    def __len__(self) -> int:
        return len(self.matches)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Format the group for display in console."""
        render_results = []

        # render the "anchor" span first (i.e., the span that all matches share)
        render_results += [
            f"[bold]{self.doc._.id}[/bold] ({self.start}–{self.end-1})：",
            console.highlighter.format_span(self.anchor_span),
            console.highlighter.transcribe_span(self.anchor_span),
        ]

        # render the non-anchor spans from each match in the group
        for i, match in enumerate(self.matches):
            span = self.non_anchor_span(match)
            alignment = self.non_anchor_alignment(match)
            anchor_alignment = self.anchor_alignment(match)
            render_results += [
                f"{i + 1}. {span.doc._.id} ({span.start}–{span.end-1})：",
                console.highlighter.format_span(
                    span, self.anchor_span, alignment, anchor_alignment
                ),
                console.highlighter.transcribe_span(span),
            ]

        return render_results

    @cached_property
    def anchor_span(self) -> Span:
        """Get the anchor span for the group."""
        return self.doc[self.start : self.end]

    def anchor_alignment(self, match: Match) -> str:
        """Get the anchor alignment for a given match."""
        if match.u == self.doc._.id:
            return match.au
        if match.v == self.doc._.id:
            return match.av
        raise ValueError("Match does not belong to document.", match, self.doc)

    def non_anchor_span(self, match: Match) -> Span:
        """Get the non-anchor span for a given match."""
        if match.u == self.doc._.id:
            return match.vtxt
        if match.v == self.doc._.id:
            return match.utxt
        raise ValueError("Match does not belong to document.", match, self.doc)

    def non_anchor_alignment(self, match: Match) -> str:
        """Get the non-anchor alignment for a given match."""
        if match.u == self.doc._.id:
            return match.av
        if match.v == self.doc._.id:
            return match.au
        raise ValueError("Match does not belong to document.", match, self.doc)


class MatchGraph:
    _G: MultiGraph

    def __init__(self) -> None:
        self._G = MultiGraph()
        self.progress = Progress(
            "[progress.description]{task.description}",
            SpinnerColumn(),
            "[progress.description]{task.fields[u]} × {task.fields[v]}",
            BarColumn(bar_width=None),
            "{task.completed}/{task.total}",
            "{task.percentage:>3.1f}%",
            console=err_console,
            transient=True,
        )

    @property
    def matches(self) -> Iterator[Match]:
        """Iterator over all matches in the graph."""
        return (Match(**data) for _u, _v, data in self._G.edges(data=True))

    @property
    def docs(self) -> Iterator[Doc]:
        """Iterator over all docs in the graph."""
        return (doc for _label, doc in self._G.nodes(data="doc"))

    def number_of_matches(self) -> int:
        """Total number of matches in the graph."""
        return self._G.number_of_edges()

    def number_of_docs(self) -> int:
        """Total number of documents in the graph."""
        return self._G.number_of_nodes()

    def add_doc(self, doc: Doc, label: str = None) -> None:
        """Add a single document to the graph."""
        doc_id = label or doc._.id
        if not doc_id:
            raise ValueError("Document must have an identifier.", doc)
        doc._.id = doc_id
        self._G.add_node(doc_id, doc=doc)

    def add_docs(self, docs: Iterable[Doc]) -> None:
        """Add a collection of documents to the graph."""
        [self.add_doc(doc) for doc in docs]

    def add_match(self, match: Match) -> None:
        """Add a single match to the graph."""
        self._G.add_edge(match.u, match.v, **match._asdict())

    def add_matches(self, matches: Iterable[Match]) -> None:
        """Add a collection of matches to the graph."""
        [self.add_match(match) for match in matches]

    def extend(self, extender: Extender) -> None:
        """Extend all matches in the graph using a provided strategy."""
        # track progress
        task = self.progress.add_task(
            "extending", u="", v="", total=self.number_of_matches()
        )

        # create a new graph without matches and add each extended match to it
        G = create_empty_copy(self._G)
        with self.progress:
            for u, v in combinations(self._G.nodes, 2):
                edges = self._G.get_edge_data(u, v)
                if edges:
                    self.progress.update(task, u=u, v=v)
                    matches = [Match(**data) for data in edges.values()]
                    extended = extend_matches(matches, extender)
                    G.add_edges_from([(m.u, m.v, m._asdict()) for m in extended])
                    self.progress.update(task, advance=len(edges))
        self._G = G
        self.progress.remove_task(task)

    def align(self, align: Aligner) -> None:
        """Align all matches in the graph using a provided strategy."""
        # track progress
        task = self.progress.add_task(
            "aligning", u="", v="", total=self.number_of_matches()
        )

        # create a new graph without matches and add each aligned match to it
        G = create_empty_copy(self._G)
        with self.progress:
            for u, v in combinations(self._G.nodes, 2):
                edges = self._G.get_edge_data(u, v)
                if edges:
                    self.progress.update(task, u=u, v=v)
                    matches = [Match(**data) for data in edges.values()]
                    aligned = [align(match) for match in matches]
                    G.add_edges_from([(m.u, m.v, m._asdict()) for m in aligned])
                    self.progress.update(task, advance=len(edges))
        self._G = G
        self.progress.remove_task(task)

    def group(self) -> None:
        """Group all matches in the graph by their shared spans."""
        # track progress
        task = self.progress.add_task(
            "grouping", u="", v="", total=self.number_of_matches()
        )

        # iterate through each document and group all matches that target it
        with self.progress:
            for doc in self.docs:
                self.progress.update(task, u=doc)
                edges = self._G.edges(doc._.id, data=True)
                matches = [Match(**data) for _u, _v, data in edges]
                for span, group in groupby(
                    sorted(matches, key=_bounds_in(doc)), key=_bounds_in(doc)
                ):
                    doc._.groups.append(MatchGroup(doc, span[0], span[1], group))
                self.progress.update(task, advance=len(edges))
        self.progress.remove_task(task)

    def filter(self, predicate: Callable[[Match], bool]) -> None:
        """Filter all matches in the graph using a provided predicate."""
        G = create_empty_copy(self._G)
        filtered = filter(predicate, self.matches)
        G.add_edges_from([(m.u, m.v, m._asdict()) for m in filtered])
        self._G = G


# helper for getting bounds of a match in a given document
def _bounds_in(doc):
    def _bounds(match):
        if match.utxt.doc == doc:
            return match.utxt.start, match.utxt.end
        if match.vtxt.doc == doc:
            return match.vtxt.start, match.vtxt.end
        raise ValueError("Match does not belong to document.", match, doc)

    return _bounds
