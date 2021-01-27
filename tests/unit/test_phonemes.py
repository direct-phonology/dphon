"""Tests for the phonemes module."""

import logging
from unittest import TestCase

import spacy
from dphon.match import Match
from dphon.phonemes import OOV_PHONEMES, Phonemes
from spacy.tokens import Doc, Span, Token

# disconnect logging for testing
logging.disable(logging.CRITICAL)


class TestPhonemes(TestCase):
    """Test the phonemes spaCy pipeline component."""

    def setUp(self) -> None:
        """Set up a basic pipeline with sound table for testing."""
        self.nlp = spacy.blank("en")
        self.sound_table = {
            "1": ("w", "ʌn"),
            "2": ("t", "uː"),
            "3": ("θ", "riː"),
            "one": ("w", "ʌn"),
            "two": ("t", "uː"),
            "three": ("θ", "riː"),
            "to": ("t", "uː"),
            "too": ("t", "uː"),
        }
        self.px = Phonemes(self.nlp, self.sound_table)

    def tearDown(self) -> None:
        """Unregister the component to prevent name collisions."""
        if hasattr(self, "px"):
            self.px.teardown()

    def test_defaults(self) -> None:
        """should populate name and attr by default and store sound table"""
        self.nlp.add_pipe(self.px)
        self.assertTrue(self.nlp.vocab.lookups.has_table("phonemes"))
        self.assertTrue(Doc.has_extension("phonemes"))
        self.assertTrue(Span.has_extension("phonemes"))
        self.assertTrue(Token.has_extension("phonemes"))
        self.assertTrue(Token.has_extension("is_oov"))
        self.assertTrue(self.nlp.has_pipe("phonemes"))

    def test_is_token_oov(self) -> None:
        """should detect if a token is not in the sound table"""
        doc1 = self.nlp.make_doc("we're number one")
        # "number" isn't in the table...
        self.assertTrue(doc1[2]._.is_oov)
        # ...but "one" is
        self.assertFalse(doc1[3]._.is_oov)

    def test_are_graphic_variants(self) -> None:
        """should correctly detect if a set of tokens are graphic variants"""
        doc1 = self.nlp.make_doc("that's two now!")
        doc2 = self.nlp.make_doc("2 too many")
        doc3 = self.nlp.make_doc("one to remember")
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
        doc1 = self.nlp.make_doc("that's two now!")
        doc2 = self.nlp.make_doc("that's 2 now!")
        doc3 = self.nlp.make_doc("that's three now!")

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
        doc = self.nlp.make_doc("one two 3 go!")
        # "go" has no entry and "!" is non-voiced; they won't appear
        self.assertEqual(list(doc._.phonemes), [
                         "w", "ʌn", "t", "uː", "θ", "riː"])
        # try running on a span without "one" in it
        span = doc[1:]
        self.assertEqual(list(span._.phonemes), ["t", "uː", "θ", "riː"])

    def test_get_token_phonemes(self) -> None:
        """should return phonemes for a token if any exist"""
        doc = self.nlp.make_doc("one two 3 go!")
        # "one" is in the table
        self.assertEqual(doc[0]._.phonemes, ("w", "ʌn"))
        # "go" isn't in the table; it should return OOV_PHONEMES
        self.assertEqual(doc[3]._.phonemes, (OOV_PHONEMES,))
        # "!" is non-voiced, it should return a syllable of `None`s
        self.assertEqual(doc[4]._.phonemes, (None, None))
