"""Tests for the n-grams module."""

from dphon.ngrams import Ngrams
from unittest import TestCase

import spacy
from spacy.tokens import Doc


class TestNgrams(TestCase):
    """Test the n-grams spaCy pipeline component."""

    def setUp(self) -> None:
        """create blank spaCy language for testing"""
        self.nlp = spacy.blank("en")

    def test_defaults(self) -> None:
        """should store value for n and set extensions"""
        ngrams = Ngrams(self.nlp, n=4)
        self.assertEqual(ngrams.n, 4)
        self.assertTrue(Doc.has_extension("ngrams"))

    def test_unigrams(self) -> None:
        """should create single-token n-grams successfully"""
        ngrams = Ngrams(self.nlp, n=1)
        doc = self.nlp("It was a dark and stormy night")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, [
            "It", "was", "a", "dark", "and", "stormy", "night"
        ])

    def test_bigrams(self) -> None:
        """should create 2-token n-grams successfully"""
        ngrams = Ngrams(self.nlp, n=2)
        doc = self.nlp("It was a dark and stormy night")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, [
            "It was", "was a", "a dark", "dark and", "and stormy",
            "stormy night"
        ])

    def test_trigrams(self) -> None:
        """should create 3-token n-grams successfully"""
        ngrams = Ngrams(self.nlp, n=3)
        doc = self.nlp("It was a dark and stormy night")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, [
            "It was a", "was a dark", "a dark and", "dark and stormy",
            "and stormy night"
        ])

    def test_empty_doc(self) -> None:
        """should handle an empty doc"""
        ngrams = Ngrams(self.nlp, n=3)
        doc = self.nlp("")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, [])

    def test_one_token_doc(self) -> None:
        """should handle a doc with one token"""
        ngrams = Ngrams(self.nlp, n=3)
        doc = self.nlp("Nope")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, ["Nope"])

    def test_n_larger_than_doc(self) -> None:
        """should handle a value for n larger than the doc itself"""
        ngrams = Ngrams(self.nlp, n=5)
        doc = self.nlp("No way")
        results = [str(ngram) for ngram in ngrams.get_doc_ngrams(doc)]
        self.assertEqual(results, ["No way"])
