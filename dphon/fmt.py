# -*- coding: utf-8 -*-
"""Classes for formatting and display of matches."""

from abc import ABC, abstractmethod
from typing import Tuple, Callable, List

from rich.theme import Theme

from dphon.match import Match

# Default color scheme for the RichFormatter
DEFAULT_THEME = Theme({
    "context": "dim",
    "variant": "blue",
    "insertion": "green",
    "mismatch": "red"
})


class MatchFormatter(ABC):
    """Abstract class; encodes matches into printable strings."""

    @abstractmethod
    def __call__(self, match: Match) -> str:
        """Generate a printable string based on a match and return it."""
        raise NotImplementedError


class SimpleFormatter(MatchFormatter):
    """Basic formatter that displays aligned matches with doc information.

    The characters used to represent gaps in alignment and newlines can be
    customized by specifying gap_char and nl_char respectively."""

    gap_char: str
    nl_char: str
    _transforms: List[Callable[[str], str]]

    def __init__(self, gap_char: str = " ", nl_char: str = "⏎") -> None:
        """Create a formatter with specified gap and newline characters."""
        self.gap_char = gap_char
        self.nl_char = nl_char

    def _format_seqs(self, match: Match) -> Tuple[str, str]:
        """Format the match sequences for display.

        Uses aligned versions if they are present, replacing alignment gaps and
        newlines with gap_char and nl_char."""
        _u, _v, utxt, vtxt, _score, au, av = match
        if au and av:
            return (
                au.replace("-", self.gap_char).replace("\n", self.nl_char),
                av.replace("-", self.gap_char).replace("\n", self.nl_char)
            )
        return (
            utxt.text.replace("-", self.gap_char).replace("\n", self.nl_char),
            vtxt.text.replace("-", self.gap_char).replace("\n", self.nl_char)
        )

    def __call__(self, match: Match) -> str:
        """Display the match sequences with metadata."""
        fu, fv = self._format_seqs(match)
        u, v, utxt, vtxt, *_ = match
        return (f"{fu} ({u} {utxt.start}–{utxt.end-1})\n"
                f"{fv} ({v} {vtxt.start}–{vtxt.end-1})")


class ColorFormatter(SimpleFormatter):
    """Formatter that annotates output so it can be colorized in terminal.

    Uses a DFA approach to parse the sequences and annotate them with markers
    that correspond to a color scheme."""

    # TODO

    pass
