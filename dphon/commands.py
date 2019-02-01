import json
import re
import sys

from dphon.util import tokenize_string, lookup, shingle, clean


def analyze(text: str):
    output = {}
    for position, char in enumerate(text): 
        # get the info for each character
        if char.isalpha():
            if lookup(char):
                output[position] = lookup(char)
    return output
    # return json.dumps(output_dict, indent=4, ensure_ascii=False).encode('utf-8')

def search(text: str, search: str, punct: bool=False):
    # clean & tokenize the text
    text = clean(text)
    tokenized_text = tokenize_string(text)
    # clean & tokenize the search string
    search = clean(search)
    tokenized_search = tokenize_string(search)
    # match 4-grams of tokens
    matches = []
    shingles = shingle(tokenized_search, 4, punct)
    for ngram in shingles:
        for hit in re.finditer(ngram[1], tokenized_text):
            start = ngram[0]
            end = ngram[0] + len(ngram[1])
            search_ngram = tokenized_search[start:end]
            start = hit.start()
            end = hit.end()
            corpus_ngram = text[start:end]
            matches.append({
                'search_ngram': search_ngram,
                'search_pos': ngram[0],
                'corpus_ngram': corpus_ngram,
                'corpus_pos': hit.start()
            })
    return matches
