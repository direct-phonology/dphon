"""
A reuse graph connects all instances of intertextuality between each document
in the Corpus.
"""

from collections import deque
from dataclasses import dataclass
from typing import Iterable, List, Deque


@dataclass(order=True)
class Match():
    """
    Matches connect two documents and store the indices of the corresponding
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

        # initialize with an empty deque for each doc's match list
        self._docs = docs
        self._matches = 0
        self._graph = [[] for _ in range(docs)]

    def validate_doc(self, doc: int) -> None:
        """
        Check that a document ID is valid in the context of this graph.
        """
        if doc < 0 or doc >= self._docs:
            raise ValueError(f"Invalid document ID: {doc}")

    def add_match(self, doc1: int, doc2: int, pos1: slice, pos2: slice) -> None:
        """
        Create a new match and add it to the graph.
        """
        self.validate_doc(doc1)
        self.validate_doc(doc2)

        # store in both adjacency lists, but increment count once
        # FIXME ensure this is a reference and not a clone!
        match = Match(doc1, doc2, pos1, pos2)
        self._graph[match.doc1].append(match)
        self._graph[match.doc2].append(match)
        self._matches += 1

    def doc_matches(self, doc: int) -> Iterable[Match]:
        """
        Return an iterable of all the matches that connect to a given document.
        Matches are ordered successively by:
            - target document
            - position in source document
            - position in target document
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

    def _condense_doc(self, doc: int) -> None:
        """
        For a single document, combine matches that are overlapping, so that
        only maximal matches are left in the graph.
        """

        

    def condense(self) -> None:
        """
        Combine matches that are overlapping, so that only maximal matches are
        left in the graph.
        """
        for doc, matches in enumerate(self._graph):
            if len(matches) == 0:
                continue

            # FIXME add comment here
            new_matches: List[Match] = []
            stack: List[Match] = []

            # pull matches off of the old list and compare to top of stack
            while len(matches) > 0:
                current = matches.popleft()
                compare = stack[0]

                # if docs are different, reset everything
                if compare.doc2 != compare.doc2:
                    pass

                #

            # store new list, replacing old one
            self._graph[doc] = new_matches
