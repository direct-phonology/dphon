#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

import math
from typing import Dict, List, NamedTuple, Tuple

import Levenshtein as Lev
from rich.padding import Padding
from rich.console import Console, ConsoleOptions, RenderResult
from spacy.tokens import Span


class Match(NamedTuple):
    """A match is a pair of similar textual sequences in two documents."""

    u: str
    v: str
    utxt: Span
    vtxt: Span
    weight: float = 0
    au: List[str] = []
    av: List[str] = []

    def __len__(self) -> int:
        """Length of the longer sequence in the match."""
        return max(len(self.utxt), len(self.vtxt))

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Format the match for display in console."""
        # get colorized match text and transcription
        su, sv = console.highlighter.format_match(self)  # type: ignore
        pu, pv = self.transcription

        # add left-padding to align with match numbers, and bottom-padding
        # so that there's a space between matches in output
        su, sv, pu = map(lambda t: Padding(t, (0, 0, 0, 4)), (su, sv, pu))
        pv = Padding(pv, (0, 0, 1, 4))

        # return everything as an iterable of renderables
        return (
            f"1.  [white]{self.u}[/white] ({self.utxt.start}–{self.utxt.end-1})：",
            su,
            pu,
            f"2.  [white]{self.v}[/white] ({self.vtxt.start}–{self.vtxt.end-1})：",
            sv,
            pv,
        )

    @property
    def u_transcription(self) -> str:
        return "*" + " ".join(self.utxt._.syllables)

    @property
    def v_transcription(self) -> str:
        return "*" + " ".join(self.vtxt._.syllables)

    @property
    def weighted_score(self) -> float:
        """Ratio of phonemic similarity to graphic similarity."""
        try:
            return self.phonetic_similarity() / self.graphic_similarity()
        except ZeroDivisionError:
            return math.inf

    @property
    def transcription(self) -> Tuple[str, str]:
        """Return the phonemic transcription of the match."""
        return (self.u_transcription, self.v_transcription)

    def graphic_similarity(self) -> float:
        """Levenshtein ratio of the aligned sequences."""
        return Lev.seqratio(self.au, self.av)

    def phonetic_similarity(self) -> float:
        """Similarity score of the phonetic content of the sequences."""
        return self.weight

    def context(self, chars: int) -> Tuple[str, str, str, str]:
        """Return up to `chars` characters of context around the match.

        Return value is a tuple of four strings:
        - left context of u
        - right context of u
        - left context of v
        - right context of v
        """
        u, v = self.utxt.doc, self.vtxt.doc
        u_start, u_end = self.utxt.start, self.utxt.end
        v_start, v_end = self.vtxt.start, self.vtxt.end
        u_context_left = u[max(u_start - chars, 0) : u_start]
        v_context_left = v[max(v_start - chars, 0) : v_start]
        u_context_right = u[u_end : min(u_end + chars, len(u))]
        v_context_right = v[v_end : min(v_end + chars, len(v))]
        return (u_context_left, u_context_right, v_context_left, v_context_right)

    def as_dict(self) -> Dict[str, str]:
        """Dict form for structured output formats."""
        return {
            "u_id": self.u,
            "v_id": self.v,
            "u_text": self.utxt.text,
            "v_text": self.vtxt.text,
            "u_text_aligned": "".join(self.au),
            "v_text_aligned": "".join(self.av),
            "u_transcription": self.u_transcription,
            "v_transcription": self.v_transcription,
            "u_start": self.utxt.start,
            "u_end": self.utxt.end,
            "v_start": self.vtxt.start,
            "v_end": self.vtxt.end,
            "phonetic_similarity": self.phonetic_similarity(),
            "graphic_similarity": self.graphic_similarity(),
        }
