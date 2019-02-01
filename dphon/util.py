import json

with open('data/dummy_dict.json') as file:
    DUMMY_DICT = json.loads(file.read())

def lookup(char: str):
    """Retrieve information on single a character from a dictionary."""
    if char.isalpha():
        if char in DUMMY_DICT:
            return {
                'char': char,
                'init': DUMMY_DICT[char][0],
                'rhyme': DUMMY_DICT[char][1],
                'dummy': DUMMY_DICT[char][2]
            }
    return False

def tokenize(char: str):
    """Convert a single character to a phonological token."""
    entry = lookup(char)
    if entry:
        return entry['dummy']
    return char

def tokenize_string(string: str):
    """Convert a string into phonological tokens."""
    return ''.join([tokenize(char) for char in string])

def clean(text: str):
    """Remove whitespace from a string."""
    return ''.join(text.split())

def shingle(text: str, n: int=3, punct=False):
    """Split a given string into all possible overlapping n-grams."""
    ngrams = [(i, text[i:i + n]) for i in range(len(text) - n + 1)]
    if not punct:
        return [ngram for ngram in ngrams if ngram[1].isalpha()]
    else:
        return ngrams
