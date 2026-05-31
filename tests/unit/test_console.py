"""Tests for the console module."""

from re import match

import spacy
from unittest import TestCase

from dphon.match import Match
from dphon.console import MatchHighlighter
from dphon.g2p import GraphemesToPhonemes
from dphon.align import SmithWatermanPhoneticAligner

class TestMatchHighlighter(TestCase):
    """Test the MatchHighlighter."""

    def setUp(self) -> None:
        """Set up objects for testing."""

        # set up a g2p component with a simple sound table for testing
        self.nlp = spacy.blank("en")
        self.g2p = GraphemesToPhonemes(
            self.nlp,
            sound_table={
                "1": ("w", "ʌn"),
                "2": ("t", "uː"),
                "3": ("θ", "riː"),
                "one": ("w", "ʌn"),
                "two": ("t", "uː"),
                "three": ("θ", "riː"),
                "to": ("t", "uː"),
                "too": ("t", "uː"),
                "four": ("f", "ɔːr"),
            },
        )

        # set up an aligner for testing
        self.align = SmithWatermanPhoneticAligner()

        # force using entire syllable for testing
        self.g2p._select = lambda reading: reading  # type: ignore

    def test_transcribe(self) -> None:
        """should transcribe a span"""
        highlighter = MatchHighlighter(self.g2p)
        span = self.nlp("one two three")[1:2] # the "two" token, with 1 token of context
        self.assertEqual(highlighter.transcribe_span(span), "*tuː")

    def test_transcribe_with_context(self) -> None:
        """should transcribe including highlighted context if configured"""
        highlighter = MatchHighlighter(self.g2p, context=1, transcribe_context=True)
        span = self.nlp("one two three")[1:2] # the "two" token, with 1 token of context
        self.assertEqual(
            highlighter.transcribe_span_with_context(span),
            "[context]*wʌn[/context] tuː [context]θriː[/context]",
        )

    def test_added_context(self) -> None:
        """should transcribe and highlight a match with context added"""
        highlighter = MatchHighlighter(self.g2p, context=1, transcribe_context=True)
        doc1 = self.nlp("one two three")
        doc2 = self.nlp("too four")
        match = Match(
            u="doc1",
            v="doc2",
            utxt=doc1[1:2], # "two"
            vtxt=doc2[:1],  # "too", which should be marked as a variant
        )
        aligned = self.align(match)
        su, sv = highlighter.format_match(aligned)
        pu, pv = highlighter.transcribe_match(aligned)
        self.assertEqual(su, "[context]one[/context] [variant]two[/variant] [context]three[/context]")
        self.assertEqual(sv, "[variant]too[/variant] [context]four[/context]")
        self.assertEqual(pu, "[context]*wʌn[/context] tuː [context]θriː[/context]")
        self.assertEqual(pv, "*tuː [context]fɔːr[/context]")
