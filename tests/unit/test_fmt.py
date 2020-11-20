# -*- coding: utf-8 -*-
"""Formatter unit tests."""

from unittest import TestCase

import spacy
from dphon.fmt import SimpleFormatter
from dphon.match import Match
from spacy.tokens import Doc


class TestSimpleFormatter(TestCase):
    """Test the SimpleFormatter."""

    def setUp(self) -> None:
        """Create docs and match for testing."""
        self.nlp = spacy.blank("en")
        self.doc1 = self.nlp.make_doc("a bumblebee under a glass tumbler")
        self.doc2 = self.nlp.make_doc("an inverted glass tumbler of fireflies")
        # a glass tumbler (doc1)
        # an inverted glass tumbler (doc2)
        self.match = Match(self.doc1[3:], self.doc2[:4])

    def tearDown(self) -> None:
        """Unregister doc attribute to prevent name collisions."""
        if Doc.has_extension("title"):
            Doc.remove_extension("title")

    def test_doc_title(self) -> None:
        """should format matches with doc titles if present"""
        fmt = SimpleFormatter()
        # add doc titles
        Doc.set_extension("title", default="")
        self.doc1._.title = "doc1"
        self.doc2._.title = "doc2"
        output = fmt(self.match)
        # should be in output
        self.assertTrue("doc1" in output)
        self.assertTrue("doc2" in output)

    def test_no_doc_title(self) -> None:
        """should format matches with doc ids if no doc titles"""
        fmt = SimpleFormatter()
        output = fmt(self.match)
        # ids should be in output
        self.assertTrue(str(id(self.doc1)) in output)
        self.assertTrue(str(id(self.doc2)) in output)

    def test_aligned_match(self) -> None:
        """should format matches using stored alignment if present"""
        # add an alignment
        fmt = SimpleFormatter()
        match = Match(self.match.left, self.match.right,
                      (["a ", "-------- ", "glass ", "tumbler"],
                       ["an ", "inverted ", "glass ", "tumbler"]))
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
        match = Match(self.match.left, self.match.right,
                      (["a ", "-------- ", "glass ", "tumbler"],
                       ["an ", "inverted ", "glass ", "tumbler"]))
        output = fmt(match)
        # should use gap character in output
        self.assertTrue("a $$$$$$$$ glass tumbler" in output)

    def test_nl_char(self) -> None:
        """should allow customization of newline character in sequences"""
        doc3 = self.nlp.make_doc("a\n glass tumbler")
        match = Match(self.doc1[3:], doc3[:])
        fmt = SimpleFormatter(nl_char="$")
        output = fmt(match)
        # should use newline character in output
        self.assertTrue("a$ glass tumbler" in output)
