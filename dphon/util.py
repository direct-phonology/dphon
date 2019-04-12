from re import finditer
from typing import List

from dphon.lib import Character, Sequence, Match

def build_character_array(text: str):
    return [Character(position=pos, original=char) for pos, char in enumerate(text)]

def clean(text: List):
    """Discard whitespace and punctuation characters."""
    return [c for c in text if c.original.isalpha()]

def shingle(text: List, n: int=3):
    """Split a given string into all possible overlapping n-grams."""
    return [text[i:i + n] for i in range(len(text) - n + 1)]

def match(textA: List, textB: List):
    # start with trigrams
    matches = []
    a_ngrams = shingle(textA, 4)
    b_ngrams = shingle(textB, 4)
    for a_ngram in a_ngrams:
        for b_ngram in b_ngrams:
            if ''.join([c.dummy for c in a_ngram]) == ''.join([c.dummy for c in b_ngram]):
            # if a_ngram[0].dummy == b_ngram[0].dummy and a_ngram[1].dummy == b_ngram[1].dummy and a_ngram[2].dummy == b_ngram[2].dummy:
                a_sequence = Sequence(0, a_ngram[0].position, a_ngram[3].position - a_ngram[0].position)
                b_sequence = Sequence(1, b_ngram[0].position, b_ngram[3].position - b_ngram[0].position)
                matches.append(Match(source = a_sequence, dest = b_sequence))
    return matches