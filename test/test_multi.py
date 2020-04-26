from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer
from dphon.filter import NonAlphaFilter, PhoneticFilter
from dphon.index import InMemoryIndex

# analysis stack
index = InMemoryIndex()
trigrams = NgramTokenizer(n=3)
schuessler = PhoneticFilter("data/dummy_dict.json")

# load corpus
corpus = KanripoLoader("./test/fixtures/krp/")

# index phonetic content of all documents
for doc in corpus.docs():
    index.add(
        schuessler.process(
            NonAlphaFilter.process(
                trigrams.tokenize(doc)
            )
        )
    )

# keep only tokens that occur in at least two places
index.drop(lambda tokens: len(tokens) < 1)

# for testing: keep only groups where exactly two texts match
index.drop(lambda tokens: len(tokens) != 2)

for (seed, tokens) in index.tokens():
    print(f"seed: {seed} tokens: {tokens}")
