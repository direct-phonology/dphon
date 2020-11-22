# -*- coding: utf-8 -*-
"""Aligner unit tests."""

from unittest import TestCase

import spacy
from dphon.align import SmithWatermanAligner
from dphon.match import Match
from lingpy.align.pairwise import _get_scorer


class TestSmithWatermanAligner(TestCase):
    """Test the SmithWatermanAligner."""
    maxDiff = None   # don't limit length of diff output for failures

    def setUp(self) -> None:
        """Create a spaCy pipeline and aligner for use in testing."""
        # blank chinese pipeline
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
        # allow the aligner to create default matching matrix
        self.align = SmithWatermanAligner()

    def test_no_spacing(self) -> None:
        """Prealigned matches should be unchanged.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""

        # create docs and a match
        left = self.nlp.make_doc("千室之邑百乘之家")
        right = self.nlp.make_doc("千室之邑百乘之家")
        match = Match(left=left[:], right=right[:])

        # alignment should be identical
        aligned_left, aligned_right = self.align(match).alignment
        self.assertEqual(aligned_left, left.text)
        self.assertEqual(aligned_right, right.text)

    def test_trim(self) -> None:
        """Matches with a trailing portion that doesn't match should be trimmed.

        Text sources:
        - https://ctext.org/text.pl?node=370528&if=en&filter=497427"""

        # create docs and a match
        left = self.nlp.make_doc("子如鄉黨恂恂如也似不能言者")
        right = self.nlp.make_doc("子於鄉黨恂恂如也父母之國")
        match = Match(left=left[:], right=right[:])

        # alignment should include only matching portion
        aligned_left, aligned_right = self.align(match).alignment
        self.assertEqual(aligned_left, "子如鄉黨恂恂如也")
        self.assertEqual(aligned_right, "子於鄉黨恂恂如也")

    def test_spacing(self) -> None:
        """Matches with deletions should be padded so that lengths align.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""

        # create a mock match and align it
        left = self.nlp.make_doc(("由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千"
                                  "室之邑百乘之家可使為之宰也不知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也"))
        right = self.nlp.make_doc(("由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之"
                                   "宰赤也束帶立於朝可使與賓客言也又曰子謂子產有君子之道四焉其行己也恭其事上也敬"))
        match = Match(left=left[:], right=right[:])

        # first string shouldn't change when aligned
        aligned_left, aligned_right = self.align(match).alignment
        self.assertEqual(aligned_left, left.text)
        # alignment should space out second string to match first
        # note that this isn't the ideal alignment for us, but it is considered
        # an optimal alignment by the algorithm
        self.assertEqual(aligned_right, (
            "由也千乘之國可使治其賦-------也----求也千室之邑百乘之家"
            "可使為之宰------------赤也束帶立於朝可使與賓客言也"
        ))

    def test_scorer(self) -> None:
        """scoring matrix should affect alignment"""
        # special scoring matrix for testing where B == A
        scorer = _get_scorer("ABC", "ABC")
        scorer[("A", "B")] = scorer[("B", "A")] = 1.0
        self.align = SmithWatermanAligner(scorer=scorer)

        # create match and align it
        left = self.nlp.make_doc("AACABACABACABACC")
        right = self.nlp.make_doc("CCCBBBCBBBCBBBAA")
        match = Match(left=left[:], right=right[:])

        # central part is aligned exactly
        result = self.align(match)
        aligned_left, aligned_right = result.alignment
        self.assertEqual((aligned_left, aligned_right), (
            "CABACABACABA",
            "CBBBCBBBCBBB"
        ))
        # perfect score (1.0 × 12)
        self.assertEqual(result.score, 12.0)
