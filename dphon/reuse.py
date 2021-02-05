#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for analyzing text reuse."""

from itertools import combinations
from typing import Callable, Iterable, Iterator, Tuple

from networkx import MultiGraph, create_empty_copy
from rich.progress import Progress, BarColumn, SpinnerColumn
from spacy.tokens import Doc

from .align import Aligner
from .extend import Extender, extend_matches
from .match import Match


class MatchGraph():

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

    def add_doc(self, label: str, doc: Doc) -> None:
        """Add a single document to the graph."""
        self._G.add_node(label, doc=doc)

    def add_docs(self, docs: Iterable[Tuple[str, Doc]]) -> None:
        """Add a collection of documents to the graph."""
        self._G.add_nodes_from(((label, {"doc": doc}) for label, doc in docs))

    def add_match(self, match: Match) -> None:
        """Add a single match to the graph."""
        self._G.add_edge(match.u, match.v, **match._asdict())

    def add_matches(self, matches: Iterable[Match]) -> None:
        """Add a collection of matches to the graph."""
        self._G.add_edges_from([(m.u, m.v, m._asdict()) for m in matches])

    def extend(self, extender: Extender) -> None:
        """Extend all matches in the graph using a provided strategy."""
        # track progress
        task = self.progress.add_task(
            "extending", u="", v="", total=self.number_of_matches())

        # create a new graph without matches and add each extended match to it
        G = create_empty_copy(self._G)
        with self.progress:
            for u, v in combinations(self._G.nodes, 2):
                edges = self._G.get_edge_data(u, v)
                if edges:
                    self.progress.update(task, u=u, v=v)
                    matches = [Match(**data) for data in edges.values()]
                    extended = extend_matches(matches, extender)
                    G.add_edges_from([(m.u, m.v, m._asdict())
                                      for m in extended])
                    self.progress.update(task, advance=len(edges))
        self._G = G
        self.progress.remove_task(task)

    def align(self, align: Aligner) -> None:
        """Align all matches in the graph using a provided strategy."""
        # track progress
        task = self.progress.add_task(
            "aligning", u="", v="", total=self.number_of_matches())

        # create a new graph without matches and add each aligned match to it
        G = create_empty_copy(self._G)
        with self.progress:
            for u, v in combinations(self._G.nodes, 2):
                edges = self._G.get_edge_data(u, v)
                if edges:
                    self.progress.update(task, u=u, v=v)
                    matches = [Match(**data) for data in edges.values()]
                    aligned = [align(match) for match in matches]
                    G.add_edges_from([(m.u, m.v, m._asdict())
                                      for m in aligned])
                    self.progress.update(task, advance=len(edges))
        self._G = G
        self.progress.remove_task(task)

    def filter(self, predicate: Callable[[Match], bool]) -> None:
        """Filter all matches in the graph using a provided predicate."""
        G = create_empty_copy(self._G)
        filtered = filter(predicate, self.matches)
        G.add_edges_from([(m.u, m.v, m._asdict()) for m in filtered])
        self._G = G
