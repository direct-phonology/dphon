from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer
from dphon.filter import WhitespaceFilter
from dphon.index import InMemoryIndex

trigrams = NgramTokenizer(n=3)
index = InMemoryIndex()

for doc in KanripoLoader("./test/fixtures/krp/"):
    index.store(WhitespaceFilter.process(trigrams.tokenize(doc)))

print(index)
