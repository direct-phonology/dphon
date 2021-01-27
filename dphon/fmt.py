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
        self.gap_char = gap_char
        self.nl_char = nl_char

    def _format_seqs(self, match: Match) -> Tuple[str, str]:
        """Format the match sequences for display.

        Uses aligned versions if they are present, replacing alignment gaps and
        newlines with gap_char and nl_char."""

        if match.au and match.av:
            au, av = map("".join, (match.au, match.av))
            au, av = map(lambda s: s.replace("-", self.gap_char), (au, av))
        else:
            au, av = (match.utxt.text, match.vtxt.text)
        au, av = map(lambda s: s.replace("\n", self.nl_char), (au, av))
        return au, av

    def __call__(self, match: Match) -> str:
        """Display the match sequences with metadata."""
        fu, fv = self._format_seqs(match)
        u, v, utxt, vtxt, *_ = match
        return (f"{fu} ({u} {utxt.start}–{utxt.end-1})\n"
                f"{fv} ({v} {vtxt.start}–{vtxt.end-1})")


class RichFormatter(SimpleFormatter):
    """Formatter that annotates output so it can be colorized in terminal."""

    theme: Theme = DEFAULT_THEME
    context_len: int = 4

    def _format_seqs(self, match: Match) -> Tuple[str, str]:
        """Format the match sequences for display.
        
        Uses aligned versions if they are present, replacing alignment gaps and
        newlines with gap_char and nl_char.
        
        Colorizes output using the stored theme, and adds context to either side
        of the match sequences."""

        # convert to lists of strings; replace alignment gaps
        if match.au and match.av:
            au = [t if t != "-" else self.gap_char for t in match.au]
            av = [t if t != "-" else self.gap_char for t in match.av]
        else:
            au = [t.text for t in match.utxt]
            av = [t.text for t in match.vtxt]
        
        # replace newlines
        au = [t if t != "\n" else self.nl_char for t in au]
        av = [t if t != "\n" else self.nl_char for t in av]

        return au, av