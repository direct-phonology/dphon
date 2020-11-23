"""The Match class and associated functionality."""

from typing import Optional, Tuple, Any
from dataclasses import dataclass

from spacy.tokens import Span


@dataclass(order=True)
class Match():
    """Matches are similar pairs of textual sequences."""

    left: Span
    right: Span
    score: Optional[float] = None
    alignment: Optional[Tuple[str, str]] = None

    def __init__(self, left: Span, right: Span, score: Optional[float] = None,
                 alignment: Optional[Tuple[str, str]] = None) -> None:
        """Make a shallow copy of the two sequences in the match."""
        self.left = left.doc[left.start:left.end]
        self.right = right.doc[right.start:right.end]
        self.score = score
        self.alignment = alignment

    def __len__(self) -> int:
        """Return the length of the longer sequence in the match."""
        return max(len(self.left), len(self.right))
