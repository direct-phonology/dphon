"""Classes and functions for analyzing text reuse."""

from itertools import combinations
from typing import Iterable, Iterator, Tuple, Callable

from networkx import MultiGraph, create_empty_copy
from spacy.tokens import Doc

from dphon.align import Aligner
from dphon.extend import Extender, extend_matches
from dphon.match import Match


class MatchGraph():

    _G: MultiGraph

    def __init__(self) -> None:
        self._G = MultiGraph()

    @property
    def matches(self) -> Iterator[Match]:
        """Iterator over all matches in the graph."""
        return (Match(**data) for _u, _v, data in self._G.edges(data=True))

    @property
    def docs(self) -> Iterator[Doc]:
        """Iterator over all docs in the graph."""
        return (doc for _label, doc in self._G.nodes(data="doc"))

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
        G = create_empty_copy(self._G)
        for u, v in combinations(self._G.nodes, 2):
            matches = [Match(**data)
                       for _u, _v, data in self._G.edges((u, v), data=True)]
            extended = extend_matches(matches, extender)
            G.add_edges_from([(m.u, m.v, m._asdict()) for m in extended])
        self._G = G

    def align(self, align: Aligner) -> None:
        """Align all matches in the graph using a provided strategy."""
        G = create_empty_copy(self._G)
        aligned = [align(match) for match in self.matches]
        G.add_edges_from([(m.u, m.v, m._asdict()) for m in aligned])
        self._G = G

    def filter(self, predicate: Callable[[Match], bool]) -> None:
        """Filter all matches in the graph using a provided predicate."""
        G = create_empty_copy(self._G)
        filtered = filter(predicate, self.matches)
        G.add_edges_from([(m.u, m.v, m._asdict()) for m in filtered])
        self._G = G
