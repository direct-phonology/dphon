import unittest
from unittest.mock import patch

import pytest

from dphon.util import shingle


class TestUtils(unittest.TestCase):

    def test_shingle(self):
        # by default, no ngrams should include punctuation
        text = '皆知善之為善'
        ngrams = shingle(text, n=3)
        for ngram in ngrams:
            assert ngram[1].isalpha()
        # if punct flag is passed, ngrams should include punctuation
        text='名可名，非常名。'
        ngrams = shingle(text,n=3,punct=True)
        ngram_texts = [ngram[1] for ngram in ngrams]
        assert '可名，' in ngram_texts
        assert '常名。' in ngram_texts
        # ngrams in output should be the right length (n)
        text = '皆知善之為善'
        ngrams = shingle(text, n=3)
        for ngram in ngrams:
            assert len(ngram[1]) == 3
        # for a string of length l, we should get x = l - n + 1 ngrams
        text = '有名萬物之母'
        n = 3
        assert len(shingle(text, n=n)) == len(text) - n + 1
        # the output should include position markers with ngrams
        text = '皆知善之為善'
        ngrams = shingle(text, n=3)
        for ngram in ngrams:
            assert isinstance(ngram[0], int)