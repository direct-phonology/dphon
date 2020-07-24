"""Utility function unit tests."""

from unittest import TestCase

from dphon.tokenizer import Token
from dphon.util import has_graphic_variation, condense_matches
from dphon.document import Document
from dphon.graph import Match


class TestHasGraphicVariation(TestCase):

    def setUp(self) -> None:
        # create some basic docs to compare
        self.doc1 = Document(0, '恐出奔齊有二心矣')
        self.doc2 = Document(1, '公出奔齊有二心矣')
        self.doc3 = Document(2, '恐出奔齊有二心矣')

    def test_with_variation(self) -> None:
        tokens = [
            Token(0, self.doc1, 0, 3, '恐出奔齊'),
            Token(1, self.doc2, 0, 3, '公出奔齊'),
            Token(2, self.doc3, 0, 3, '恐出奔齊')
        ]
        # set the "original text" to current text (no transformation)
        for token in tokens:
            token.meta['orig_text'] = token.text
        # should show as having variation
        self.assertTrue(has_graphic_variation(tokens))

    def test_no_variation(self) -> None:
        tokens = [
            Token(0, self.doc1, 0, 3, '有二心矣'),
            Token(1, self.doc2, 0, 3, '有二心矣'),
            Token(2, self.doc3, 0, 3, '有二心矣')
        ]
        # set the "original text" to current text (no transformation)
        for token in tokens:
            token.meta['orig_text'] = token.text
        # no variation in this match
        self.assertFalse(has_graphic_variation(tokens))


class TestCondenseMatches(TestCase):

    def test_reduce_trigram_to_quad(self) -> None:
        """
        Two overlapping trigram matches should be condensed into a single
        quad-gram match.
        """
        matches = [
            Match(0, 1, slice(0, 2), slice(1, 3)),
            Match(0, 1, slice(1, 3), slice(2, 4))
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(0, 3), slice(1, 4))
        ])

    def test_different_match_lengths(self) -> None:
        """
        A long match that overlaps with a short match should be combined into
        a single match comprising the content of both matches.
        """
        matches = [
            Match(0, 1, slice(3, 17), slice(1, 15)),
            Match(0, 1, slice(16, 18), slice(14, 16))
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(3, 18), slice(1, 16))
        ])

    def test_multiple_overlap(self) -> None:
        """
        Sequences of consecutive overlapping matches should all be condensed
        into a single match.
        """
        matches = [
            Match(0, 1, slice(0, 2), slice(10, 12)),
            Match(0, 1, slice(1, 3), slice(11, 13)),
            Match(0, 1, slice(2, 4), slice(12, 14)),
            Match(0, 1, slice(3, 5), slice(13, 15)),
            Match(0, 1, slice(4, 6), slice(14, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37))  # unrelated
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(0, 6), slice(10, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37))  # unchanged
        ])

    def test_sub_overlap(self) -> None:
        """
        Sequences of consecutive overlapping matches with subsequences that
        also match elsewhere should be independently extended.
        """
        matches = [
            Match(0, 1, slice(8, 10), slice(13, 15)),
            Match(0, 1, slice(9, 11), slice(14, 16)),
            # subset matches elsewhere
            Match(0, 1, slice(10, 12), slice(1, 3)),
            Match(0, 1, slice(10, 12), slice(15, 17)),
            # subset needs to be extended
            Match(0, 1, slice(11, 13), slice(2, 4)),
            Match(0, 1, slice(11, 13), slice(16, 18)),
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(8, 13), slice(13, 18)),
            Match(0, 1, slice(10, 13), slice(1, 4))
        ])

    def test_mirror_submatches(self) -> None:
        """
        In matching sequences with repeated subsequences, we should get a
        large match covering the entirety of both sequences. We don't care
        about the internal matches between subsequences since they are
        subsumed in the larger sequence.
        """
        matches = [
            Match(0, 1, slice(1, 3), slice(1, 3)),
            Match(0, 1, slice(2, 4), slice(2, 4)),
            # subset matches later subset
            Match(0, 1, slice(2, 4), slice(12, 14)),
            Match(0, 1, slice(3, 6), slice(3, 6)),
            Match(0, 1, slice(4, 7), slice(4, 7)),
            Match(0, 1, slice(6, 8), slice(6, 8)),
            Match(0, 1, slice(7, 9), slice(7, 9)),
            Match(0, 1, slice(8, 11), slice(8, 11)),
            Match(0, 1, slice(9, 12), slice(9, 12)),
            Match(0, 1, slice(11, 13), slice(11, 13)),
            # mirror of earlier subset
            Match(0, 1, slice(12, 14), slice(2, 4)),
            Match(0, 1, slice(12, 14), slice(12, 14)),
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(1, 14), slice(1, 14))
        ])
