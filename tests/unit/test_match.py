"""Tests for the match module."""

from unittest import TestCase

import spacy

from dphon.match import Match


class TestMatch(TestCase):
    """Test the Match model."""

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
        self.assertEqual(match.__repr__(), "Match([4:6], [2:4])")

    def test_str(self) -> None:
        """should print its text in both docs as a string"""
        left = self.doc1[4:6]
        right = self.doc2[2:4]
        match = Match(left, right)
        self.assertEqual(str(match), "glass tumbler :: glass tumbler")

    def test_lt(self) -> None:
        """should form a total order by both doc and position"""
        doc1 = self.nlp.make_doc("A B C D A B C D E F G H")
        doc2 = self.nlp.make_doc("Z Z G H Z Z C D Z Z Z Z")
        doc3 = self.nlp.make_doc("E F X X A B C D X X X X")
        m1 = Match(doc1[8:10], doc3[0:2]) # 1:EF :: 3:EF
        m2 = Match(doc1[0:4], doc3[4:9]) # 1:ABCD :: 3:ABCD
        m3 = Match(doc1[10:12], doc2[0:2]) # 1:GH :: 2:GH
        m4 = Match(doc1[4:9], doc3[4:9]) # 1:ABCD :: 3:ABCD
        m5 = Match(doc1[2:4], doc2[6:8]) # 1:CD :: 2:CD
        m6 = Match(doc1[7:9], doc2[6:8]) # 1:CD :: 2:CD
        m7 = Match(doc2[6:8], doc3[6:8]) # 2:CD :: 3:CD
        m_unsorted = [m1, m2, m3, m4, m5, m6, m7]
        m_sorted = list(sorted(m_unsorted))
        self.assertListEqual(m_sorted, [m5, m6, m3, m2, m4, m1, m7])
