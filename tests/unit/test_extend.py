"""Extender unit tests."""

from unittest import TestCase

import spacy

from dphon.extend import LevenshteinExtender
from dphon.reuse import Match


class TestLevenshteinExtender(TestCase):
    """Test the LevenshteinExtender."""

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
        # create a match and extend it
        match = Match(left[0:8], right[0:8])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        # shouldn't be extended
        self.assertEqual(extend(match), match)
        # perfect score
        self.assertEqual(match.score, 1.0)

    def test_perfect_match(self) -> None:
        """matches should be extended as far as possible

        Text sources:
        - https://ctext.org/text.pl?node=416724&if=en&filter=463451
        - https://ctext.org/text.pl?node=542654&if=en&filter=463451"""

        # create mock documents
        left = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        right = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        # create a match and extend it
        match = Match(left[4:8], right[4:8])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extend(match)
        # should be fully extended in both directions
        self.assertEqual(match.left, left[0:18])
        self.assertEqual(match.right, right[0:18])
        # perfect score
        self.assertEqual(match.score, 1.0)

    def test_cutoff(self) -> None:
        """matches should end when similarity drops below threshold

        Text sources:
        - https://ctext.org/analects/xue-er?filter=538878
        - https://ctext.org/lunheng/cheng-cai?filter=538878"""

        # create mock documents
        left = self.nlp.make_doc("行有餘力則以學文")
        right = self.nlp.make_doc("行有餘力博學覽古")
        # create a match and extend it
        match = Match(left[0:2], right[0:2])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extend(match)
        # should only extend over similar region
        self.assertEqual(match.left, left[0:4])
        self.assertEqual(match.right, right[0:4])

    def test_short_cutoff(self) -> None:
        """matches should be fully trimmed back to final high-similarity point

        Text sources:
        - https://ctext.org/analects/xue-er?filter=538878
        - https://ctext.org/lunheng/cheng-cai?filter=538878"""

        # create mock documents
        left = self.nlp.make_doc("行有餘力則")
        right = self.nlp.make_doc("行有餘力博")
        # create a match and extend it
        match = Match(left[0:2], right[0:2])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extend(match)
        # should only extend over similar region
        self.assertEqual(match.left, left[0:4])
        self.assertEqual(match.right, right[0:4])

    def test_fuzzy_match(self) -> None:
        """matches should extend as long as they're above the threshold

        Text sources:
        - https://ctext.org/analects/xue-er?filter=449401
        - https://ctext.org/text.pl?node=416724&if=en&filter=449401"""

        # create mock documents
        left = self.nlp.make_doc("子曰弟子入則孝出則弟謹而信汎愛眾而親仁行有餘力則以學文")
        right = self.nlp.make_doc("子曰弟子入則孝出則悌謹而信泛愛衆而親仁行有餘力則以學文")
        # create a match and extend it
        match = Match(left[0:4], right[0:4])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extend(match)
        # should extend all the way, despite mismatches in the middle
        self.assertEqual(match.left, left[0:27])
        self.assertEqual(match.right, right[0:27])

    def test_long_match(self) -> None:
        """long matches should capture the entirety of the match in both docs

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""

        # create mock documents
        left = self.nlp.make_doc((
            "由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千室之邑百乘之家可使為之宰也不"
            "知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也"))
        right = self.nlp.make_doc((
            "由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之宰赤也束帶立於朝可使與賓客言"
            "也又曰子謂子產有君子之道四焉其行己也恭其事上也敬"))
        # create a match and extend it; lower threshold and len_limit
        match = Match(left[0:4], right[0:4])
        extend = LevenshteinExtender(threshold=0.5, len_limit=50)
        extend(match)
        # Note that we'll capture a lot of garbage at the end of doc 1 here; in
        # practice an aligner will resolve that by spacing out the text. We need
        # to extend to the full length of the match in doc 0.
        self.assertEqual(match.left, left[0:64])
        self.assertEqual(match.right, right[0:64])
