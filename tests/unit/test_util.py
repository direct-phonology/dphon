"""Utility function unit tests."""

from unittest import TestCase, skip

import spacy
from spacy.tokens import Doc

from dphon.extend import LevenshteinExtender
from dphon.reuse import Match
from dphon.util import extend_matches, group_by_doc, is_norm_eq

'''
class TestCondenseMatches(TestCase):

    def test_reduce_trigram_to_quad(self) -> None:
        """
        Two overlapping trigram matches should be condensed into a single
        quad-gram match.
        """
        matches = [
            Match(0, 1, slice(0, 2), slice(1, 3)),
            Match(0, 1, slice(1, 3), slice(2, 4))
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(0, 3), slice(1, 4))
        ])

    def test_different_match_lengths(self) -> None:
        """
        A long match that overlaps with a short match should be combined into
        a single match comprising the content of both matches.
        """
        matches = [
            Match(0, 1, slice(3, 17), slice(1, 15)),
            Match(0, 1, slice(16, 18), slice(14, 16))
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(3, 18), slice(1, 16))
        ])

    def test_multiple_overlap(self) -> None:
        """
        Sequences of consecutive overlapping matches should all be condensed
        into a single match.
        """
        matches = [
            Match(0, 1, slice(0, 2), slice(10, 12)),
            Match(0, 1, slice(1, 3), slice(11, 13)),
            Match(0, 1, slice(2, 4), slice(12, 14)),
            Match(0, 1, slice(3, 5), slice(13, 15)),
            Match(0, 1, slice(4, 6), slice(14, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37))  # unrelated
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(0, 6), slice(10, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37))  # unchanged
        ])

    def test_sub_overlap(self) -> None:
        """
        Sequences of consecutive overlapping matches with subsequences that
        also match elsewhere should be independently extended.
        """
        matches = [
            Match(0, 1, slice(8, 10), slice(13, 15)),
            Match(0, 1, slice(9, 11), slice(14, 16)),
            # subset matches elsewhere
            Match(0, 1, slice(10, 12), slice(1, 3)),
            Match(0, 1, slice(10, 12), slice(15, 17)),
            # subset needs to be extended
            Match(0, 1, slice(11, 13), slice(2, 4)),
            Match(0, 1, slice(11, 13), slice(16, 18)),
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(8, 13), slice(13, 18)),
            Match(0, 1, slice(10, 13), slice(1, 4))
        ])

    def test_mirror_submatches(self) -> None:
        """
        In matching sequences with repeated subsequences, we should get a
        large match covering the entirety of both sequences. We don't care
        about the internal matches between subsequences since they are
        subsumed in the larger sequence.
        """
        matches = [
            Match(0, 1, slice(1, 3), slice(1, 3)),
            Match(0, 1, slice(2, 4), slice(2, 4)),
            # subset matches later subset
            Match(0, 1, slice(2, 4), slice(12, 14)),
            Match(0, 1, slice(3, 6), slice(3, 6)),
            Match(0, 1, slice(4, 7), slice(4, 7)),
            Match(0, 1, slice(6, 8), slice(6, 8)),
            Match(0, 1, slice(7, 9), slice(7, 9)),
            Match(0, 1, slice(8, 11), slice(8, 11)),
            Match(0, 1, slice(9, 12), slice(9, 12)),
            Match(0, 1, slice(11, 13), slice(11, 13)),
            # mirror of earlier subset
            Match(0, 1, slice(12, 14), slice(2, 4)),
            Match(0, 1, slice(12, 14), slice(12, 14)),
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(1, 14), slice(1, 14))
        ])
'''


class TestGroupByDoc(TestCase):
    """Test grouping matches by doc."""

    @classmethod
    def setUpClass(cls) -> None:
        """Register the title attribute on Docs."""
        Doc.set_extension("title", default="")

    @classmethod
    def tearDownClass(cls) -> None:
        """Unregister the title attribute on Docs."""
        Doc.remove_extension("title")

    def setUp(self) -> None:
        """Create a blank spaCy model to test with."""
        self.nlp = spacy.blank("en")

    @skip("todo")
    def test_groups(self) -> None:
        """should group by left doc, then sort by sequence position"""
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
        m_grouped = list(group_by_doc(m_unsorted))


class TestIsNormEq(TestCase):

    def setUp(self) -> None:
        """Create a blank spaCy model to test with."""
        self.nlp = spacy.blank("en")

    def test_is_norm_eq(self) -> None:
        """should detect if match texts are identical after normalization"""
        doc1 = self.nlp.make_doc("What's that?")
        doc2 = self.nlp.make_doc("whatsthat")
        doc3 = self.nlp.make_doc("Whats that now?")
        m1 = Match(doc1[:], doc2[:])
        m2 = Match(doc1[:], doc3[:])
        self.assertTrue(is_norm_eq(m1))
        self.assertFalse(is_norm_eq(m2))


class TestExtendMatches(TestCase):
    """Test extending match lists."""

    @ classmethod
    def setUpClass(cls) -> None:
        """Register the title attribute on Docs."""
        Doc.set_extension("title", default="")

    @ classmethod
    def tearDownClass(cls) -> None:
        """Unregister the title attribute on Docs."""
        Doc.remove_extension("title")

    def setUp(self) -> None:
        """Create a blank spaCy model and extender to test with."""
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
        self.extend = LevenshteinExtender(threshold=0.75, len_limit=100)

    def test_no_extension(self) -> None:
        """matches that can't be extended any further should be unchanged

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""

        # create mock documents
        left = self.nlp.make_doc("千室之邑百乘之家")
        right = self.nlp.make_doc("千室之邑百乘之家")
        left._.title = "analects"
        right._.title = "shiji"
        # create matches and extend them
        matches = [Match(left[0:8], right[0:8])]
        # output should be identical to input
        results = extend_matches(matches, self.extend)
        self.assertEqual(results, matches)

    def test_perfect_match(self) -> None:
        """matches should be extended as far as possible

        Text sources:
        - https://ctext.org/text.pl?node=416724&if=en&filter=463451
        - https://ctext.org/text.pl?node=542654&if=en&filter=463451"""

        left = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        right = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        left._.title = "analects"
        right._.title = "yiwen-leiju"
        matches = [
            Match(left[0:4], right[0:4]),
            Match(left[1:5], right[1:5])
        ]
        results = extend_matches(matches, self.extend)
        # first match is kept and extended; second is discarded as internal
        self.assertEqual(results, [Match(left[0:18], right[0:18])])

    def test_sub_overlap(self) -> None:
        """consecutive overlapping matches should be independently extended"""
        left = self.nlp.make_doc("水善利萬物而不爭自見者不明弊則新無關")
        right = self.nlp.make_doc("可者不明下母得已以百姓為芻自見者不明")
        left._.title = "left"
        right._.title = "right"
        matches = [
            Match(left[8:10], right[13:15]),
            Match(left[9:11], right[14:16]),
            # subset matches elsewhere
            Match(left[10:12], right[1:3]),
            Match(left[10:12], right[15:17]),
            # subset needs to be extended
            Match(left[11:13], right[2:4]),
            Match(left[11:13], right[16:18]),
        ]
        results = extend_matches(matches, self.extend)
        # two different extended matches
        self.assertEqual(results, [
            Match(left[8:13], right[13:18]),
            Match(left[10:13], right[1:4])
        ])

    def test_mirror_submatches(self) -> None:
        """longer matches shouldn't generate internal mirrored submatches"""
        left = self.nlp.make_doc("邑與學吾交言而有信雖曰未學吾矣")
        right = self.nlp.make_doc("室與學吾交言而有信雖曰未學吾恐")
        left._.title = "left"
        right._.title = "right"
        matches = [
            Match(left[1:3], right[1:3]),
            Match(left[2:4], right[2:4]),
            # subset matches later subset
            Match(left[2:4], right[12:14]),
            Match(left[3:6], right[3:6]),
            Match(left[4:7], right[4:7]),
            Match(left[6:8], right[6:8]),
            Match(left[7:9], right[7:9]),
            Match(left[8:11], right[8:11]),
            Match(left[9:12], right[9:12]),
            Match(left[11:13], right[11:13]),
            # mirror of earlier subset
            Match(left[12:14], right[2:4]),
            Match(left[12:14], right[12:14]),
        ]
        results = extend_matches(matches, self.extend)
        # single match from chars 1-13, no internal matching
        self.assertEqual(results, [Match(left[1:14], right[1:14])])
