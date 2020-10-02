"""Tests for the phonetic module."""

from unittest import TestCase

import spacy
from spacy.tokens import Doc

from dphon.phonemes import Phonemes


class TestPhonemes(TestCase):
    """Test the phonemes spaCy pipeline component."""

    def setUp(self) -> None:
        """Create a blank spaCy pipeline to use in tests."""
        self.nlp = spacy.blank("en")

    def tearDown(self) -> None:
        """Explicitly destroy the component to prevent name collisions."""
        if hasattr(self, "px"):
            del self.px

    def test_defaults(self) -> None:
        """should populate name and attr by default"""
         self.px = Phonemes(self.nlp, )
