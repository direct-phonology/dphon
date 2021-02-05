#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

from typing import List, NamedTuple, Optional

from rich.console import Console, ConsoleOptions, RenderResult
from spacy.tokens import Span


class Match(NamedTuple):
    """A match is a pair of similar textual sequences in two documents."""
    u: str
    v: str
    utxt: Span
    vtxt: Span
    weight: float = 0
    au: Optional[List[str]] = None
    av: Optional[List[str]] = None

    def __len__(self) -> int:
        """Length of the longer sequence in the match."""
        return max(len(self.utxt), len(self.vtxt))

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Colorize and format the match for display in console."""
        # use aligned versions if available, else sequence texts
        if self.au and self.av:
            fu, fv = "".join(self.au), "".join(self.av)
        else:
            fu, fv = self.utxt.text, self.vtxt.text

        # print with scores and sequence indices
        yield f"score {int(self.weight)}, weighted {self.weighted_score}"
        yield f"{fu} ({self.u} {self.utxt.start}–{self.utxt.end-1})"
        yield f"{fv} ({self.v} {self.vtxt.start}–{self.vtxt.end-1})"

    @property
    def weighted_score(self) -> float:
        """Match score divided by its length."""
        return round(self.weight / float(len(self)), 2)
