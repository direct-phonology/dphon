#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SpaCy pipeline components for building indices of arbitrary document data."""

import logging
from abc import ABC, abstractmethod
from typing import Callable, Hashable, Iterable, Iterator, List, Tuple, TypeVar, Generic

from spacy.language import Language
from spacy.tokens import Doc, Span
from spacy.lookups import Table

K = TypeVar("K")                    # type for keys stored in the index
V = TypeVar("V")                    # type for values stored in the index


class Index(ABC, Generic[K, V]):
    """A spaCy pipeline component that indexes arbitrary items via callables."""

    def __init__(self, nlp: Language):
        """Initialize the index component."""
        logging.info(f"using {self.__class__}")

    @abstractmethod
    def __call__(self, doc: Doc) -> Doc:
        """Index a single spaCy Doc. Should not mutate the Doc."""
        return doc

    @abstractmethod
    def __contains__(self, key: K) -> bool:
        """Check if a key is in the index."""
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, key: K) -> Iterable[V]:
        """Return all values indexed at a given key."""
        raise NotImplementedError

    @abstractmethod
    def __iter__(self) -> Iterator[Tuple[K, List[V]]]:
        """Return a (k, v) iterator over all entries in the index."""
        raise NotImplementedError

    @abstractmethod
    def filter(self, fn: Callable[[Tuple[K, List[V]]], bool]) -> Iterator[Tuple[K, List[V]]]:
        """Return a (k, v) iterator over all entries which match a predicate."""
        raise NotImplementedError

    @abstractmethod
    def __len__(self) -> int:
        """Get the total number of keys in the index."""
        raise NotImplementedError

    @property
    @abstractmethod
    def size(self) -> int:
        """Get the total number of values in the index."""
        raise NotImplementedError


class LookupsIndex(Index[Hashable, V], Generic[V]):

    _table: Table       # uses spaCy's lookup tables (bloom filtered dict)
    _size: int          # tracker for total number of values in index

    def __init__(self, nlp: Language) -> None:
        self._table = nlp.vocab.lookups.add_table("index")
        self._size = 0
        super().__init__(nlp)

    def __call__(self, doc: Doc) -> Doc:
        """Extract values from a doc with _get_vals and index with _get_key."""
        for val in self._get_vals(doc):
            key = self._get_key(val)
            try:
                self._table.get(key).append(val)
            except AttributeError:
                self._table.set(key, [val])
            self._size += 1
        return super().__call__(doc)

    def __len__(self) -> int:
        """Get the total number of keys in the index."""
        return len(self._table)

    def __contains__(self, key: K) -> bool:
        """Check if a key is in the index."""
        return key in self._table

    def __getitem__(self, key: K) -> List[V]:
        """Return a list of all values indexed at a given key."""
        return self._table.get(key)

    def __iter__(self) -> Iterator[Tuple[K, List[V]]]:
        """Return a (k, v) iterator over all entries in the index."""
        return (entry for entry in self._table.items())

    @abstractmethod
    def _get_vals(self, doc: Doc) -> Iterable[V]:
        """Get all the values to be indexed from a Doc."""
        raise NotImplementedError

    @abstractmethod
    def _get_key(self, val: V) -> Hashable:
        """Get the key to index a particular value."""
        raise NotImplementedError

    def filter(self, fn: Callable[[Tuple[K, List[V]]], bool]) -> Iterator[Tuple[K, List[V]]]:
        """Return a (k, v) iterator over all entries which match a predicate."""
        return (entry for entry in iter(self) if fn(entry))

    @property
    def size(self) -> int:
        """Get the total number of values in the index."""
        return self._size


class NgramPhonemesLookupsIndex(LookupsIndex[Span]):

    def _get_vals(self, doc: Doc) -> Iterator[Span]:
        """Iterator over alphabetic ngrams in the doc."""
        return (ngram for ngram in doc._.ngrams if ngram.text.isalpha)

    def _get_key(self, val: Span) -> str:
        """All phonetic content of an ngram as a string."""
        return "".join(val._.phonemes)


@Language.factory("ngram_phonemes_index")
def create_ngram_phonemes_lookup_index(nlp: Language, name: str) -> NgramPhonemesLookupsIndex:
    return NgramPhonemesLookupsIndex(nlp)
