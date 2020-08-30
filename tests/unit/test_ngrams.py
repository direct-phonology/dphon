"""Test the n-grams spaCy pipeline component."""

from unittest import TestCase
from unittest.mock import patch, MagicMock

import spacy
from spacy.tokens import Doc

from dphon.ngrams import Ngrams

class TestNgrams(TestCase):

    def setUp(self) -> None:
        """Create a blank pipeline to use in tests."""
        self.nlp = spacy.blank("en")
    
    def test_init(self) -> None:
        """should store the value for `n` and component's name on init"""
        quadgrams = Ngrams(self.nlp, name="quadgrams", n=4, attr="quadgrams")
        self.assertEqual(quadgrams.n, 4)
        self.assertEqual(quadgrams.name, "quadgrams")

    def test_attr(self) -> None:
        """should add a custom getter attribute to Doc on init"""
        # by default, uses the name "ngrams"
        trigrams = Ngrams(self.nlp, name="trigrams", n=3)
        self.assertTrue(Doc.has_extension("ngrams"))
        # if attr is provided, will register using that name instead
        quadgrams = Ngrams(self.nlp, name="quadgrams", n=4, attr="quadgrams")
        self.assertTrue(Doc.has_extension("quadgrams"))

    def test_unigrams(self) -> None:
        """should create single-token n-grams successfully"""
        unigrams = Ngrams(self.nlp, n=1, name="unigrams", attr="unigrams")
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = list(doc._.unigrams)
        self.assertEqual(len(results), 7)
        self.assertEqual(str(results[0]), "It")
        self.assertEqual(str(results[-1]), "night")

    def test_bigrams(self) -> None:
        """should create 2-token n-grams successfully"""
        bigrams = Ngrams(self.nlp, n=2, name="bigrams", attr="bigrams")
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = list(doc._.bigrams)
        self.assertEqual(len(results), 6)
        self.assertEqual(str(results[0]), "It was")
        self.assertEqual(str(results[-1]), "stormy night")

    def test_trigrams(self) -> None:
        """should create 3-token n-grams successfully"""
        trigrams = Ngrams(self.nlp, n=3, name="trigrams", attr="trigrams")
        doc = self.nlp.make_doc("It was a dark and stormy night")
        results = list(doc._.trigrams)
        self.assertEqual(len(results), 5)
        self.assertEqual(str(results[0]), "It was a")
        self.assertEqual(str(results[-1]), "and stormy night")

    def test_one_token_doc(self) -> None:
        """should handle a doc with one token"""
        quadgrams = Ngrams(self.nlp, name="quadgrams", n=4, attr="quadgrams")
        doc = self.nlp.make_doc("Nope")
        results = list(doc._.quadgrams)
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]), "Nope")
