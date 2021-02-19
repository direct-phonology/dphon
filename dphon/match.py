#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

from typing import List, NamedTuple, Dict

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
        yield (f"[bold]score[/bold] {int(self.weight)}, "
               f"[bold]weighted[/bold] {self.weighted_score}\t"
               f"[white]{self.u}[/white]({self.utxt.start}–{self.utxt.end-1}):"
               f"[white]{self.v}[/white]({self.vtxt.start}–{self.vtxt.end-1})\n"
               f"{su}\n{sv}\n")

    @property
    def weighted_score(self) -> float:
        """Match score divided by its length."""
        return round(self.weight / float(len(self)), 2)

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
