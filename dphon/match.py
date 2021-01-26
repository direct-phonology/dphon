from spacy.tokens import Span
from typing import NamedTuple, Optional


class Match(NamedTuple):
    """A match is a pair of similar textual sequences in two documents."""
    u: str
    v: str
    utxt: Span
    vtxt: Span
    weight: float = 0
    au: Optional[str] = None
    av: Optional[str] = None

    def __len__(self) -> int:
        """Return the length of the longer sequence in the match."""
        return max(len(self.utxt), len(self.vtxt))
