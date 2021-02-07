#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

from typing import List, NamedTuple, Tuple
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

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Format the match for display in console."""
        su, sv = console.highlighter.format_match(self)     # type: ignore
        yield (f"score {int(self.weight)}, weighted {self.weighted_score}\n"
               f"{su} ({self.u} {self.utxt.start}–{self.utxt.end-1})\n"
               f"{sv} ({self.v} {self.vtxt.start}–{self.vtxt.end-1})\n")

    @property
    def weighted_score(self) -> float:
        """Match score divided by its length."""
        return round(self.weight / float(len(self)), 2)
