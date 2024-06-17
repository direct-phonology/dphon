#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

import math
from typing import Dict, List, NamedTuple, Tuple

import Levenshtein as Lev
from rich.console import Console, ConsoleOptions, RenderResult
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

    def __key(self) -> tuple:
        return (
            *sorted((self.u, self.v)),
            *sorted((self.utxt.text, self.vtxt.text)),
        )

    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, value: object) -> bool:
        """Matches are equal if they have the same text in the same documents."""
        if isinstance(value, Match):
            return self.__key() == value.__key()
        return NotImplemented

    def __len__(self) -> int:
        """Length of the longer sequence in the match."""
        return max(len(self.utxt), len(self.vtxt))

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Format the match for display in console."""
        table = Table(show_header=False, box=None)
        table.add_column("doc", no_wrap=True)
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
    def u_transcription(self) -> str:
        return "*" + " ".join(self.utxt._.syllables)

    @property
    def v_transcription(self) -> str:
        return "*" + " ".join(self.vtxt._.syllables)

    @property
    def weighted_score(self) -> float:
        """Ratio of phonemic similarity to graphic similarity."""
        try:
            return self.phonetic_similarity / self.graphic_similarity
        except ZeroDivisionError:
            return math.inf

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
            "phonetic_similarity": self.phonetic_similarity,
            "graphic_similarity": self.graphic_similarity,
        }
