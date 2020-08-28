"""SpaCy pipeline components for building indexes of arbitrary Token data."""

import logging
from itertools import dropwhile
from typing import Any, Callable, Iterator, List, Tuple, Generic, TypeVar

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["index"] = lambda nlp, **cfg: Index(nlp, **cfg)

class Index():
    """A spaCy pipeline component that indexes Tokens via a callable."""

    name: str  # component name, will show up in the pipeline as "[name]_index"

    def __init__(self, nlp: Language, name: str, fn: Callable[[Token], Any]):
        """Initialize the index component."""
        logging.info(f"initializing index pipeline component")

        # store name, callable used to index tokens, and total token count
        self.fn = fn
        self.name = f"{name}_index"
        self._token_count = 0

        # initialize the index
        self.table = nlp.vocab.lookups.add_table(self.name)
        logging.info(f"index added to vocab as lookups.{self.name}")

    def __call__(self, doc: Doc) -> Doc:
        """Index each Token in a Doc at a key returned by calling a function."""
        for token in doc:
            key = self.fn(token)
            if key is not None:
                if key not in self.table:
                    self.table[key] = []
                self.table[key].append(token)
                self._token_count += 1
        return doc

    def __len__(self) -> int:
        """Get the total number of entries in the index."""
        return len(self.table)

    def __getitem__(self, key: Any) -> List[Token]:
        """Return a list of all Tokens indexed at a given key."""
        return self.table[key]

    def __iter__(self) -> Iterator[Tuple[Any, List[Token]]]:
        """Return a (k, v) iterator over all entries in the index."""
        return ((key, tokens) for key, tokens in self.table.items())

    def filter(self, fn: Callable[[Tuple[Any, List[Token]]], bool]) -> Iterator[Tuple[Any, List[Token]]]:
        """Return a (k, v) iterator over all entries which match a predicate."""
        return ((key, tokens) for key, tokens in dropwhile(fn, self.table.items()))

    @property
    def token_count(self) -> int:
        """Get the total number of tokens in the index."""
        return self._token_count


class NgramIndex(Index):
    """A spaCy pipeline component that indexes Token n-grams via a callable."""

    def __init__(self, nlp: Language, name: str, fn: Callable[[Span], Any]):
        """Initialize the n-gram index component."""
        logging.info(f"initializing n-gram index pipeline component")

        # store name, callable used to index tokens, and total token count
        self.fn = fn
        self.name = f"{name}_ngram_index"
        self._token_count = 0

        # initialize the index
        self.table = nlp.vocab.lookups.add_table(self.name)
        logging.info(f"index added to vocab as lookups.{self.name}")

    def __call__(self, doc: Doc) -> Doc:
        """Index each n-gram in a Doc at a key returned by calling a function."""
        for ngram in doc:
            key = self.fn(ngram)
            if key is not None:
                if key not in self.table:
                    self.table[key] = []
                self.table[key].append(ngram)
                self._token_count += 1
        return doc
