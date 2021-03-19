# -*- coding: utf-8 -*-
"""Aligner unit tests."""

from unittest import TestCase

import spacy
from dphon.match import Match
from dphon.align import SmithWatermanAligner
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
        u = self.nlp.make_doc("千室之邑百乘之家")
        v = self.nlp.make_doc("千室之邑百乘之家")
        match = Match("analects", "shiji", u[:], v[:])

        # alignment should be identical with perfect score
        aligned = self.align(match)
        self.assertEqual(aligned.au, list(u.text))
        self.assertEqual(aligned.av, list(v.text))
        self.assertEqual(aligned.weight, 1.0)

    def test_trim(self) -> None:
        """Matches with a trailing portion that doesn't match should be trimmed.

        Text sources:
        - https://ctext.org/text.pl?node=370528&if=en&filter=497427"""

        # create docs and a match
        u = self.nlp.make_doc("子如鄉黨恂恂如也似不能言者")
        v = self.nlp.make_doc("子於鄉黨恂恂如也父母之國")
        match = Match("taipingyulan", "taipingyulan", u[:], v[:])

        # alignment should include only matching portion
        aligned = self.align(match)
        self.assertEqual(aligned.au, list("子如鄉黨恂恂如也"))
        self.assertEqual(aligned.av, list("子於鄉黨恂恂如也"))

    def test_trim_punct(self) -> None:
        """Leading or trailing non-alphanumeric content should be trimmed."""

        # create docs and a match
        u = self.nlp.make_doc("，子如鄉黨恂恂如也。似不能言者")
        v = self.nlp.make_doc("，子於鄉黨恂恂如也。父母之國")
        match = Match("taipingyulan", "taipingyulan", u[:], v[:])

        # alignment should include only matching portion, no punctuation
        aligned = self.align(match)
        self.assertEqual(aligned.au, list("子如鄉黨恂恂如也"))
        self.assertEqual(aligned.av, list("子於鄉黨恂恂如也"))


    def test_spacing(self) -> None:
        """Matches with deletions should be padded so that lengths align.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""

        # create a mock match and align it
        u = self.nlp.make_doc(("由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千"
                               "室之邑百乘之家可使為之宰也不知其仁也赤也何如子曰赤也"
                               "束帶立於朝可使與賓客言也"))
        v = self.nlp.make_doc(("由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之"
                               "宰赤也束帶立於朝可使與賓客言也又曰子謂子產有君子之道"
                               "四焉其行己也恭其事上也敬"))
        match = Match("analects", "taipingyulan", u[:], v[:])

        # first string shouldn't change when aligned
        aligned = self.align(match)
        self.assertEqual(aligned.au, list(u.text))

        # alignment should space out second string to match first
        # note that this isn't the ideal alignment for us, but it is considered
        # an optimal alignment by the algorithm
        self.assertEqual(aligned.av, list((
            "由也千乘之國可使治其賦-------也----求也千室之邑百乘之家"
            "可使為之宰------------赤也束帶立於朝可使與賓客言也"
        )))

    def test_scorer(self) -> None:
        """scoring matrix should affect alignment"""
        # special scoring matrix for testing where B == A
        scorer = _get_scorer("ABC", "ABC")
        scorer[("A", "B")] = scorer[("B", "A")] = 1.0
        self.align = SmithWatermanAligner(scorer=scorer)

        # create match and align it
        u = self.nlp.make_doc("AACABACABACABACC")
        v = self.nlp.make_doc("CCCBBBCBBBCBBBAA")
        match = Match("u", "v", u[:], v[:])

        # central part is aligned exactly; perfect score
        aligned = self.align(match)
        self.assertEqual(aligned.au, list("CABACABACABA"))
        self.assertEqual(aligned.av, list("CBBBCBBBCBBB"))
        self.assertEqual(aligned.weight, 1.0)
