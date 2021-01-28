#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SpaCy pipeline components for building indices of arbitrary Token data."""

import logging
from itertools import filterfalse
from typing import Any, Callable, Iterator, Iterable, List, Tuple, TypeVar, Optional

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["index"] = lambda nlp, **cfg: Index(nlp, **cfg)

KT = TypeVar("KT")              # type for keys stored in the index
VT = TypeVar("VT")              # type for values stored in the index
Entry = Tuple[KT, List[VT]]     # type for an index entry (all values at key)

# called on a Doc; returns the list of values from the doc we want to index
ValFn = Callable[[Doc], Iterable[VT]]

# called on a value; if False the value will not be indexed
FilterFn = Callable[[VT], bool]

# called on a value to index; returns the key to index at (i.e. hash)
KeyFn = Callable[[VT], KT]


class Index():
    """A spaCy pipeline component that indexes arbitrary items via callables."""

    name = "index"  # will appear in spaCy pipeline

    def __init__(self, nlp: Language, key_fn: Optional[KeyFn] = None,
                 val_fn: Optional[ValFn] = None, filter_fn: Optional[FilterFn] = None,
                 name: str = None):
        """Initialize the index component.

        - By default, an index will store lists of Tokens keyed on their text.
        - Pass val_fn to control what values are extracted from a Doc.
        - Pass key_fn to control what key values are indexed at.
        - Pass filter_fn to control which values are indexed."""
        # store name, callables used to index values, and total values (size)
        self.name = name if name else self.name
        self._size = 0

        # by default, extracts tokens from docs and indexes them via their text
        self.val_fn: ValFn = val_fn if val_fn else lambda doc: doc
        self.key_fn: KeyFn = key_fn if key_fn else lambda token: token.text
        self.filter_fn: FilterFn = filter_fn if filter_fn else lambda token: True

        # initialize the index
        self.table = nlp.vocab.lookups.add_table(self.name)
        logging.info(f"created component \"{self.name}\"")

    def __call__(self, doc: Doc) -> Doc:
        """Extract values from a doc and index those that pass the filter.

        - Values are extracted from the doc using val_fn(doc).
        - Values that pass the predicate filter_fn(value) are indexed.
        - Values will be indexed using the output of key_fn(value).
        - The Doc is returned unmodified."""

        for val in self.val_fn(doc):
            if self.filter_fn(val):
                key = self.key_fn(val)
                try:
                    self.table.get(key).append(val)
                except AttributeError:
                    self.table.set(key, [val])
                self._size += 1
        return doc

    def __len__(self) -> int:
        """Get the total number of keys in the index."""
        return len(self.table)

    def __contains__(self, key: KT) -> bool:
        """Check if a key is in the index."""
        return key in self.table

    def __getitem__(self, key: KT) -> List[VT]:
        """Return a list of all values indexed at a given key."""
        return self.table.get(key)

    def __iter__(self) -> Iterator[Entry]:
        """Return a (k, v) iterator over all entries in the index."""
        return self.filter(lambda entry: True)

    def filter(self, fn: Callable[[Entry], bool]) -> Iterator[Entry]:
        """Return a (k, v) iterator over all entries which match a predicate."""
        return (entry for entry in self.table.items() if fn(entry))

    @property
    def size(self) -> int:
        """Get the total number of values in the index."""
        return self._size
