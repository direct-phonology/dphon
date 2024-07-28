#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

import math
from typing import Dict, List, NamedTuple

import Levenshtein as Lev
from rich.console import Console, ConsoleOptions, RenderResult
from rich.padding import Padding
from rich.table import Table
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
        table = Table(show_header=False, box=None)
        table.add_column("doc")
        table.add_column("bounds")
        table.add_column("text")
        table.add_column("transcription")

        # get colorized match text and transcription
        su, sv = console.highlighter.format_match(self)
        pu, pv = console.highlighter.transcribe_match(self)

        # add rows for each document
        table.add_row(self.u, f"{self.utxt.start}-{self.utxt.end-1}", su, pu)
        table.add_row(self.v, f"{self.vtxt.start}-{self.vtxt.end-1}", sv, pv)

        return [table]

    @property
    def graphic_similarity(self) -> float:
        """Levenshtein ratio of the aligned sequences."""
        return Lev.seqratio(self.au, self.av)

    @property
    def phonetic_similarity(self) -> float:
        """Similarity score of the phonetic content of the sequences."""
        return self.weight

    @property
    def weighted_score(self) -> float:
        """Ratio of phonemic similarity to graphic similarity."""
        try:
            return self.phonetic_similarity / self.graphic_similarity
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
            "phonetic_similarity": self.phonetic_similarity,
            "graphic_similarity": self.graphic_similarity,
        }
