"""Test the n-grams spaCy pipeline component."""

from typing import Any
from unittest import TestCase
from unittest.mock import Mock, patch

import spacy
from spacy.tokens import Doc

from dphon.ngrams import Ngrams


class TestNgrams(TestCase):

    def setUp(self) -> None:
        """Create a blank pipeline to use in tests."""
        self.nlp = spacy.blank("en")

    def tearDown(self) -> None:
        """Explicitly destroy the component to prevent name collisions."""
        if hasattr(self, "ng"):
            del self.ng

    def test_default(self) -> None:
        """should populate name and attr by default and store n"""
        self.ng = Ngrams(self.nlp, n=4)
        self.nlp.add_pipe(self.ng)
        self.assertEqual(self.ng.n, 4)
        self.assertTrue(Doc.has_extension("ngrams"))
        self.assertTrue(self.nlp.has_pipe("ngrams"))

    def test_custom_name(self) -> None:
        """should accept a custom name for pipeline component"""
        self.ng = Ngrams(self.nlp, name="my_ngrams", n=4)
        self.nlp.add_pipe(self.ng)
        self.assertTrue(self.nlp.has_pipe("my_ngrams"))

    def test_custom_attr(self) -> None:
        """should accept a custom attribute name for accessing ngrams"""
        self.ng = Ngrams(self.nlp, attr="my_ngrams", n=4)
        self.nlp.add_pipe(self.ng)
        self.assertTrue(Doc.has_extension("my_ngrams"))

    def test_unigrams(self) -> None:
        """should create single-token n-grams successfully"""
        self.ng = Ngrams(self.nlp, n=1)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, [
            "It", "was", "a", "dark", "and", "stormy", "night"
        ])

    def test_bigrams(self) -> None:
        """should create 2-token n-grams successfully"""
        self.ng = Ngrams(self.nlp, n=2)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, [
            "It was", "was a", "a dark", "dark and", "and stormy",
            "stormy night"
        ])

    def test_trigrams(self) -> None:
        """should create 3-token n-grams successfully"""
        self.ng = Ngrams(self.nlp, n=3)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, [
            "It was a", "was a dark", "a dark and", "dark and stormy",
            "and stormy night"
        ])

    def test_empty_doc(self) -> None:
        """should handle an empty doc"""
        self.ng = Ngrams(self.nlp, n=3)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, [])

    def test_one_token_doc(self) -> None:
        """should handle a doc with one token"""
        self.ng = Ngrams(self.nlp, n=3)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("Nope")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, ["Nope"])

    def test_n_larger_than_doc(self) -> None:
        """should handle a value for n larger than the doc itself"""
        self.ng = Ngrams(self.nlp, n=5)
        self.nlp.add_pipe(self.ng)
        doc = self.nlp.make_doc("No way")
        results = [str(ngram) for ngram in doc._.ngrams]
        self.assertEqual(results, ["No way"])
