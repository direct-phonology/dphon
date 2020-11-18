# -*- coding: utf-8 -*-
"""Aligner unit tests."""

from unittest import TestCase
from unittest.mock import MagicMock

from lingpy.align.pairwise import _get_scorer
from dphon.aligner import SmithWatermanAligner, SmithWatermanPhoneticAligner


class TestSmithWatermanAligner(TestCase):
    """Test the SmithWatermanAligner."""
    maxDiff = None   # don't limit length of diff output for failures

    def setUp(self) -> None:
        """Create an aligner for use in testing."""
        # allow the aligner to create default matching matrix
        self.aligner = SmithWatermanAligner()

    def test_no_spacing(self) -> None:
        """Prealigned matches should be unchanged.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""

        # create a mock match and align it
        match = MagicMock()
        left = "千室之邑百乘之家"
        right = "千室之邑百乘之家"
        match.left.text = left
        match.right.text = right

        # alignment should be identical
        aligned_left, aligned_right, _score = self.aligner.align(match)
        self.assertEqual(aligned_left, left)
        self.assertEqual(aligned_right, right)

    def test_trim(self) -> None:
        """Matches with a trailing portion that doesn't match should be trimmed.

        Text sources:
        - https://ctext.org/text.pl?node=370528&if=en&filter=497427"""

        # create a mock match and align it
        match = MagicMock()
        left = "子如鄉黨恂恂如也似不能言者"
        right = "子於鄉黨恂恂如也父母之國"
        match.left.text = left
        match.right.text = right
        aligned_left, aligned_right, _score = self.aligner.align(match)

        # alignment should include only matching portion
        self.assertEqual(aligned_left, "子如鄉黨恂恂如也")
        self.assertEqual(aligned_right, "子於鄉黨恂恂如也")

    def test_spacing(self) -> None:
        """Matches with deletions should be padded so that lengths align.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""

        # create a mock match and align it
        match = MagicMock()
        left = ("由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千室之邑百乘之家可使為之"
                "宰也不知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也")
        right = ("由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之宰赤也束帶立於朝可使與"
                 "賓客言也又曰子謂子產有君子之道四焉其行己也恭其事上也敬")
        match.left.text = left
        match.right.text = right
        aligned_left, aligned_right, _score = self.aligner.align(match)

        # first string shouldn't change when aligned
        self.assertEqual(aligned_left, left)
        # alignment should space out second string to match first
        # note that this isn't the ideal alignment for us, but it is considered
        # an optimal alignment by the algorithm
        self.assertEqual(aligned_right, (
            "由也千乘之國可使治其賦　　　　　　　也　　　　求也千室之邑百乘之家"
            "可使為之宰　　　　　　　　　　　　赤也束帶立於朝可使與賓客言也"
        ))


class TestSmithWatermanPhoneticAligner(TestCase):
    """Test the SmithWatermanPhoneticAligner."""
    maxDiff = None

    def setUp(self) -> None:
        """Create an aligner for use in testing."""
        # special scoring matrix for testing where B == A
        scorer = _get_scorer("ABC", "ABC")
        scorer[("A", "B")] = scorer[("B", "A")] = 1.0
        self.aligner = SmithWatermanPhoneticAligner(scorer=scorer)

    def test_spacing(self) -> None:
        """scoring matrix should affect alignment"""
        match = MagicMock()
        match.left.text = "AACABACABACABACC"
        match.right.text = "CCCBBBCBBBCBBBAA"
        aligned_left, aligned_right, score = self.aligner.align(match)
        # central part is aligned exactly
        self.assertEqual((aligned_left, aligned_right), (
            "CABACABACABA",
            "CBBBCBBBCBBB"
        ))
        # perfect score (1.0 × 12)
        self.assertEqual(score, 12.0)