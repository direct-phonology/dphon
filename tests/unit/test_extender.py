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
        # create mock documents
        docs = [
            Document(0, '中士聞道若存若'),
            Document(1, '中士聞道天下正')
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
        # create mock documents
        docs = [
            Document(0, '中士聞道若存若'),
            Document(1, '中士聞道若存若')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # should be fully extended
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 7), slice(0, 7)))

    def test_trail(self) -> None:
        # create mock documents
        docs = [
            Document(0, '中士聞道若存若夫物芸芸各復歸其根'),
            Document(1, '中士聞道若存若盜賊無有此三者以為')
        ]
        corpus = Mock(SimpleLoader)
        corpus.get.side_effect = docs
        # create a match and extend it
        match = Match(0, 1, slice(0, 4), slice(0, 4))
        extender = LevenshteinPhoneticExtender(
            corpus, 'data/dummy_dict.json', 0.75, 100)
        # should extend to match boundary, but not further into text
        self.assertEqual(extender.extend(match), Match(
            0, 1, slice(0, 7), slice(0, 7)))
