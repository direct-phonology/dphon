"""Extender unit tests."""

from unittest import TestCase

import spacy

from dphon.extend import LevenshteinExtender, extend_matches
from dphon.match import Match


class TestLevenshteinExtender(TestCase):
    """Test the LevenshteinExtender."""

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
        u = self.nlp.make_doc("千室之邑百乘之家")
        v = self.nlp.make_doc("千室之邑百乘之家")

        # create a match and extend it
        match = Match("analects", "shiji", u[0:8], v[0:8])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extended = extend(match)

        # shouldn't be extended
        self.assertEqual(extended.utxt, match.utxt)
        self.assertEqual(extended.vtxt, match.vtxt)

        # perfect score
        self.assertEqual(extended.weight, 1.0)

    def test_perfect_match(self) -> None:
        """matches should be extended as far as possible

        Text sources:
        - https://ctext.org/text.pl?node=416724&if=en&filter=463451
        - https://ctext.org/text.pl?node=542654&if=en&filter=463451"""

        # create mock documents
        u = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        v = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")

        # create a match and extend it
        match = Match("qunshu", "yiwen", u[4:8], v[4:8])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extended = extend(match)

        # should be fully extended in both directions
        self.assertEqual(extended.utxt, u[0:18])
        self.assertEqual(extended.vtxt, v[0:18])

        # perfect score
        self.assertEqual(extended.weight, 1.0)

    def test_cutoff(self) -> None:
        """matches should end when similarity drops below threshold

        Text sources:
        - https://ctext.org/analects/xue-er?filter=538878
        - https://ctext.org/lunheng/cheng-cai?filter=538878"""

        # create mock documents
        u = self.nlp.make_doc("行有餘力則以學文")
        v = self.nlp.make_doc("行有餘力博學覽古")

        # create a match and extend it
        match = Match("analects", "lunheng", u[0:2], v[0:2])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extended = extend(match)

        # should only extend over similar region
        self.assertEqual(extended.utxt, u[0:4])
        self.assertEqual(extended.vtxt, v[0:4])

    def test_short_cutoff(self) -> None:
        """matches should be fully trimmed back to final high-similarity point

        Text sources:
        - https://ctext.org/analects/xue-er?filter=538878
        - https://ctext.org/lunheng/cheng-cai?filter=538878"""

        # create mock documents
        u = self.nlp.make_doc("行有餘力則")
        v = self.nlp.make_doc("行有餘力博")

        # create a match and extend it
        match = Match("analects", "lunheng", u[0:2], v[0:2])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extended = extend(match)

        # should only extend over similar region
        self.assertEqual(extended.utxt, u[0:4])
        self.assertEqual(extended.vtxt, v[0:4])

    def test_fuzzy_match(self) -> None:
        """matches should extend as long as they're above the threshold

        Text sources:
        - https://ctext.org/analects/xue-er?filter=449401
        - https://ctext.org/text.pl?node=416724&if=en&filter=449401"""

        # create mock documents
        u = self.nlp.make_doc("子曰弟子入則孝出則弟謹而信汎愛眾而親仁行有餘力則以學文")
        v = self.nlp.make_doc("子曰弟子入則孝出則悌謹而信泛愛衆而親仁行有餘力則以學文")

        # create a match and extend it
        match = Match("analects", "qunshu", u[0:4], v[0:4])
        extend = LevenshteinExtender(threshold=0.75, len_limit=100)
        extended = extend(match)

        # should extend all the way, despite mismatches in the middle
        self.assertEqual(extended.utxt, u[0:27])
        self.assertEqual(extended.vtxt, v[0:27])

    def test_long_match(self) -> None:
        """long matches should capture the entirety of the match in both docs

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""

        # create mock documents
        u = self.nlp.make_doc((
            "由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千室之邑百乘之家可使為之宰也不"
            "知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也"))
        v = self.nlp.make_doc((
            "由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之宰赤也束帶立於朝可使與賓客言"
            "也又曰子謂子產有君子之道四焉其行己也恭其事上也敬"))

        # create a match and extend it; lower threshold and len_limit
        match = Match("analects", "taipingyulan", u[0:4], v[0:4])
        extend = LevenshteinExtender(threshold=0.5, len_limit=50)
        extended = extend(match)

        # Note that we'll capture a lot of garbage at the end of v here; in
        # practice an aligner will resolve that by spacing out the text. We need
        # to extend to the full length of the match in u.
        self.assertEqual(extended.utxt, u[0:64])
        self.assertEqual(extended.vtxt, v[0:64])


class TestExtendMatches(TestCase):
    """Test extending match lists."""

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
        u = self.nlp.make_doc("千室之邑百乘之家")
        v = self.nlp.make_doc("千室之邑百乘之家")

        # create matches and extend them
        matches = [Match("analects", "shiji", u[0:8], v[0:8], 1.0)]

        # output should be identical to input
        results = extend_matches(matches, self.extend)
        self.assertEqual(results, matches)

    def test_perfect_match(self) -> None:
        """matches should be extended as far as possible

        Text sources:
        - https://ctext.org/text.pl?node=416724&if=en&filter=463451
        - https://ctext.org/text.pl?node=542654&if=en&filter=463451"""

        # create mock documents
        u = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        v = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")

        # create matches and extend them
        matches = [
            Match("analects", "yiwen-leiju", u[0:4], v[0:4]),
            Match("analects", "yiwen-leiju", u[1:5], v[1:5])
        ]
        results = extend_matches(matches, self.extend)

        # first match is kept and extended; second is discarded as internal
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].utxt, u[0:18])
        self.assertEqual(results[0].vtxt, v[0:18])

    def test_sub_overlap(self) -> None:
        """consecutive overlapping matches should be independently extended"""
        # create mock documents
        u = self.nlp.make_doc("水善利萬物而不爭自見者不明弊則新無關")
        v = self.nlp.make_doc("可者不明下母得已以百姓為芻自見者不明")

        # create matches and extend them
        matches = [
            Match("u", "v", u[8:10], v[13:15]),
            Match("u", "v", u[9:11], v[14:16]),
            Match("u", "v", u[10:12], v[1:3]),   # matches twice in v
            Match("u", "v", u[10:12], v[15:17]),
            Match("u", "v", u[11:13], v[2:4]),   # both should be extended
            Match("u", "v", u[11:13], v[16:18]),
        ]
        results = extend_matches(matches, self.extend)

        # should have two different extended matches
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].utxt, u[8:13])
        self.assertEqual(results[0].vtxt, v[13:18])
        self.assertEqual(results[1].utxt, u[10:13])
        self.assertEqual(results[1].vtxt, v[1:4])

    def test_mirror_submatches(self) -> None:
        """longer matches shouldn't generate internal mirrored submatches"""
        # create mock documents
        u = self.nlp.make_doc("邑與學吾交言而有信雖曰未學吾矣")
        v = self.nlp.make_doc("室與學吾交言而有信雖曰未學吾恐")

        # create matches and extend them
        matches = [
            Match("u", "v", u[1:3], v[1:3]),
            Match("u", "v", u[2:4], v[2:4]),
            Match("u", "v", u[2:4], v[12:14]),       # matches twice in v
            Match("u", "v", u[3:6], v[3:6]),
            Match("u", "v", u[4:7], v[4:7]),
            Match("u", "v", u[6:8], v[6:8]),
            Match("u", "v", u[7:9], v[7:9]),
            Match("u", "v", u[8:11], v[8:11]),
            Match("u", "v", u[9:12], v[9:12]),
            Match("u", "v", u[11:13], v[11:13]),
            Match("u", "v", u[12:14], v[2:4]),      # reverse of earlier match
            Match("u", "v", u[12:14], v[12:14]),
        ]
        results = extend_matches(matches, self.extend)

        # single match from chars 1-13, no internal matching
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].utxt, u[1:14])
        self.assertEqual(results[0].vtxt, v[1:14])

    def test_dedup(self) -> None:
        """output shouldn't include duplicate matches"""
        # create mock documents
        u = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將闐之以無名之樸")
        v = self.nlp.make_doc("侯王若能守之萬物將自化化而欲作吾將鎮之以無名之樸")

        # create matches and extend them
        matches = [
            Match("mwd_laozi", "laozi", u[3:6], v[3:6]),
            Match("mwd_laozi", "laozi", u[12:15], v[12:15]),
            Match("mwd_laozi", "laozi", u[20:23], v[20:23])
        ]
        results = extend_matches(matches, self.extend)

        # single match spanning entire doc
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].utxt, u[:])
        self.assertEqual(results[0].vtxt, v[:])

    def test_aggregation(self) -> None:
        """many consecutive small matches should be aggregated"""
        # create mock documents
        u = self.nlp.make_doc(("視素保樸，少私寡欲。江海所以為百谷王，以其能為百谷下，"
                               "是以能為百谷王。聖人之在民前也，以身後之；其在民上也，"
                               "以言下之。"))
        v = self.nlp.make_doc(("與物反矣，然後乃至大順江海所以能為百谷王者，以其善下之，"
                               "故能為百谷王。是以聖人欲上民，必以言下之；欲先民，必以身"
                               "後之。"))

        # several 3-4 matching character spans, spaced out relatively evenly
        # with low enough threshold to extend between matches
        matches = [
            Match("gd_laozi", "laozi", u[10:14], v[11:15]),
            Match("gd_laozi", "laozi", u[15:18], v[17:20]),
            Match("gd_laozi", "laozi", u[15:18], v[31:34]),
            Match("gd_laozi", "laozi", u[31:34], v[17:20]),
            Match("gd_laozi", "laozi", u[31:34], v[31:34]),
        ]
        self.extend = LevenshteinExtender(threshold=0.6, len_limit=100)
        results = extend_matches(matches, self.extend)

        # should all be combined
        self.assertEqual(len(results), 1)
