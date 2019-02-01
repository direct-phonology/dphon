import json
import unittest
from unittest.mock import patch

import pytest

from dphon.util import clean, shingle, lookup, tokenize, tokenize_string


class TestUtils(unittest.TestCase):

    def test_shingle(self):
        text = '名可名，非常名。'
        ngrams = shingle(text, n=2) # test with n=2
        ngrams_p = shingle(text, n=2, punct=True) # version with punctuation
        ngram_texts = [ngram[1] for ngram in ngrams] # the actual ngram texts
        ngram_texts_p = [ngram[1] for ngram in ngrams_p] # texts with punctuation

        for ng in ngram_texts:
            assert len(ng) == 2, 'ngrams should have length `n`'

        for n in range(1, 5): # this only holds if punctuation is included
            assert len(shingle(text, n=n, punct=True)) == len(text) - n + 1, \
            'for a string of length l, we should get x = l - n + 1 ngrams'

        for ng in ['名可', '可名', '非常', '常名']:
            assert ng in ngram_texts, 'shingling should produce all valid ngrams'

        for ng in ngrams:
            assert isinstance(ng[0], int), 'output should include positions'

        for ng in ngram_texts:
            assert ng.isalpha(), 'punctuation should be ignored by default'
        
        for ng in ['名，', '名。']:
            assert ng in ngram_texts_p, '`punct` flag should enable punctuation'

    def test_clean(self):
        text = '名可名， 非常名。 \t可名，名。\r\n非常\f  非常名\v.'
        whitespace = [' ', '\f', '\n', '\r', '\t', '\v']
        clean_text = clean(text)

        for char in whitespace:
            assert char not in clean_text, \
            'cleaned text should not include whitespace'

    def test_lookup(self):
        assert type(lookup('冥')) is dict, 'should return a dictionary entry'
        assert type(lookup('冥')['dummy']) is str, 'entry should contain a dummy'
        assert lookup('𠀀') is False, 'should return false for missing chars'

    def test_tokenize(self):
        assert tokenize('冥') == '名', 'should return the dummy char, if present'
        assert tokenize('𠀀') == '𠀀', 'input should be unchanged if no entry'
        assert tokenize('。') == '。', 'input should be unchanged for punctuation'
        assert tokenize('\n') == '\n', 'input should be unchanged for whitespace'

    def test_tokenize_string(self):
        string = '名可名，非常名。'
        string_t = tokenize_string(string)

        for char in string:
            assert tokenize(char) in string_t, 'should tokenize all chars in string'
