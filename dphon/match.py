"""The Match class and associated functionality."""

from spacy.tokens import Doc, Span, Token


class Match():
    """Matches are immutable pairs of locations in two documents."""

    _left: Span
    _right: Span
    _norm_eq: bool
    _graphic_var: bool

    def __init__(self, left: Span, right: Span):
        """Create a new Match with shallow copies of its two locations."""
        self._left = left.doc[left.start:left.end]
        self._right = right.doc[right.start:right.end]
        self._norm_eq = is_norm_eq(self)

    def __repr__(self) -> str:
        """Return the match locations as a string."""
        return f"Match({self._left.doc._.title}[{self._left.start}:{self._left.end}], {self._right.doc._.title}[{self._right.start}:{self._right.end}])"

    def __str__(self) -> str:
        """Return the text of the match as a string."""
        return f"{self._left.text} ({self._left.doc._.title})\n{self._right.text} ({self._right.doc._.title})"

    def __lt__(self, other: object) -> bool:
        """Order matches by left location, then right. Group by doc title."""
        if not isinstance(other, Match):
            return False
        if self._left.doc._.title < other.left.doc._.title:
            return True
        if self._left.doc._.title == other.left.doc._.title:
            if self._right.doc._.title < other.right.doc._.title:
                return True
            if self._right.doc._.title == other.right.doc._.title:
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

    @property
    def is_norm_eq(self) -> bool:
        """See `dphon.match.is_norm_eq`."""
        return self._norm_eq


def is_norm_eq(match: Match) -> bool:
    """True if a match's texts are equal after normalization.

    This comparison ignores whitespace, case, and punctuation, returning
    True if all alphanumeric characters of the left location match all
    alphanumeric characters of the right location and False otherwise."""

    left_norm = "".join([c.lower() for c in match._left.text if c.isalnum()])
    right_norm = "".join([c.lower() for c in match._right.text if c.isalnum()])
    return left_norm == right_norm
