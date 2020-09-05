"""Matches represent a correspondence between two sections of Documents."""

from spacy.tokens import Doc, Span, Token


class Match():
    """Matches are immutable pairs of locations (Spans) in two documents."""

    _left: Span
    _right: Span

    def __init__(self, left: Span, right: Span):
        """Create a new Match with shallow copies of its two locations."""
        self._left = left.doc[left.start:left.end]
        self._right = right.doc[right.start:right.end]

    def __repr__(self) -> str:
        """Return the representation of the match locations as a string."""
        return f"Match([{self._left.start}:{self._left.end}], [{self._right.start}:{self._right.end}])"

    def __str__(self) -> str:
        """Return the text of the match as a string."""
        left_text = self._left.text.replace("\n", "")
        right_text = self._right.text.replace("\n", "")
        return f"{left_text} :: {right_text}"

    def __lt__(self, other: Span) -> bool:
        """Order matches by left location, then right. Group by doc."""
        if id(self._left.doc) < id(other.left.doc):
            return True
        elif id(self._left.doc) == id(other.left.doc):
            if id(self._right.doc) < id(other.right.doc):
                return True
            elif id(self._right.doc) == id(other.right.doc):
                if self._left < other.left:
                    return True
                if self._left == other.left:
                    return self._right < other.right
                return False
            return False
        return False

    @property
    def left(self) -> Span:
        """Return one of the locations the match points to."""
        return self._left

    @property
    def right(self) -> Span:
        """Return the other location the match points to."""
        return self._right