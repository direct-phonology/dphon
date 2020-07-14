import time
from itertools import combinations

from dphon.filter import PhoneticFilter
from dphon.graph import ReuseGraph
from dphon.index import InMemoryIndex
from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer

# analysis stack
INDEX = InMemoryIndex()
QUADGRAMS = NgramTokenizer(n=4)
SCHUESSLER = PhoneticFilter("data/dummy_dict.json")

# load corpus
start = time.time()
CORPUS = KanripoLoader("tests/fixtures/krp/", clean=True)
finish = time.time() - start
print(f"Loaded {len(CORPUS)} documents in {finish:.2f} seconds")

# load corpus and index
start = time.time()
for doc in CORPUS.docs():
    INDEX.add(SCHUESSLER.process(QUADGRAMS.tokenize(doc)))
INDEX.drop(lambda tokens: len(tokens) < 2)
finish = time.time() - start
print(f"N-gram index built in {finish:.2f} seconds")
print(f"Indexed {INDEX.token_count():,} unique tokens at {INDEX.location_count():,} document locations")

# build graph
start = time.time()
GRAPH = ReuseGraph(len(CORPUS))

for (_text, tokens) in INDEX.tokens():
    for (token1, token2) in combinations(tokens, 2):
        GRAPH.add_match(
            token1.doc.id,
            token2.doc.id,
            slice(token1.start, token1.stop, 1),
            slice(token2.start, token2.stop, 1)
        )


finish = time.time() - start
print(f"Reuse graph built in {finish:.2f} seconds")
