# -*- coding: utf-8 -*-
"""Classes and types for pairwise match alignment."""

from abc import ABC, abstractmethod
from typing import Mapping, Optional, Tuple, Union, List

from lingpy.align.pairwise import sw_align
from spacy.tokens import Span

from dphon.match import Match

# Lingpy scoring matrices: a × b = 1.0 -> { ("a", "b"): 1.0, ("b", "a"): 1.0 }
# Matrix cells are represented as tuples; both a × b and b × a need to exist
Scorer_T = Mapping[Tuple[str, str], float]

# Lingpy aligner input type: tuple of str | list of str | str
Seq_T = Union[Tuple[str], List[str], str]


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

    def _get_seqs(self, match: Match) -> Tuple[Seq_T, Seq_T]:
        """Get the two sequences to compare."""
        return match.utxt.text, match.vtxt.text

    def __call__(self, match: Match) -> Match:
        """Perform the alignment and use it to modify the provided match.

        The updated match uses the values calculated from alignment to adjust
        the start and end points of its sequences, as well as storing the score
        and sequence texts calculated for the alignment."""

        # compute the alignment and keep non-aligned regions
        (lu, cu, ru), (lv, cv, rv), score = sw_align(*self._get_seqs(match),
                                                     self.scorer)

        # use lengths of non-aligned regions to move the sequence boundaries
        # [...] ["A", "B", "C"] [...]
        # ---->                <----
        u, v = match.utxt.doc, match.vtxt.doc
        utxt = u[match.utxt.start + len(lu):match.utxt.end - len(ru)]
        vtxt = v[match.vtxt.start + len(lv):match.vtxt.end - len(rv)]

        # use the gaps in the alignment to construct a new sequence of token
        # texts, inserting a spacer wherever the aligner created one
        u_ptr = 0
        v_ptr = 0
        au = []
        av = []
        for i in range(max(len(utxt), len(vtxt))):
            if cu[i] != "-":
                au.append(utxt[u_ptr].text)
                u_ptr += 1
            else:
                au.append("-")
            if cv[i] != "-":
                av.append(vtxt[v_ptr].text)
                v_ptr += 1
            else:
                av.append("-")

        # trim back the sequence boundaries further to remove any non-alphanum.
        # tokens from the start and end of both alignment and orig. sequence
        while not au[-1].isalnum() or not av[-1].isalnum():
            utxt, vtxt, au, av = utxt[:-1], vtxt[:-1], au[:-1], av[:-1]
        while not au[0].isalnum() or not av[0].isalnum():
            utxt, vtxt, au, av = utxt[1:], vtxt[1:], au[1:], av[1:]

        # create a new match with alignment info and adjusted boundaries
        return Match(match.u, match.v, utxt, vtxt, score, au, av)


class SmithWatermanPhoneticAligner(SmithWatermanAligner):
    """Local alignment using phonetic values provided by a Phonemes instance."""

    def __init__(self, scorer: Scorer_T = None) -> None:
        # error if phonetic information isn't available
        if not Span.has_extension("phonemes"):
            raise RuntimeError("Phonemes component not available")
        super().__init__(scorer=scorer)

    def _get_seqs(self, match: Match) -> Tuple[Seq_T, Seq_T]:
        """Get the phonemes of the two sequences for comparison."""
        # combine the phonemes for each token into a single string; if there's
        # no phonetic content, use the token text in place of the phonemes
        return (
            ["".join([p or "" for p in t._.phonemes]) or t.text for t in match.utxt],
            ["".join([p or "" for p in t._.phonemes]) or t.text for t in match.vtxt],
        )
