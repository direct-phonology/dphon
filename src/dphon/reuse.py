#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for analyzing text reuse."""

from collections import defaultdict
from functools import cached_property
from itertools import combinations
from typing import Callable, Iterable, Iterator, List

from networkx import Graph, MultiGraph, connected_components, create_empty_copy
from rich.console import Console, ConsoleOptions, RenderResult
from rich.progress import BarColumn, Progress, SpinnerColumn
from rich.table import Table
from spacy.tokens import Doc, Span

from .align import Aligner
from .console import err_console
from .extend import Extender, extend_matches
from .match import Match


class MatchGroup:
    """A group of matches across several documents."""

    def __init__(self, matches: Iterable[Match]) -> None:
        self.matches = list(sorted(set(matches)))
        if not self.matches:
            raise ValueError("Group must contain at least one match.", self)
        
        # Create internal list of spans and presort by aligned text
        self.spans = set()
        for match in self.matches:
            self.spans.add((match.utxt, "".join(match.au)))
            self.spans.add((match.vtxt, "".join(match.av)))
        self.spans = list(sorted(self.spans, key=lambda x: x[1]))

        # Select the "anchor" span which identifies the group
        self.anchor_span, self.anchor_alignment = self.spans[0]
        self.doc = self.anchor_span.doc
        self.start = self.anchor_span.start
        self.end = self.anchor_span.end

    def __key(self) -> tuple:
        return tuple(self.matches)

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, value: object) -> bool:
        if isinstance(value, MatchGroup):
            return self.matches == value.matches
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self.matches)

    def __repr__(self) -> str:
        return f"<MatchGroup ({len(self)} matches)>"

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Format the group for display in console."""
        table = Table(show_header=False, box=None)
        table.add_column("doc", no_wrap=True)
        table.add_column("bounds")
        table.add_column("text")
        table.add_column("transcription")

        # render the "anchor" span first
        table.add_row(
            self.doc._.id,
            f"{self.start}–{self.end-1}",
            console.highlighter.format_span(self.anchor_span),
            console.highlighter.transcribe_span(self.anchor_span),
        )

        # render the non-anchor spans relative to the anchor
        for span, alignment in self.spans[1:]:
            table.add_row(
                span.doc._.id,
                f"{span.start}–{span.end-1}",
                console.highlighter.format_span(
                    span, self.anchor_span, alignment, self.anchor_alignment
                ),
                console.highlighter.transcribe_span(span),
            )

        return [table]

    @cached_property
    def anchor_span(self) -> Span:
        """Get the anchor span for the group."""
        return self.doc[self.start : self.end]

    @cached_property
    def graphic_similarity(self) -> float:
        """Average of graphic similarities for all matches in the group."""
        return sum(m.graphic_similarity for m in self.matches) / len(self.matches)

    @cached_property
    def phonetic_similarity(self) -> float:
        """Average of phonetic similarities for all matches in the group."""
        return sum(m.phonetic_similarity for m in self.matches) / len(self.matches)

    @cached_property
    def weighted_score(self) -> float:
        """Average of weighted scores for all matches in the group."""
        return sum(m.weighted_score for m in self.matches) / len(self.matches)


class MatchGraph:
    _G: MultiGraph

    def __init__(self) -> None:
        self._G = MultiGraph()
        self.groups: List[MatchGroup] = []
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

    @property
    def number_of_matches(self) -> int:
        """Total number of matches in the graph."""
        return self._G.number_of_edges()

    @property
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
            "extending", u="", v="", total=self.number_of_matches
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
            "aligning", u="", v="", total=self.number_of_matches
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
            "grouping", u="", v="", total=self.number_of_matches
        )
        groups = set()

        # create a map of match bounds to matches containing those bounds
        bounds_to_matches = defaultdict(set)
        for match in self.matches:
            u_key = (match.u, match.utxt.start, match.utxt.end)
            v_key = (match.v, match.vtxt.start, match.vtxt.end)
            bounds_to_matches[u_key].add(match)
            bounds_to_matches[v_key].add(match)
            self.progress.update(task, advance=1)

        # matches that don't share bounds become their own groups; for the
        # others, group matches that share bounds together
        grouped_matches = []
        for match_set in bounds_to_matches.values():
            if len(match_set) == 1:
                groups.add(MatchGroup(match_set))
            else:
                grouped_matches.append(match_set)

        # create a new undirected graph where nodes are matches and an edge
        # indicates that two matches share a span (i.e., are in the same group)
        G = Graph()
        for match_set in grouped_matches:
            for u, v in combinations(match_set, 2):
                G.add_edge(u, v)

        # groups are connected components in the new graph
        for group in connected_components(G):
            groups.add(MatchGroup(group))

        # store the groups at the top level
        self.groups = list(groups)

    def filter(self, predicate: Callable[[Match], bool]) -> None:
        """Filter all matches in the graph using a provided predicate."""
        G = create_empty_copy(self._G)
        filtered = filter(predicate, self.matches)
        G.add_edges_from([(m.u, m.v, m._asdict()) for m in filtered])
        self._G = G
