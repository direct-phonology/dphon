"""Matches represent a correspondence between two sections of Documents."""

from spacy.tokens import Doc, Span, Token


class Match():
    """Matches are immutable pairs of locations in two documents."""

    _left: Span
    _right: Span

    def __init__(self, left: Span, right: Span):
        """Create a new Match with shallow copies of its two locations."""
        self._left = left.doc[left.start:left.end]
        self._right = right.doc[right.start:right.end]

    def __repr__(self) -> str:
        """Return the match locations as a string."""
        return f"Match({id(self._left.doc)}[{self._left.start}:{self._left.end}], {id(self._right.doc)}[{self._right.start}:{self._right.end}])"

    def __str__(self) -> str:
        """Return the text of the match as a string."""
        if Doc.has_extension("title"):
            return f"{self._left.text} ({self._left.doc._.title}) :: {self._right.text} ({self._right.doc._.title})"
        return f"{self._left.text} :: {self._right.text}"

    def __lt__(self, other: object) -> bool:
        """Order matches by left location, then right. Group by doc."""
        if not isinstance(other, Match):
            return False
        if id(self._left.doc) < id(other.left.doc):
            return True
        if id(self._left.doc) == id(other.left.doc):
            if id(self._right.doc) < id(other.right.doc):
                return True
            if id(self._right.doc) == id(other.right.doc):
                if self._left < other.left:
                    return True
                if self._left == other.left:
                    return self._right < other.right
                return False
            return False
        return False

    def __eq__(self, other: object) -> bool:
        """Two matches are equal if their docs and locations are identical."""
        if not isinstance(other, Match):
            return False
        if self._left != other.left or self._right != other.right:
            return False
        return True

    def __len__(self) -> int:
        """Return the length of shorter of the two locations in the match."""
        return min(len(self.left), len(self.right))

    @property
    def left(self) -> Span:
        """Return one of the locations the match points to."""
        return self._left

    @property
    def right(self) -> Span:
        """Return the other location the match points to."""
        return self._right
