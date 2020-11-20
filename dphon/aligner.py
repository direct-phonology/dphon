# -*- coding: utf-8 -*-
"""Classes and types for pairwise match alignment."""

from abc import ABC, abstractmethod
from typing import Tuple, Mapping, List, Optional

from lingpy.align.pairwise import sw_align

from dphon.match import Match

# Lingpy scoring matrices: a × b = 1.0 -> { ("a", "b"): 1.0, ("b", "a"): 1.0 }
# Matrix cells are represented as tuples; both a × b and b × a need to exist
Scorer_T = Mapping[Tuple[str, str], float]

# Single local alignment: "...ABC..." -> ([...], ["A", "B", "C"], [...])
# Center section represents main aligned portion with highest similarity
Aligned_T = Tuple[List[str], List[str], List[str]]

# Match alignment results with score: (([], [ABC], []), ([], [ABC], []), 1.0)
# Combines alignments for two sequences with the total score of the alignment
Alignment_T = Tuple[Aligned_T, Aligned_T, float]


class Aligner(ABC):
    """Abstract class; implements pairwise alignment via the align() method."""

    @abstractmethod
    def align(self, match: Match) -> Match:
        """Return an aligned copy of a match. Should not mutate its argument."""
        raise NotImplementedError


class SmithWatermanAligner(Aligner):
    """Local alignment with an optional custom scoring matrix."""

    scorer: Optional[Scorer_T]

    def __init__(self, scorer: Scorer_T = None) -> None:
        self.scorer = scorer

    def get_alignment(self, match: Match) -> Alignment_T:
        """Return a Smith-Waterman alignment of the match sequences."""
        return sw_align(match.left.text, match.right.text, self.scorer)

    def align(self, match: Match) -> Match:
        """Perform the alignment and use it to create and return a new match.

        The new match uses the values calculated from alignment to adjust the
        start and end points of its sequences, as well as storing the score
        and sequence texts calculated for the alignment."""

        # compute the alignment and keep non-aligned regions
        (bl, cl, al), (br, cr, ar), score = self.get_alignment(match)

        # use lengths of non-aligned regions to move the sequence boundaries
        # [...] ["A", "B", "C"] [...]
        # ---->                <----
        return Match(
            match.left.doc[match.left.start + len(bl):
                           match.left.end - len(al)],
            match.right.doc[match.right.start + len(br):
                            match.right.end - len(ar)],
            (cl, cr),   # alignment text
            score       # alignment score
        )
