"""Tests for the indexing module."""

import io
import logging
from unittest import TestCase
from typing import Iterator

import spacy
from spacy.tokens import Doc, Token
from dphon.console import err_console
from dphon.index import LookupsIndex, NgramPhonemesLookupsIndex

# disconnect logging and capture stderr output for testing
logging.disable(logging.CRITICAL)
err_console.file = io.StringIO()


class TokenTextLookupsIndex(LookupsIndex[Token]):
    """A LookupsIndex subclass for testing; indexes token texts."""

    def _get_vals(self, doc: Doc) -> Iterator[Token]:
        return (token for token in doc)

    def _get_key(self, val: Token) -> str:
        return val.text


class TestLookupsIndex(TestCase):
    """Test the generic LookupsIndex via a subclass."""

    def setUp(self) -> None:
        """Create a blank spaCy pipeline, index, and doc for testing."""
        self.nlp = spacy.blank("en")
        self.idx = TokenTextLookupsIndex(self.nlp)
        self.doc = self.nlp("To be or not to be")
        self.idx(self.doc)

    def test_init(self) -> None:
        """should create lookups table"""
        self.assertTrue(self.nlp.vocab.lookups.has_table("index"))

    def test_len(self) -> None:
        """should store total number of keys in index"""
        # 5 unique token texts; "be" occurs twice
        self.assertEqual(len(self.idx), 5)

    def test_size(self) -> None:
        """should store total number of values in index"""
        # 6 total tokens stored in index
        self.assertEqual(self.idx.size, 6)

    def test_getitem(self) -> None:
        """should retrieve all values at a key"""
        # should index both locations of "be" at same key
        self.assertEqual(self.idx["be"], [self.doc[1], self.doc[5]])

    def test_contains(self) -> None:
        """should report if a key is in the index"""
        # "be" is in the index; "missing" is not
        self.assertTrue("be" in self.idx)
        self.assertFalse("missing" in self.idx)

    def test_iter(self) -> None:
        """should iterate through entries in index"""
        # when iterating, token texts will be Lexeme objects
        entries = list(iter(self.idx))
        self.assertEqual(entries[0], (self.nlp.vocab["To"], [self.doc[0]]))
        self.assertEqual(entries[1], (self.nlp.vocab["be"], [
                         self.doc[1], self.doc[5]]))

    def test_filter(self) -> None:
        """should iterate through entries in index that match predicate"""
        # test filtering to only unique tokens; "be" occurs more than once
        unique = list(self.idx.filter(lambda entry: len(entry[1]) == 1))
        self.assertEqual(unique[0], (self.nlp.vocab["To"], [self.doc[0]]))
        unique_texts = [self.nlp.vocab[entry[0]] for entry in unique]
        self.assertTrue("be" not in unique_texts)


class TestNgramPhonemesLookupsIndex(TestCase):
    """Test the index spaCy pipeline component."""

    def setUp(self) -> None:
        """Create a blank spaCy pipeline, index, and doc for testing."""
        self.nlp = spacy.blank("en")
        self.idx = NgramPhonemesLookupsIndex(self.nlp)
        self.doc = self.nlp("To be or not to be")

    def test_call(self) -> None:
        """foo"""
        pass
