"""SpaCy pipeline components for building indexes of arbitrary Token data."""

import logging
from itertools import dropwhile
from typing import Any, Callable, Iterator, Iterable, List, Tuple, TypeVar

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["index"] = lambda nlp, **cfg: Index(nlp, **cfg)

KT = TypeVar("KT")              # type for keys stored in the index
VT = TypeVar("VT")              # type for values stored in the index
Entry = Tuple[KT, List[VT]]     # type for an index entry (all values at key)


class Index():
    """A spaCy pipeline component that indexes arbitrary items via callables."""

    def __init__(self, nlp: Language, name: str, key_fn: Callable[[KT], VT],
                 val_fn: Callable[[Doc], Iterable[KT]]):
        """Initialize the index component."""
        # store name, callables used to index values, and total values (size)
        self.name = name
        self.key_fn = key_fn
        self.val_fn = val_fn
        self._size = 0

        # initialize the index
        self.table = nlp.vocab.lookups.add_table(self.name)
        logging.info(f"created {self.__class__} as {self.name}")

    def __call__(self, doc: Doc) -> Doc:
        """Extract useful values from the Doc and add them to the index."""
        for val in self.val_fn(doc):
            key = self.key_fn(val)
            # if key_fn returns None, skip indexing this value
            if key is not None:
                try:
                    self.table[key].append(val)
                except KeyError:
                    self.table[key] = [val]
                self._size += 1
        return doc

    def __len__(self) -> int:
        """Get the total number of keys in the index."""
        return len(self.table)

    def __getitem__(self, key: KT) -> List[VT]:
        """Return a list of all values indexed at a given key."""
        return self.table[key]

    def __iter__(self) -> Iterator[Entry]:
        """Return a (k, v) iterator over all entries in the index."""
        return ((key, values) for key, values in self.table.items())

    def filter(self, fn: Callable[[Entry], bool]) -> Iterator[Entry]:
        """Return a (k, v) iterator over all entries which match a predicate."""
        return ((key, values) for key, values in dropwhile(fn, self.table.items()))

    @property
    def size(self) -> int:
        """Get the total number of values in the index."""
        return self._size
