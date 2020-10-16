# -*- coding: utf-8 -*-
"""Aligner unit tests."""

from unittest import TestCase, skip

from dphon.aligner import NeedlemanWunschAligner


@skip("fixme")
class TestNeedlemanWunschAligner(TestCase):
    """Test the NeedlemanWunschAligner."""

    maxDiff = None   # don't limit length of diff output for failures

    def test_no_spacing(self) -> None:
        """Prealigned matches should be unchanged.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""
        # create mock matches, documents, and aligner
        source = '千室之邑百乘之家'
        target = '千室之邑百乘之家'
        aligner = NeedlemanWunschAligner()
        (aligned_source, aligned_target) = aligner.align(source, target)
        # alignment should be identical
        self.assertEqual(aligned_source, source)
        self.assertEqual(aligned_target, target)

    def test_trim(self) -> None:
        """Matches with a trailing portion that doesn't match should be trimmed.

        Text source:
        - https://ctext.org/text.pl?node=370528&if=en&filter=497427"""
        # create mock matches, documents, and aligner
        source = '子如鄉黨恂恂如也似不能言者'
        target = '子於鄉黨恂恂如也父母之國'
        aligner = NeedlemanWunschAligner()
        (aligned_source, aligned_target) = aligner.align(source, target)
        # alignment should include only matching portion
        self.assertEqual(aligned_source, '子如鄉黨恂恂如也')
        self.assertEqual(aligned_target, '子於鄉黨恂恂如也')

    def test_spacing(self) -> None:
        """Matches with deletions should be padded so that lengths align.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""
        # create mock matches, documents, and aligner
        source = ('由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千室之邑百乘之家可使為之'
                  '宰也不知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也')
        target = ('由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之宰赤也束帶立於朝可使與'
                  '賓客言也又曰子謂子產有君子之道四焉其行己也恭其事上也敬')
        aligner = NeedlemanWunschAligner()
        (aligned_source, aligned_target) = aligner.align(source, target)
        # first string shouldn't change when aligned
        self.assertEqual(aligned_source, source)
        # alignment should space out second string to match first
        self.assertEqual(aligned_target, (
            '由也千乘之國可使治其賦也　　　　　　　　　　　求也千室之邑百乘之家'
            '可使為之宰　　　　　　　　　　　　赤也束帶立於朝可使與賓客言也'
        ))
