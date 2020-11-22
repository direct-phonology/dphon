"""Tests for the match module."""

from unittest import TestCase, skip

import spacy
from spacy.tokens import Doc

from dphon.match import Match


class TestMatch(TestCase):
    """Test the Match model."""

    maxDiff = None   # don't limit length of diff output for failures

    def setUp(self) -> None:
        """Create example Docs to test with."""
        self.nlp = spacy.blank("en")
        self.doc1 = self.nlp.make_doc("a bumblebee under a glass tumbler")
        self.doc2 = self.nlp.make_doc("an inverted glass tumbler of fireflies")

    def test_init(self) -> None:
        """should make a shallow copy of its provided locations on init"""
        left = self.doc1[4:6]   # "glass tumbler"
        right = self.doc2[2:4]  # "glass tumbler"
        match = Match(left, right)
        # match has its own copy of the spans
        self.assertNotEqual(id(left), id(match.left))
        self.assertNotEqual(id(right), id(match.right))
        # but its spans point to the same tokens in memory
        self.assertEqual(id(left[0]), id(match.left[0]))    # "glass"
        self.assertEqual(id(right[0]), id(match.right[0]))  # "glass"

    def test_repr(self) -> None:
        """should print a representation of its locations"""
        left = self.doc1[4:6]
        right = self.doc2[2:4]
        match = Match(left, right)
        self.assertEqual(match.__repr__(), f"Match([4:6], [2:4])")

    def test_str(self) -> None:
        """should print its text in both docs"""
        left = self.doc1[4:6]
        right = self.doc2[2:4]
        match = Match(left, right)
        self.assertEqual(str(match), "glass tumbler :: glass tumbler")

    def test_lt(self) -> None:
        """should form a total order by position"""
        doc1 = self.nlp.make_doc("A B C D A B C D E F G H")
        doc2 = self.nlp.make_doc("Z Z G H Z Z C D Z Z Z Z")
        doc3 = self.nlp.make_doc("E F X X A B C D X X X X")
        m1 = Match(doc1[8:10], doc3[0:2])  # 1:EF :: 3:EF
        m2 = Match(doc1[0:4], doc3[4:9])  # 1:ABCD :: 3:ABCD
        m3 = Match(doc1[10:12], doc2[0:2])  # 1:GH :: 2:GH
        m4 = Match(doc1[4:9], doc3[4:9])  # 1:ABCD :: 3:ABCD
        m5 = Match(doc1[2:4], doc2[6:8])  # 1:CD :: 2:CD
        m6 = Match(doc1[7:9], doc2[6:8])  # 1:CD :: 2:CD
        m7 = Match(doc2[6:8], doc3[6:8])  # 2:CD :: 3:CD
        m_unsorted = [m1, m2, m3, m4, m5, m6, m7]
        m_sorted = list(sorted(m_unsorted))
        self.assertEqual(m_sorted, [m2, m5, m4, m7, m6, m1, m3])

    def test_eq(self) -> None:
        """should test equality via position"""
        left = self.doc1[4:6]
        right = self.doc2[2:4]
        # shallow copies of spans should be equal
        m1 = Match(left, right)
        m2 = Match(left, right)
        self.assertEqual(m1, m2)
        # pre-copied spans should also be equal
        m3 = Match(self.doc1[4:6], self.doc2[2:4])
        self.assertEqual(m1, m3)

    def test_norm_eq(self) -> None:
        """should detect if its texts are identical after normalization"""
        doc1 = self.nlp.make_doc("What's that?")
        doc2 = self.nlp.make_doc("whatsthat")
        doc3 = self.nlp.make_doc("Whats that now?")
        m1 = Match(doc1[:], doc2[:])
        m2 = Match(doc1[:], doc3[:])
        self.assertTrue(m1.is_norm_eq)
        self.assertFalse(m2.is_norm_eq)
