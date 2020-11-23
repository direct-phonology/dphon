"""Tests for the indexing module."""

import logging
from itertools import islice
from unittest import TestCase

import spacy
from dphon.index import Index

# disconnect logging for testing
logging.disable(logging.CRITICAL)


class TestIndex(TestCase):
    """Test the index spaCy pipeline component."""

    def setUp(self) -> None:
        """Create a blank spaCy pipeline and doc for testing."""
        self.nlp = spacy.blank("en")
        self.doc = self.nlp.make_doc("To be or not to be")

    def test_defaults(self) -> None:
        """should use name `index` and create lookup table by default"""
        idx = Index(self.nlp)
        self.nlp.add_pipe(idx)
        self.assertEqual(idx.name, "index")
        self.assertTrue(self.nlp.has_pipe("index"))
        self.assertTrue(self.nlp.vocab.lookups.has_table("index"))
        
    def test_val_fn(self) -> None:
        """can get values to index via a provided callable"""
        # example: only index the first three tokens from each doc
        first_three_tokens = lambda doc: islice(doc, 3)
        idx = Index(self.nlp, val_fn=first_three_tokens)
        idx(self.doc)
        self.assertEqual(idx.size, 3) # only indexed 3 tokens total
        self.assertFalse("not" in idx) # "not" wasn't indexed

    def test_filter_fn(self) -> None:
        """can skip indexing values if they fail a provided predicate"""
        # example: index tokens only if they are lowercase
        all_lowercase = lambda token: token.is_lower
        idx = Index(self.nlp, filter_fn=all_lowercase)
        idx(self.doc)
        self.assertEqual(idx.size, 5) # indexed all but one token
        self.assertFalse("To" in idx) # "To" wasn't indexed

    def test_key_fn(self) -> None:
        """can index values at a key generated via a provided callable"""
        # example: index tokens by their character position
        token_position = lambda token: token.idx
        idx = Index(self.nlp, key_fn=token_position)
        idx(self.doc)
        self.assertEqual(idx[0], [self.doc[0]]) # "To" is at beginning
        self.assertEqual(idx[3], [self.doc[1]]) # "be" occurs in two places
        self.assertEqual(idx[16], [self.doc[5]])

    def test_len(self) -> None:
        """should get the total number of keys in the index"""
        idx = Index(self.nlp)
        idx(self.doc)
        self.assertEqual(len(idx), 5) # 5 unique token texts

    def test_size(self) -> None:
        """should get the total number of values in the index"""
        idx = Index(self.nlp)
        idx(self.doc)
        self.assertEqual(idx.size, 6) # 6 total tokens

    def test_getitem(self) -> None:
        """should access values by key"""
        idx = Index(self.nlp)
        idx(self.doc)
        self.assertEqual(idx["be"], [self.doc[1], self.doc[5]]) # two tokens with "be"
        self.assertEqual(idx["or"], [self.doc[2]]) # one token with "or"

    def test_contains(self) -> None:
        """should check if a key is present"""
        idx = Index(self.nlp)
        idx(self.doc)
        self.assertTrue("be" in idx)
        self.assertFalse("tuna" in idx)

    def test_iter(self) -> None:
        """should iterate over its key/value pairs"""
        idx = Index(self.nlp)
        idx(self.doc)
        entries = list(iter(idx))
        # Note that token texts are technically Lexemes so we need to convert
        self.assertEqual(entries[0], (self.nlp.vocab["To"], [self.doc[0]]))
        self.assertEqual(entries[1], (self.nlp.vocab["be"], [self.doc[1], self.doc[5]]))
        self.assertEqual(entries[2], (self.nlp.vocab["or"], [self.doc[2]]))

    def test_filter(self) -> None:
        """should iterate over a subset of its key/value pairs"""
        # example: get all the entries with at least two tokens
        idx = Index(self.nlp)
        idx(self.doc)
        entries = list(idx.filter(lambda entry: len(entry[1]) > 1))
        self.assertEqual(len(entries), 1) # "be" occurs twice
        self.assertEqual(entries[0][0], self.nlp.vocab["be"])
