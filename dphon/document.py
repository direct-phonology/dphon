"""A document is the basic unit of text comparison."""

from typing import Dict, Any
from collections import defaultdict

class Document:
    """Basic documents store their text prior to indexing."""

    _id: int
    text: str
    title: str
    series: str
    meta: Dict[str, Any]

    def __init__(self, _id: int, text: str):
        self._id = _id
        self.text = text
        self.meta = defaultdict()

    def __repr__(self) -> str:
        return f"<Document id: {self._id}>"

    def __str__(self) -> str:
        return self.text

    def __len__(self) -> int:
        return len(self.text)

    @property
    def id(self) -> int:
        return self._id
