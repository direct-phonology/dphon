"""Extender unit tests."""

from unittest import TestCase
from unittest.mock import Mock

from dphon.graph import Match
from dphon.loader import SimpleLoader
from dphon.extender import LevenshteinPhoneticExtender
from dphon.document import Document


class TestLevenshteinPhoneticExtender(TestCase):
    """Test the LevenshteinPhoneticExtender."""

    def test_no_extension(self) -> None:
        """Matches that can't be extended any further should be unchanged.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=503848
        - https://ctext.org/shiji/zhong-ni-di-zi-lie-zhuan?filter=503848"""
        # create mock documents
        docs = [
            Document(0, '千室之邑百乘之家'),
            Document(1, '千室之邑百乘之家')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # shouldn't be extended
        self.assertEqual(extender.extend(match), match)

    def test_perfect_match(self) -> None:
        """Matches should be extended as far as possible.

        Text sources:
        - https://ctext.org/text.pl?node=416724&if=en&filter=463451
        - https://ctext.org/text.pl?node=542654&if=en&filter=463451"""
        # create mock documents
        docs = [
            Document(0, '與朋友交言而有信雖曰未學吾必謂之學矣'),
            Document(1, '與朋友交言而有信雖曰未學吾必謂之學矣')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # should be fully extended
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 18), slice(0, 18)))

    def test_trail(self) -> None:
        """Most matches shouldn't include a 'trail' of non-matching characters.

        Text sources:
        - https://ctext.org/analects/xue-er?filter=538878
        - https://ctext.org/lunheng/cheng-cai?filter=538878"""
        # create mock documents
        docs = [
            Document(0, '行有餘力則以學文'),
            Document(1, '行有餘力博學覽古')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 2), slice(0, 2))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # should extend to match boundary, but not further into text
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 4), slice(0, 4)))

    def test_fuzzy_match(self) -> None:
        """Matches should extend as long as they're above the threshold.

        Text sources:
        - https://ctext.org/analects/xue-er?filter=449401
        - https://ctext.org/text.pl?node=416724&if=en&filter=449401"""
        # create mock documents
        docs = [
            Document(0, '子曰弟子入則孝出則弟謹而信汎愛眾而親仁行有餘力則以學文'),
            Document(1, '子曰弟子入則孝出則悌謹而信泛愛衆而親仁行有餘力則以學文')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # should cover entire document, including mismatches
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 27), slice(0, 27)))

    def test_long_match(self) -> None:
        """Long matches should capture the entirety of the match in both docs.

        Note that we'll capture a lot of garbage at the end of doc 1 here; in
        practice an aligner will resolve that by spacing out the text. We need
        to extend to the full length of the match in doc 0.

        Text sources:
        - https://ctext.org/analects/gong-ye-chang?filter=430524
        - https://ctext.org/text.pl?node=384985&if=en&filter=430524"""
        # create mock documents
        docs = [
            Document(0, '''由也千乘之國可使治其賦也不知其仁也求也何如子曰求也千室之邑百乘'''
                     '''之家可使為之宰也不知其仁也赤也何如子曰赤也束帶立於朝可使與賓客言也'''),
            Document(1, '''由也千乘之國可使治其賦也求也千室之邑百乘之家可使為之宰赤也束帶'''
                     '''立於朝可使與賓客言也又曰子謂子產有君子之道四焉其行己也恭其事上也敬''')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it - set a low threshold and len_limit
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.5, 50)
        # should cover entire document, including middle section
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 64), slice(0, 64)))
