# -*- coding: utf-8 -*-
"""Classes for formatting and display of matches."""

from abc import ABC, abstractmethod
from typing import Tuple

from rich.theme import Theme
from spacy.tokens import Doc

from dphon.match import Match, NotAlignedError

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

    def __init__(self, gap_char: str = " ", nl_char: str = "⏎") -> None:
        """Create a formatter with specified gap and newline characters."""
        self.gap_char = gap_char
        self.nl_char = nl_char

    def format_seqs(self, left: str, right: str) -> Tuple[str, str]:
        """Replace gap and newline characters in sequences."""
        # alignment result uses "-" to indicate gaps
        return (
            left.replace("-", self.gap_char).replace("\n", self.nl_char),
            right.replace("-", self.gap_char).replace("\n", self.nl_char)
        )

    def __call__(self, match: Match) -> str:
        """Display the match sequences with document information.

        - Uses the aligned versions of match texts, if available.
        - Uses the document title if available, otherwise unique id.
        """

        # check for alignment, if none use unaligned version
        try:
            left, right = match.alignment
        except NotAlignedError:
            left, right = match.left.text, match.right.text
        # format the two sequences
        fmt_left, fmt_right = self.format_seqs(left, right)
        # add doc titles if present, otherwise use IDs
        if Doc.has_extension("title"):
            top = f"{fmt_left} ({match.left.doc._.title})"
            bottom = f"{fmt_right} ({match.right.doc._.title})"
        else:
            top = f"{fmt_left} ({id(match.left.doc)})"
            bottom = f"{fmt_right} ({id(match.right.doc)})"
        # join with a newline
        return f"{top}\n{bottom}"


class ColorFormatter(SimpleFormatter):
    """Formatter that annotates output so it can be colorized in terminal.

    Uses a DFA approach to parse the sequences and annotate them with markers
    that correspond to a color scheme."""

    # TODO

    pass
