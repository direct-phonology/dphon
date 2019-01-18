import json
import re
import sys

from dphon.util import tokenize_file, lookup, shingle, clean, load_file


def ingest(arguments: dict):
    # TODO sanitize the input
    with open(arguments['<text>']) as file:
        output_dict = {}
        file_text = file.read()
        for position, char in enumerate(file_text): 
            # tokenize the input
            if char.isalpha():
                if lookup(char):
                    output_dict[position] = lookup(char)
    # output a optimized database to match against
    return json.dumps(output_dict, indent=4, ensure_ascii=False).encode('utf-8')

def match(arguments: dict):
    # sanitize the input
    punct = arguments['--punctuation']
    # tokenize the search string
    orig_search = clean(load_file(arguments['<search>']))
    search = clean(tokenize_file(arguments['<search>']))
    # tokenize the matched text
    orig_corpus = clean(load_file(arguments['<corpus>']))
    corpus = clean(tokenize_file(arguments['<corpus>']))
    # match the input against the database
    matches = []
    if punct:
        shingles = shingle(text=search, n=4, punct=True)
    else:
        shingles = shingle(text=search, n=4)
    for ngram in shingles:
        for hit in re.finditer(ngram[1], corpus):
            start = ngram[0]
            end = ngram[0] + len(ngram[1])
            search_ngram = orig_search[start:end]
            start = hit.start()
            end = hit.end()
            corpus_ngram = orig_corpus[start:end]
            matches.append({
                'search_ngram': search_ngram,
                'search_pos': ngram[0],
                'corpus_ngram': corpus_ngram,
                'corpus_pos': hit.start()
            })
    for match in matches:
        print("{}({}) :: {}({})".format(
            match['search_ngram'],
            match['search_pos'],
            match['corpus_ngram'],
            match['corpus_pos']
        ))
    # use n-gram shingling to compute similarity
    # output info about results
    pass
