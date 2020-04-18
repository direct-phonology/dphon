"""Tokenizers are responsible for breaking up a document into a sequence of
Tokens that can be used for analysis."""

from abc import ABC, abstractmethod
from typing import Sequence, Dict, Any, NewType
from collections import defaultdict

from dphon.document import Document


class Token():
    """A Token is a single unit of text in a Document, which stores positional
    data and a reference to its parent Document along with other metadata added
    by Tokenizers or Filters."""

    _id: int
    start: int
    stop: int
    text: str
    doc: Document
    meta: Dict[str, Any]

    def __init__(self, _id: int, doc: Document, text: str):
        self._id = _id
        self.doc = doc
        self.text = text
        self.meta = defaultdict()

    def __repr__(self) -> str:
        return f"<Token id: {self.doc.id}-{self._id}>"

    def __str__(self) -> str:
        return self.text

    @property
    def id(self) -> int:
        return self._id


TokenStream = NewType('TokenStream', Sequence[Token])


class Tokenizer(ABC):
    """A Tokenizer must implement tokenize() to transform a Document into a
    TokenStream."""

    @abstractmethod
    def tokenize(self, doc: Document) -> TokenStream:
        """Tokenizers must implement this method to return a TokenStream."""
        raise NotImplementedError


class NgramTokenizer(Tokenizer):
    """A Tokenizer that splits ("shingles") Documents into overlapping n-gram
    Tokens of a provided size (n)."""

    _n: int
    _id: int

    def __init__(self, n: int):
        self._n = n

    def tokenize(self, doc: Document) -> TokenStream:
        self._id = 0

        for i in range(len(doc.text) - self._n):
            seed = doc.text[i:i + self._n]
            yield Token(doc=doc, _id=self._id, text=seed)
            self._id += 1
