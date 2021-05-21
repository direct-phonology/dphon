#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

import math
from typing import Dict, List, NamedTuple

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
        pu, pv = console.highlighter.transcription(self)  # type: ignore

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
    def weighted_score(self) -> float:
        """Ratio of phonemic similarity to graphic similarity."""
        try:
            return self.weight / Lev.seqratio(self.au, self.av)
        except ZeroDivisionError:
            return math.inf

    def as_dict(self) -> Dict[str, str]:
        """Match with prettier field names for serialization."""
        return {
            "u_id": self.u,
            "v_id": self.v,
            "u_text": self.utxt.text,
            "v_text": self.vtxt.text,
            "u_text_aligned": "".join(self.au),
            "v_text_aligned": "".join(self.av),
            "u_start": self.utxt.start,
            "u_end": self.utxt.end,
            "v_start": self.vtxt.start,
            "v_end": self.vtxt.end,
            "score": str(self.weight),
            "weighted_score": str(self.weighted_score),
        }
