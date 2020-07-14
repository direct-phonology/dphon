"""
Utility function tests
"""


from unittest import TestCase

from dphon.tokenizer import Token
from dphon.util import has_graphic_variation
from dphon.document import Document


class TestHasGraphicVariation(TestCase):

    def setUp(self):
        # create some basic docs to compare
        self.doc1 = Document(0, '恐出奔齊有二心矣')
        self.doc2 = Document(1, '公出奔齊有二心矣')
        self.doc3 = Document(2, '恐出奔齊有二心矣')

    def test_with_variation(self):
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

    def test_no_variation(self):
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
