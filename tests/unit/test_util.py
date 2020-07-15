"""
Utility function tests
"""


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
        Two overlapping trigram Matches should be condensed into a single
        quad-gram Match.
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
        a single Match comprising the content of both Matches.
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
        Sequences of consecutive overlapping Matches should all be condensed
        into a single Match.
        """
        matches = [
            Match(0, 1, slice(0, 2), slice(10, 12)),
            Match(0, 1, slice(1, 3), slice(11, 13)),
            Match(0, 1, slice(2, 4), slice(12, 14)),
            Match(0, 1, slice(3, 5), slice(13, 15)),
            Match(0, 1, slice(4, 6), slice(14, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37)) # unrelated
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(0, 6), slice(10, 16)),
            Match(0, 1, slice(23, 27), slice(33, 37)) # unchanged
        ])

    def test_sub_overlap(self) -> None:
        """
        Sequences of consecutive overlapping Matches with subsequences that
        also match elsewhere should be independently extended.
        """
        matches = [
            Match(0, 1, slice(8, 10), slice(13, 15)),
            Match(0, 1, slice(9, 11), slice(14, 16)),
            Match(0, 1, slice(10, 12), slice(1, 3)),  # subset of this sequence matches elsewhere
            Match(0, 1, slice(10, 12), slice(15, 17)),
            Match(0, 1, slice(11, 13), slice(2, 4)), # subset also needs to be extended
            Match(0, 1, slice(11, 13), slice(16, 18)),
        ]
        self.assertEqual(condense_matches(matches), [
            Match(0, 1, slice(8, 13), slice(13, 18)),
            Match(0, 1, slice(10, 13), slice(1, 4))
        ])
