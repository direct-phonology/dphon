from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer
from dphon.filter import NonAlphaFilter, PhoneticFilter
from dphon.index import InMemoryIndex

index = InMemoryIndex()
trigrams = NgramTokenizer(n=3)
schuessler = PhoneticFilter("data/dummy_dict.json")

# index phonetic content of all documents
for doc in KanripoLoader("./test/fixtures/krp/"):
    index.add(
        schuessler.process(
            NonAlphaFilter.process(
                trigrams.tokenize(doc)
            )
        )
    )

# keep only tokens that occur in at least two places
index.drop(lambda tokens: len(tokens) > 1)

print(index)
