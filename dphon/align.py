# -*- coding: utf-8 -*-
"""Classes and types for pairwise match alignment."""

from abc import ABC, abstractmethod
from typing import Tuple, Mapping, List, Optional

from lingpy.align.pairwise import sw_align

from dphon.match import Match

# Lingpy scoring matrices: a × b = 1.0 -> { ("a", "b"): 1.0, ("b", "a"): 1.0 }
# Matrix cells are represented as tuples; both a × b and b × a need to exist
Scorer_T = Mapping[Tuple[str, str], float]

# Match alignment results: (["A", "B", "C"], ["A", "B", "C"])
# Set of two center aligned portions from sequences
Alignment_T = Tuple[List[str], List[str]]


class Aligner(ABC):
    """Abstract class; implements pairwise alignment."""

    @abstractmethod
    def __call__(self, match: Match) -> Match:
        """Align and return a match."""
        raise NotImplementedError


class SmithWatermanAligner(Aligner):
    """Local alignment with an optional custom scoring matrix."""

    scorer: Optional[Scorer_T]

    def __init__(self, scorer: Scorer_T = None) -> None:
        self.scorer = scorer

    def __call__(self, match: Match) -> Match:
        """Perform the alignment and use it to modify the provided match.

        The updated match uses the values calculated from alignment to adjust
        the start and end points of its sequences, as well as storing the score
        and sequence texts calculated for the alignment."""

        # compute the alignment and keep non-aligned regions
        (bu, cu, au), (bv, cv, av), score = sw_align(match.utxt.text,
                                                     match.vtxt.text,
                                                     self.scorer)

        # use lengths of non-aligned regions to move the sequence boundaries
        # [...] ["A", "B", "C"] [...]
        # ---->                <----
        u, v = match.utxt.doc, match.vtxt.doc
        utxt = u[match.utxt.start + len(bu):match.utxt.end - len(au)]
        vtxt = v[match.vtxt.start + len(bv):match.vtxt.end - len(av)]

        # create a new match with alignment info and adjusted boundaries
        au, av = map("".join, (cu, cv))
        return Match(match.u, match.v, utxt, vtxt, score, au, av)
