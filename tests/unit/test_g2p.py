"""Tests for the phonemes module."""

import logging
from unittest import TestCase

import spacy
from dphon.match import Match
from dphon.g2p import GraphemesToPhonemes, OOV_PHONEMES
from spacy.tokens import Doc, Span, Token

# disconnect logging for testing
logging.disable(logging.CRITICAL)


class TestG2P(TestCase):
    """Test the g2p spaCy pipeline component."""

    def setUp(self) -> None:
        """Set up a basic pipeline with sound table for testing."""
        self.nlp = spacy.blank("en")
        self.px = GraphemesToPhonemes(self.nlp, sound_table={
            "1": ("w", "ʌn"),
            "2": ("t", "uː"),
            "3": ("θ", "riː"),
            "one": ("w", "ʌn"),
            "two": ("t", "uː"),
            "three": ("θ", "riː"),
            "to": ("t", "uː"),
            "too": ("t", "uː"),
        })

    def test_defaults(self) -> None:
        """should create lookups sound table and register extensions"""
        self.assertTrue(self.nlp.vocab.lookups.has_table("phonemes"))
        self.assertTrue(Doc.has_extension("phonemes"))
        self.assertTrue(Span.has_extension("phonemes"))
        self.assertTrue(Token.has_extension("phonemes"))
        self.assertTrue(Token.has_extension("is_oov"))

    def test_is_token_oov(self) -> None:
        """should detect if a token is not in the sound table"""
        doc1 = self.nlp("we're number one")
        # "number" isn't in the table...
        self.assertTrue(self.px.is_token_oov(doc1[2]))
        # ...but "one" is
        self.assertFalse(self.px.is_token_oov(doc1[3]))

    def test_are_graphic_variants(self) -> None:
        """should correctly detect if a set of tokens are graphic variants"""
        doc1 = self.nlp("that's two now!")
        doc2 = self.nlp("2 too many")
        doc3 = self.nlp("one to remember")
        # "two" and "too" rhyme, so (theoretically) could be variants
        self.assertTrue(self.px.are_graphic_variants(doc1[2], doc2[1]))
        # "two", "too", "to", and "2" could all be variants
        self.assertTrue(self.px.are_graphic_variants(
            doc1[2], doc2[1], doc2[0], doc3[1]))
        # "too" and "too" aren't variants because they're the same word
        self.assertFalse(self.px.are_graphic_variants(doc2[1], doc2[1]))
        # "one" isn't a variant of the above because it sounds different
        self.assertFalse(self.px.are_graphic_variants(
            doc1[2], doc2[1], doc3[0]))
        # "!" isn't voiced, so it can't be a variant
        self.assertFalse(self.px.are_graphic_variants(
            doc1[2], doc2[1], doc1[4]))
        # "remember" isn't in our table, so it can't be a variant
        self.assertFalse(self.px.are_graphic_variants(
            doc1[2], doc2[1], doc3[2]))

    def test_has_variant(self) -> None:
        """should detect if seed sequences have a graphic variant"""
        # create testing docs
        doc1 = self.nlp("that's two now!")
        doc2 = self.nlp("that's 2 now!")
        doc3 = self.nlp("that's three now!")

        # "two" and "2" are variants
        m1 = Match("doc1", "doc2", doc1[:], doc2[:])
        self.assertTrue(self.px.has_variant(m1))

        # identical text means no variant
        m2 = Match("doc1", "doc1", doc1[:], doc1[:])
        self.assertFalse(self.px.has_variant(m2))

        # different sound means no variant
        m3 = Match("doc1", "doc3", doc1[:], doc3[:])
        self.assertFalse(self.px.has_variant(m3))

    def test_get_all_phonemes(self) -> None:
        """should iterate over all valid phonemes in a span or doc"""
        doc = self.nlp("one two 3 go!")
        # "go" has no entry and will be marked by OOV_PHONEMES;
        # "!" is non-voiced and won't appear
        self.assertEqual(list(self.px.get_all_phonemes(doc)), [
                         "w", "ʌn", "t", "uː", "θ", "riː", OOV_PHONEMES])
        # try running on a shorter span - "two 3"
        span = doc[1:3]
        self.assertEqual(list(self.px.get_all_phonemes(span)),
                         ["t", "uː", "θ", "riː"])

    def test_get_token_phonemes(self) -> None:
        """should return phonemes for a token if any exist"""
        doc = self.nlp("one two 3 go!")
        # "one" is in the table
        self.assertEqual(self.px.get_token_phonemes(doc[0]), ("w", "ʌn"))
        # "go" isn't in the table; it should return OOV_PHONEMES
        self.assertEqual(self.px.get_token_phonemes(doc[3]), (OOV_PHONEMES,))
        # "!" is non-voiced, it should return a syllable of `None`s
        self.assertEqual(self.px.get_token_phonemes(doc[4]), (None, None))
