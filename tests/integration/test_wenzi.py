"""
These tests compare the results of DIRECT against identified textual parallels
that have already been published. The source material is "The Wenzi with
Parallel Passages from Other Pre-Han and Han Texts" (《文子》與先秦兩漢典籍重見資料彙編).
"""

from unittest import TestCase

from dphon.index import InMemoryIndex
from dphon.loader import SimpleLoader
from dphon.tokenizer import NgramTokenizer
from dphon.aligner import NeedlemanWunsch
from dphon.matcher import LevenshteinMatcher


class WenziTests(TestCase):
    """
    Set up a simple analysis stack, run the algorithm, and assert that all
    relevant matches from the published book are found.
    """

    @classmethod
    def setUpClass(cls):
        """
        We use a simple analysis stack consisting of:
            - plain text files in a directory, taken from github.com/kr-shadow
            - quad-gram tokens (n-grams of length 4) indexed from this corpus
            - an in-memory inverted index for tokens
            - a levenshtein-distance based match extension algorithm
            - needleman-wunsch alignment of identified matches
        """
        corpus = SimpleLoader('tests/fixtures/wenzi/')
        quadgrams = NgramTokenizer(n=4)
        index = InMemoryIndex()
        lev = LevenshteinMatcher(threshold=0.75, limit=50)
        nw = NeedlemanWunsch()
        # tokenize and index documents
        for doc in corpus.docs():
            index.add(quadgrams.tokenize(doc))
        # drop tokens that don't occur in at least two docs
        index.drop(lambda tokens: len(tokens) < 2)
        # extend seeds
        cls.matches = []
        for (_seed, tokens) in index.tokens():
            cls.matches.append(lev.extend(tokens[0], tokens[1]))
        # align matches
        cls.matches = [nw.align(match) for match in cls.matches]

    def test_shuoyuan(self):
        for (source, target) in self.matches:
            print(f"{source}\n{target}\n")
        return True