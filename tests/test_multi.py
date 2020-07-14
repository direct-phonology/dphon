import time

from dphon.aligner import NeedlemanWunschPhonetic
from dphon.filter import PhoneticFilter
from dphon.index import InMemoryIndex
from dphon.loader import KanripoLoader
from dphon.matcher import LevenshteinPhoneticMatcher
from dphon.tokenizer import NgramTokenizer
from dphon.util import has_graphic_variation

# analysis stack
index = InMemoryIndex()
quadgrams = NgramTokenizer(n=4)
schuessler = PhoneticFilter("data/dummy_dict.json")
direct = LevenshteinPhoneticMatcher("data/dummy_dict.json", threshold=0.75, limit=50)
nw_phon = NeedlemanWunschPhonetic("data/dummy_dict.json")

# global timer
start_time = time.time()

# load corpus
corpus = KanripoLoader("./test/fixtures/krp/", clean=True)
load_time = time.time() - start_time
print(f"Loaded corpus in {load_time:.2f} seconds")

# index phonetic content of all documents
for doc in corpus.docs():
    index.add(schuessler.process(quadgrams.tokenize(doc)))
index_time = time.time() - start_time - load_time
print(f"Indexed documents in {index_time:.2f} seconds")

# keep only tokens that occur in at least two places
index.drop(lambda tokens: len(tokens) < 2)

# FIXME testing: keep only groups where exactly two different docs match 
index.drop(lambda tokens: len(tokens) != 2)
index.drop(lambda tokens: tokens[0].doc.title == tokens[1].doc.title)
prune_time = time.time() - start_time - load_time - index_time
print(f"Pruned index in {prune_time:.2f} seconds")

# extend and align seeds
matches = []
for (seed, tokens) in index.tokens():
    # only work on matches with graphic variation
    if has_graphic_variation(tokens):
        matches.append(direct.extend(tokens[0], tokens[1]))
match_time = time.time() - start_time - load_time - index_time - prune_time
print(f"Extended seeds in {match_time:.2f} seconds")

aligned_matches = [nw_phon.align(match) for match in matches]
align_time = time.time() - start_time - load_time - index_time - prune_time - match_time
print(f"Aligned matches in {align_time:.2f} seconds")

for i in range(len(matches)):
    match = matches[i]
    (q1, q2) = aligned_matches[i]
    print(f"{q1} ({match.source.doc.title}:{match.source.doc.meta['JUAN']})\n{q2} ({match.target.doc.title}:{match.target.doc.meta['JUAN']})\n")
