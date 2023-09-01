#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and types for pairwise match alignment."""

import logging
from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Tuple, Union

from lingpy.align.pairwise import sw_align
from spacy.tokens import Span

from .match import Match

# Lingpy scoring matrices: a × b = 1.0 -> { ("a", "b"): 1.0, ("b", "a"): 1.0 }
# Matrix cells are represented as tuples; both a × b and b × a need to exist
Scorer_T = Mapping[Tuple[str, str], float]

# Lingpy aligner input type: tuple of str | list of str | str
Seq_T = Union[Tuple[str], List[str], str]


class Aligner(ABC):
    """Abstract class; implements pairwise alignment.

    Override to implement __call__ and define gap_char, the character used to
    represent alignment gaps."""

    gap_char: str

    @abstractmethod
    def __call__(self, match: Match) -> Match:
        """Align and return a match."""
        raise NotImplementedError


class SmithWatermanAligner(Aligner):
    """Local alignment with an optional custom scoring matrix."""

    gap_char: str
    scorer: Optional[Scorer_T]

    def __init__(self, scorer: Scorer_T = None, gap_char: str = "-") -> None:
        self.scorer = scorer
        self.gap_char = gap_char
        logging.info(f'using {self.__class__} with gap_char="{gap_char}"')

    def _get_seqs(self, match: Match) -> Tuple[Seq_T, Seq_T]:
        """Get the two sequences to compare."""
        return match.utxt.text, match.vtxt.text

    def __call__(self, match: Match) -> Match:
        """Perform the alignment and use it to modify the provided match.

        The updated match uses the values calculated from alignment to adjust
        the start and end points of its sequences, as well as storing the score
        and sequence texts calculated for the alignment."""

        # compute the alignment and keep non-aligned regions
        (lu, cu, _ru), (lv, cv, _rv), score = sw_align(
            *self._get_seqs(match), self.scorer
        )

        # use lengths of non-aligned regions to move the sequence boundaries
        # [...] ["A", "B", "C"] [...]
        # ---->                <----
        u, v = match.utxt.doc, match.vtxt.doc
        us, vs = match.utxt.start + len(lu), match.vtxt.start + len(lv)
        utxt = u[us : us + len(cu)]
        vtxt = v[vs : vs + len(cv)]

        # use the gaps in the alignment to construct a new sequence of token
        # texts, inserting gap_char wherever the aligner created a gap
        u_ptr = 0
        v_ptr = 0
        au = []
        av = []
        for i in range(max(len(utxt), len(vtxt))):
            if cu[i] != "-":
                au.append(utxt[u_ptr].text)
                u_ptr += 1
            else:
                au.append(self.gap_char)
            if cv[i] != "-":
                av.append(vtxt[v_ptr].text)
                v_ptr += 1
            else:
                av.append(self.gap_char)

        # trim back the sequence boundaries further to remove any non-alphanum.
        # tokens from the start and end of both alignment and orig. sequence
        while not au[-1].isalnum() or not av[-1].isalnum():
            utxt, vtxt, au, av = utxt[:-1], vtxt[:-1], au[:-1], av[:-1]
        while not au[0].isalnum() or not av[0].isalnum():
            utxt, vtxt, au, av = utxt[1:], vtxt[1:], au[1:], av[1:]

        # normalize score to length; 1.0 is perfect
        norm_score = float(score) / max(len(au), len(av))

        # create a new match with alignment info and adjusted boundaries
        return Match(match.u, match.v, utxt, vtxt, norm_score, au, av)


class SmithWatermanPhoneticAligner(SmithWatermanAligner):
    """Local alignment using phonetic values provided by a Phonemes instance."""

    def __init__(self, scorer: Scorer_T = None, gap_char: str = "-") -> None:
        # error if phonetic information isn't available
        if not Span.has_extension("phonemes"):
            raise RuntimeError("Phonemes component not available")
        super().__init__(scorer=scorer, gap_char=gap_char)

    def _get_seqs(self, match: Match) -> Tuple[Seq_T, Seq_T]:
        """Get the phonemes of the two sequences for comparison."""
        # combine the phonemes for each token into a single string; if there's
        # no phonetic content, use the token text in place of the phonemes
        return (
            ["".join([p or "" for p in t._.phonemes]) or t.text for t in match.utxt],
            ["".join([p or "" for p in t._.phonemes]) or t.text for t in match.vtxt],
        )
