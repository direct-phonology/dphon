"""
A reuse graph connects all instances of intertextuality between each document
in the Corpus.
"""

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(order=True, frozen=True)
class Match():
    """
    matches connect two documents and store the indices of the corresponding
    sequences between them.
    """
    doc1: int
    doc2: int
    pos1: slice
    pos2: slice

    def other(self, doc: int) -> int:
        """Given one document ID, return the other this match connects."""
        if doc == self.doc1:
            return self.doc2
        if doc == self.doc2:
            return self.doc1
        raise ValueError(f"Invalid document ID: {doc}")
    

class ReuseGraph():
    """
    In a reuse graph, nodes are documents and edges are matches between two
    documents.
    """

    _docs: int
    _matches: int
    _graph: List[List[Match]]

    def __init__(self, docs: int):
        """
        Create a new graph with a given number of documents and zero matches.
        """
        if docs < 0:
            raise ValueError("Graph order must be a positive integer")

        self._docs = docs
        self._matches = 0
        self._graph = [[] for _ in range(docs)]

    def validate_doc(self, doc: int):
        """
        Check that a document ID is valid in the context of this graph.
        """
        if doc < 0 or doc > self._docs + 1:
            raise ValueError(f"Invalid document ID: {doc}")

    def add_match(self, doc1: int, doc2: int, pos1: slice, pos2: slice):
        """
        Create a new match and add it to the graph.
        """
        self.validate_doc(doc1)
        self.validate_doc(doc2)

        # store in both adjacency lists, but increment count once
        match = Match(doc1, doc2, pos1, pos2)
        self._graph[match.doc1].append(match)
        self._graph[match.doc2].append(match)
        self._matches += 1

    def doc_matches(self, doc: int) -> Iterable[Match]:
        """
        Return an iterable of all the matches that connect to a given document.
        Matches are ordered by document ID and then by location.
        """
        self.validate_doc(doc)
        return (match for match in sorted(self._graph[doc]))

    def connected(self, doc1: int, doc2: int) -> bool:
        """
        Check whether any match connects two given documents.
        """
        self.validate_doc(doc1)
        self.validate_doc(doc2)
        return doc2 in [m.other(doc1) for m in self._graph[doc1]]

    def docs(self) -> int:
        """
        Get the total number of documents in the graph.
        """
        return self._docs

    def matches(self) -> int:
        """
        Get the total number of matches in the graph.
        """
        return self._matches
