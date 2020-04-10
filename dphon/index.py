"""Indexes store the contents of files in a corpus in a way that supports
querying by the user."""

from abc import ABC, abstractmethod
from typing import List, Dict
from collections import defaultdict

from dphon.tokenizer import Token, TokenStream


class Index(ABC):
    """Abstract base class with no defined store() implementation."""

    @abstractmethod
    def store(self, tokens: TokenStream):
        """Store all the Tokens in a TokenStream for later querying."""
        raise NotImplementedError


class InMemoryIndex(Index):
    """A simple Index type that stores all Tokens in-memory in a Dict."""

    _tokens: Dict[str, List[Token]]

    def __init__(self):
        self._tokens = defaultdict(list)

    def store(self, tokens: TokenStream):
        for token in tokens:
            self._tokens[token.text].append(token)

    def __repr__(self) -> str:
        return self._tokens.__repr__()
