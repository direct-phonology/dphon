"""Aligner unit tests."""

from unittest import TestCase

from dphon.aligner import NeedlemanWunschPhoneticAligner


class TestNeedlemanWunschPhoneticAligner(TestCase):
    """Test the NeedlemanWunschPhoneticAligner."""

    def test_no_spacing(self) -> None:
        """Prealigned matches should be unchanged.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""
        # create mock matches, documents, and aligner
        match = (
            '千室之邑百乘之家',
            '千室之邑百乘之家'
        )
        aligner = NeedlemanWunschPhoneticAligner('data/dummy_dict.json')
        # alignment should be identical
        self.assertEqual(aligner.align(*match), match)

    def test_trim(self) -> None:
        """Matches with a trailing portion that doesn't match should be trimmed.

        Text source:
        - https://ctext.org/text.pl?node=370528&if=en&filter=497427"""
        # create mock matches, documents, and aligner
        match = (
            '子如鄉黨恂恂如也似不能言者',
            '子於鄉黨恂恂如也父母之國'
        )
        aligner = NeedlemanWunschPhoneticAligner('data/dummy_dict.json')
        # alignment should include only matching portion
        self.assertEqual(aligner.align(*match), (
            '子如鄉黨恂恂如也',
            '子於鄉黨恂恂如也'
        ))
