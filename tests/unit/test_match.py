from unittest import TestCase

import spacy
from dphon.match import Match


class TestMatch(TestCase):
    """Test the Match class."""

    maxDiff = None   # don't limit length of diff output for failures

    def setUp(self) -> None:
        """Create example Docs to test with."""
        self.nlp = spacy.blank("en")
        self.doc1 = self.nlp.make_doc("a bumblebee under a glass tumbler")
        self.doc2 = self.nlp.make_doc("an inverted glass tumbler of fireflies")

    def test_sort(self) -> None:
        """should form a total order by doc title and position"""
        doc1 = self.nlp.make_doc("A B C D A B C D E F G H")
        doc2 = self.nlp.make_doc("Z Z G H Z Z C D Z Z Z Z")
        doc3 = self.nlp.make_doc("E F X X A B C D X X X X")
        m1 = Match("doc1", "doc3", doc1[8:10], doc3[0:2])   # 1:EF :: 3:EF
        m2 = Match("doc1", "doc3", doc1[0:4], doc3[4:9])    # 1:ABCD :: 3:ABCD
        m3 = Match("doc1", "doc2", doc1[10:12], doc2[0:2])  # 1:GH :: 2:GH
        m4 = Match("doc1", "doc3", doc1[4:9], doc3[4:9])    # 1:ABCD :: 3:ABCD
        m5 = Match("doc1", "doc2", doc1[2:4], doc2[6:8])    # 1:CD :: 2:CD
        m6 = Match("doc1", "doc2", doc1[7:9], doc2[6:8])    # 1:CD :: 2:CD
        m7 = Match("doc2", "doc3", doc2[6:8], doc3[6:8])    # 2:CD :: 3:CD
        m_unsorted = [m1, m2, m3, m4, m5, m6, m7]
        m_sorted = list(sorted(m_unsorted))
        self.assertEqual(m_sorted, [m5, m6, m3, m2, m4, m1, m7])

    def test_equality(self) -> None:
        """should test equality via doc and position"""
        utxt = self.doc1[4:6]
        vtxt = self.doc2[2:4]

        # shallow copies of spans should be equal
        m1 = Match("doc1", "doc2", utxt, vtxt)
        m2 = Match("doc1", "doc2", utxt, vtxt)
        self.assertEqual(m1, m2)

        # pre-copied spans should also be equal
        m3 = Match("doc1", "doc2", self.doc1[4:6], self.doc2[2:4])
        self.assertEqual(m1, m3)
