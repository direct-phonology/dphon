"""Indexes store the contents of files in a corpus in a way that supports
querying by the user."""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable
from collections import defaultdict

from dphon.tokenizer import Token, TokenStream


class Index(ABC):
    """Abstract base class with no defined store() implementation."""

    @abstractmethod
    def add(self, tokens: TokenStream):
        """Store all the Tokens in a TokenStream for later querying."""
        raise NotImplementedError

    @abstractmethod
    def drop(self, fn: Callable):
        """Call the provided callable on each stored Token, removing those that
        return True.
        """
        raise NotImplementedError

    @abstractmethod
    def empty(self):
        """Remove all Tokens from the Index."""
        raise NotImplementedError


class InMemoryIndex(Index):
    """A simple Index type that stores all Tokens in-memory in a Dict."""

    _tokens: Dict[str, List[Token]]

    def __init__(self):
        self._tokens = defaultdict(list)

    def __repr__(self) -> str:
        return self._tokens.__repr__()

    def add(self, tokens: TokenStream):
        for token in tokens:
            self._tokens[token.text].append(token)

    def drop(self, fn: Callable):
        self._tokens = {
            text: tokens for (text, tokens) in self._tokens.items() if fn(tokens)
        }

    def empty(self):
        self._tokens.clear()
