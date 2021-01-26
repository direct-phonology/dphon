# -*- coding: utf-8 -*-
"""Formatter unit tests."""

from unittest import TestCase

import spacy
from dphon.fmt import SimpleFormatter
from dphon.match import Match


class TestSimpleFormatter(TestCase):
    """Test the SimpleFormatter."""

    def setUp(self) -> None:
        """Create docs and match for testing."""
        self.nlp = spacy.blank("en")
        self.doc1 = self.nlp.make_doc("a bumblebee under a glass tumbler")
        self.doc2 = self.nlp.make_doc("an inverted glass tumbler of fireflies")

        # a glass tumbler (doc1) :: an inverted glass tumbler (doc2)
        self.match = Match("doc1", "doc2", self.doc1[3:], self.doc2[:4])

    def test_doc_title(self) -> None:
        """should format matches with doc titles"""
        fmt = SimpleFormatter()
        output = fmt(self.match)

        # both titles should be in output
        self.assertTrue("doc1" in output)
        self.assertTrue("doc2" in output)

    def test_sequence_indices(self) -> None:
        """should format matches with sequence start and end indices"""
        fmt = SimpleFormatter()
        output = fmt(self.match)

        # sequence in doc1 is from token 4 (index 3) to token 6 (index 5)
        self.assertTrue("3–5" in output)
        # sequence in doc2 is from token 1 (index 0) to token 4 (index 3)
        self.assertTrue("0–3" in output)

    def test_aligned_match(self) -> None:
        """should format matches using stored alignment if present"""
        # add an alignment
        fmt = SimpleFormatter()
        match = Match("doc1", "doc2", self.match.utxt, self.match.vtxt, 0,
                      "a -------- glass tumbler",
                      "an inverted glass tumbler")
        output = fmt(match)

        # output should include aligned version
        self.assertTrue("a          glass tumbler" in output)

    def test_unaligned_match(self) -> None:
        """should format matches using stored sequences if no alignment"""
        fmt = SimpleFormatter()
        output = fmt(self.match)
        self.assertTrue("a glass tumbler" in output)
        self.assertTrue("an inverted glass tumbler" in output)

    def test_gap_char(self) -> None:
        """should allow customization of gap character in alignments"""
        fmt = SimpleFormatter(gap_char="$")

        # add an alignment
        match = Match("doc1", "doc2", self.match.utxt, self.match.vtxt, 0,
                      "a -------- glass tumbler",
                      "an inverted glass tumbler")
        output = fmt(match)

        # should use gap character in output
        self.assertTrue("a $$$$$$$$ glass tumbler" in output)

    def test_nl_char(self) -> None:
        """should allow customization of newline character in sequences"""
        doc3 = self.nlp.make_doc("a\n glass tumbler")
        match = Match("doc1", "doc3", self.doc1[3:], doc3[:])
        fmt = SimpleFormatter(nl_char="$")
        output = fmt(match)

        # should use newline character in output
        self.assertTrue("a$ glass tumbler" in output)
