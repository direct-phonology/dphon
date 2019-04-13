from re import finditer
from typing import List
from itertools import count, chain

from dphon.lib import Character, Sequence, Match

def build_character_array(text: str):
    return [Character(position=pos, original=char) for pos, char in enumerate(text)]

def clean(text: List):
    """Discard whitespace and punctuation characters."""
    return [c for c in text if c.original.isalpha()]

def shingle(text: List, n: int=3):
    """Split a given string into all possible overlapping n-grams."""
    return [text[i:i + n] for i in range(len(text) - n + 1)]

def match(textA: List, textB: List, a, b):
    all_matches = {}
    initial_n = 4  # start with 4-grams
    for n in count(initial_n):
        n_matches = [] # list of matches for this n
        a_ngrams = shingle(textA, n) # shingle both texts using this length
        b_ngrams = shingle(textB, n)
        for a_ngram in a_ngrams:
            for b_ngram in b_ngrams:
                if ''.join([c.dummy for c in a_ngram]) == ''.join([c.dummy for c in b_ngram]):
                    # we got a match, add it
                    a_sequence = Sequence(a_ngram[0].position, a_ngram[-1].position)
                    b_sequence = Sequence(b_ngram[0].position, b_ngram[-1].position)
                    n_matches.append(Match(source=a_sequence, dest=b_sequence))
                    # check if it's a longer version of an earlier match
                    if n > initial_n: # not necessary on first run
                        old_matches = [m for m in all_matches[str(n-1)] if m.source.start >= a_ngram[0].position and m.source.end <= a_ngram[-1].position and m.dest.start >= b_ngram[0]. position and m.dest.end <= b_ngram[-1].position]
                        if old_matches:
                            for match in old_matches:
                                all_matches[str(n-1)].remove(match)
        if len(n_matches) > 0: # if we found matches
            all_matches[str(n)] = n_matches # add them to the big dict
            continue # keep going
        else: # no matches found at this length, we're done
            break
    return chain.from_iterable(all_matches.values()) # iterable of all matches