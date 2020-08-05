"""Test an analysis stack using a reuse graph."""
import time
from itertools import combinations

from dphon.filter import PhoneticFilter
from dphon.graph import ReuseGraph
from dphon.index import InMemoryIndex
from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer


def run() -> None:
    """Test building a reuse graph with some Kanripo documents."""
    # setup analysis stack
    index = InMemoryIndex()
    ngrams = NgramTokenizer(n=4)
    token_filter = PhoneticFilter("data/dummy_dict.json")

    # load corpus
    start = time.time()
    corpus = KanripoLoader("tests/fixtures/krp/", clean=True)
    finish = time.time() - start
    print(f"Loaded {len(corpus)} documents in {finish:.2f} seconds")

    # index docs
    start = time.time()
    for doc in corpus.docs():
        index.add(token_filter.process(ngrams.tokenize(doc)))
    index.drop(lambda tokens: len(tokens) < 2)
    finish = time.time() - start
    print(f"N-gram index built in {finish:.2f} seconds")
    print(f"Indexed {index.token_count():,} unique tokens at "
          f"{index.location_count():,} document locations")

    # build graph
    start = time.time()
    graph = ReuseGraph(len(corpus))
    for _seed, tokens in index.tokens():
        for token1, token2 in combinations(tokens, 2):
            graph.add_match(
                token1.doc.id,
                token2.doc.id,
                slice(token1.start, token1.stop, 1),
                slice(token2.start, token2.stop, 1)
            )
    finish = time.time() - start
    print(f"Reuse graph built in {finish:.2f} seconds")


if __name__ == '__main__':
    run()
