"""Filters take a TokenStream as input and return one as output, processing
Tokens as they are passed through."""

import re
import json
import pkg_resources
from abc import ABC, abstractmethod

from dphon.tokenizer import Token, TokenStream


class Filter(ABC):
    """Abstract base class with no defined process() implementation."""

    @abstractmethod
    def process(self, tokens: TokenStream) -> TokenStream:
        """Filter subclasses should implement process() as a method that both
        accepts and returns a TokenStream."""
        raise NotImplementedError


class WhitespaceFilter(Filter):
    """A simple filter that removes tokens consisting entirely of whitespace."""

    WS_RE = re.compile(r"^\s+$")

    def process(self, tokens: TokenStream) -> TokenStream:
        """Discard any token consisting entirely of whitespace, via regex."""
        return (token for token in tokens if not self.WS_RE.match(token.text))


class PhoneticFilter(Filter):
    """A filter that replaces characters in tokens with placeholders that
    correspond to their phonetic value. This allows querying for matches based
    on phonetic content of texts."""

    phon_dict: dict

    def __init__(self, dict_name: str):
        """Create a new PhoneticFilter. Accepts the name of a JSON file that
        maps characters or strings to other characters."""
        
        path = pkg_resources.resource_filename(__package__, dict_name)
        with open(path, encoding="utf-8") as dict_file:
            self.phon_dict = json.loads(dict_file.read())

    def process(self, tokens: TokenStream) -> TokenStream:
        """Convert each Token's text to a phonetic representation."""

        return (self.to_phonemes(token) for token in tokens)

    def to_phonemes(self, token: Token) -> Token:
        """Replace each character in a Token's text with its entry from the
        filter's phonetic dictionary."""

        token.meta["orig_text"] = token.text
        phonemes = [self.phon_dict.get(char, char) for char in token.text]

        token.text = "".join(phonemes)
        return token
