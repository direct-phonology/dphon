"""Matches represent a correspondence between two sections of Documents."""

from spacy.tokens import Doc, Span, Token


class Match():
    """Matches are immutable pairs of matching Spans in two documents."""

    _left: Span
    _right: Span

    def __init__(self, left: Span, right: Span):
        """Create a new Match with shallow copies of its two locations."""
        self._left = left.doc[left.start:left.end]
        self._right = right.doc[right.start:right.end]

    def __repr__(self) -> str:
        """Return the numeric locations of the Spans in the match."""
        return f"{id(self.left.doc)}[{self.left.start}:{self.left.end}] :: {id(self.right.doc)}[{self.right.start}:{self.right.end}]"

    def __str__(self) -> str:
        """Return the text of both Spans in the match."""
        return f"{self.left} :: {self.right}"

    @property
    def left(self) -> Span:
        """Return one of the Spans the match points to."""
        return self._left

    @property
    def right(self) -> Span:
        """Return the other Span the match points to."""
        return self._right
