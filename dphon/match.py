"""The Match class and associated functionality."""

from typing import List, Optional, Tuple

from spacy.tokens import Span


class NotAlignedError(RuntimeError):
    """Attempted to access a match alignment when none exists."""
    pass


class Match():
    """Matches are immutable pairs of sequences in two documents."""

    _left: Span
    _right: Span
    _score: Optional[float]
    _alignment: Optional[Tuple[str, str]] = None

    def __init__(self, left: Span, right: Span, alignment: Tuple[List[str], List[str]] = None, score: float = None):
        """Create a new Match with shallow copies of its two sequences."""
        self._left = left.doc[left.start:left.end]
        self._right = right.doc[right.start:right.end]
        self._score = score
        # if an alignment was provided, store it as strings
        if alignment:
            self._alignment = ("".join(alignment[0]), "".join(alignment[1]))

    def __repr__(self) -> str:
        """Return the match sequence locations as a single string."""
        return f"Match([{self._left.start}:{self._left.end}], [{self._right.start}:{self._right.end}])"

    def __str__(self) -> str:
        """Return the texts of the match sequences as a single string."""
        return f"{self._left.text} :: {self._right.text}"

    def __lt__(self, other: object) -> bool:
        """Order matches by left location, then right."""
        if not isinstance(other, Match):
            return False
        if self._left < other.left:
            return True
        if self._left == other.left:
            return self._right < other.right
        return False

    def __eq__(self, other: object) -> bool:
        """Two matches are equal if their sequences are identical."""
        if not isinstance(other, Match):
            return False
        if self._left != other.left or self._right != other.right:
            return False
        return True

    def __len__(self) -> int:
        """Return the length of the longer sequence in the match."""
        return max(len(self.left), len(self.right))

    @property
    def left(self) -> Span:
        """Return one of the locations the match points to."""
        return self._left

    @property
    def right(self) -> Span:
        """Return the other location the match points to."""
        return self._right

    @property
    def alignment(self) -> Tuple[str, str]:
        """Return the two sequences of the match with characters aligned.

        Raise an error if this function is called when the match has not yet
        been aligned."""
        if not self._alignment:
            raise NotAlignedError()
        return self._alignment

    @property
    def score(self) -> Optional[float]:
        """Return the similarity score of the match sequences."""
        return self._score

    @property
    def is_norm_eq(self) -> bool:
        """True if a match's sequences are equal after normalization.

        This comparison ignores whitespace, case, and punctuation, returning
        True if all alphanumeric characters of the left location match all
        alphanumeric characters of the right location and False otherwise."""

        left_norm = "".join([c.lower()
                             for c in self._left.text if c.isalnum()])
        right_norm = "".join([c.lower()
                              for c in self._right.text if c.isalnum()])
        return left_norm == right_norm
