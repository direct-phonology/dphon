"""Utility function unit tests."""

from unittest import TestCase, skip

import spacy
from spacy.tokens import Doc

from dphon.extend import LevenshteinExtender
from dphon.reuse import Match
from dphon.util import extend_matches, group_by_doc, is_norm_eq, condense_matches


class TestCondenseMatches(TestCase):
    """Test condensing match lists."""

    @ classmethod
    def setUpClass(cls) -> None:
        """Register the title attribute on Docs."""
        Doc.set_extension("title", default="")

    @ classmethod
    def tearDownClass(cls) -> None:
        """Unregister the title attribute on Docs."""
        Doc.remove_extension("title")

    def setUp(self) -> None:
        """Create a blank spaCy model to test with."""
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})

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
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[0:18])
        self.assertEqual(results[0].right, right[0:18])

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
        self.assertEqual(len(results), 2)
        self.assertEqual((results[0].left, results[0].right),
                         (left[8:13], right[13:18]))
        self.assertEqual((results[1].left, results[1].right),
                         (left[10:13], right[1:4]))

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
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[1:14])
        self.assertEqual(results[0].right, right[1:14])

    def test_dedup(self) -> None:
        """output shouldn't include duplicate matches"""
        left = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將闐之以無名之樸")
        right = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將鎮之以無名之樸")
        left._.title = "mwd_laozi"
        right._.title = "laozi"
        matches = [
            # three sub-pairs of one long match
            Match(left[3:6], right[3:6]),
            Match(left[12:15], right[12:15]),
            Match(left[20:23], right[20:23])
        ]
        results = extend_matches(matches, self.extend)
        # single match spanning entire doc
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[:])
        self.assertEqual(results[0].right, right[:])
        # the first match from the list was kept; the rest were discarded
        self.assertEqual(id(results[0]), id(matches[0]))

    def test_aggregation(self) -> None:
        """many consecutive small matches should be aggregated"""
        # create testing docs
        left = self.nlp.make_doc(
            "視素保樸，少私寡欲。江海所以為百谷王，以其能為百谷下，是以能為百谷王。聖人之在民前也，以身後之；其在民上也，以言下之。")
        right = self.nlp.make_doc(
            "與物反矣，然後乃至大順江海所以能為百谷王者，以其善下之，故能為百谷王。是以聖人欲上民，必以言下之；欲先民，必以身後之。")
        left._.title = "gd_laozi"
        right._.title = "laozi"
        # several 3-4 matching character spans, spaced out relatively evenly
        matches = [
            Match(left[10:14], right[11:15]),
            Match(left[15:18], right[17:20]),
            Match(left[15:18], right[31:34]),
            Match(left[31:34], right[17:20]),
            Match(left[31:34], right[31:34]),
        ]
        # low enough threshold to extend between matches
        self.extend = LevenshteinExtender(threshold=0.6, len_limit=100)
        results = extend_matches(matches, self.extend)
        self.assertEqual(len(results), 1)


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
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[0:18])
        self.assertEqual(results[0].right, right[0:18])

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
        self.assertEqual(len(results), 2)
        self.assertEqual((results[0].left, results[0].right),
                         (left[8:13], right[13:18]))
        self.assertEqual((results[1].left, results[1].right),
                         (left[10:13], right[1:4]))

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
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[1:14])
        self.assertEqual(results[0].right, right[1:14])

    def test_dedup(self) -> None:
        """output shouldn't include duplicate matches"""
        left = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將闐之以無名之樸")
        right = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將鎮之以無名之樸")
        left._.title = "mwd_laozi"
        right._.title = "laozi"
        matches = [
            # three sub-pairs of one long match
            Match(left[3:6], right[3:6]),
            Match(left[12:15], right[12:15]),
            Match(left[20:23], right[20:23])
        ]
        results = extend_matches(matches, self.extend)
        # single match spanning entire doc
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].left, left[:])
        self.assertEqual(results[0].right, right[:])
        # the first match from the list was kept; the rest were discarded
        self.assertEqual(id(results[0]), id(matches[0]))

    def test_aggregation(self) -> None:
        """many consecutive small matches should be aggregated"""
        # create testing docs
        left = self.nlp.make_doc(
            "視素保樸，少私寡欲。江海所以為百谷王，以其能為百谷下，是以能為百谷王。聖人之在民前也，以身後之；其在民上也，以言下之。")
        right = self.nlp.make_doc(
            "與物反矣，然後乃至大順江海所以能為百谷王者，以其善下之，故能為百谷王。是以聖人欲上民，必以言下之；欲先民，必以身後之。")
        left._.title = "gd_laozi"
        right._.title = "laozi"
        # several 3-4 matching character spans, spaced out relatively evenly
        matches = [
            Match(left[10:14], right[11:15]),
            Match(left[15:18], right[17:20]),
            Match(left[15:18], right[31:34]),
            Match(left[31:34], right[17:20]),
            Match(left[31:34], right[31:34]),
        ]
        # low enough threshold to extend between matches
        self.extend = LevenshteinExtender(threshold=0.6, len_limit=100)
        results = extend_matches(matches, self.extend)
        self.assertEqual(len(results), 1)
