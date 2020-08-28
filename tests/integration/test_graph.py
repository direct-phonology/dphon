"""Test an analysis stack using a reuse graph."""
import time
from collections import defaultdict
from itertools import combinations
from multiprocessing import Process, Queue
from typing import Dict, List

from dphon.extender import LevenshteinExtender
from dphon.filter import PhoneticFilter
from dphon.graph import Match, ReuseGraph
from dphon.index import InMemoryIndex
from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer
from dphon.util import extend_matches
from dphon.extender import Extender


def extend_matches_par(matches: List[Match], extender: Extender, queue: Queue) -> None:
    for match in extend_matches(matches, extender):
        queue.put(match)

def run() -> None:
    """Test building a reuse graph with some Kanripo documents."""
    # load corpus
    start = time.time()
    corpus = KanripoLoader("tests/fixtures/krp/", clean=True)
    finish = time.time() - start
    print(f"Loaded {len(corpus)} documents in {finish:.2f} seconds")

    # index docs
    start = time.time()
    index = InMemoryIndex()
    ngrams = NgramTokenizer(n=4)
    for doc in corpus.docs():
        index.add(ngrams.tokenize(doc))
    index.drop(lambda tokens: len(tokens) < 2)
    finish = time.time() - start
    print(f"N-gram index built in {finish:.2f} seconds")
    print(f"Indexed {index.token_count():,} unique tokens at "
          f"{index.location_count():,} document locations")

    # create matches from seeds
    start = time.time()
    matches: Dict[int, Dict[int, List[Match]]] = defaultdict(lambda: defaultdict(list))
    for _seed, tokens in index.tokens():
        for token1, token2 in combinations(tokens, 2):
            matches[token1.doc.id][token2.doc.id].append(Match(
                token1.doc.id,
                token2.doc.id,
                slice(token1.start, token1.stop, 1),
                slice(token2.start, token2.stop, 1)
            ))
    finish = time.time() - start
    print(f"Seeded {len(matches):,} matches in {finish:.2f} seconds")

    # extend matches
    start = time.time()
    extender = LevenshteinExtender(corpus, 0.75, 100)
    extended: Queue = Queue()

    # NOTE parallelize by doc: split up matches by source document, then extend
    # and align them one-by-one keeping track of quote extent so work is not
    # repeated
    match_groups = [[doc2 for doc2 in doc1.values()] for doc1 in matches.values()]
    flattened = [m for g in match_groups for m in g]
    procs = []
    for group in flattened:
        procs.append(Process(target=extend_matches_par, args=(group, extender, extended)))
    for proc in procs:
        proc.start()
        proc.join()

    finish = time.time() - start
    print(f"Extended {len(extended):,} matches in {finish:.2f} seconds")

    # build graph
    # start = time.time()
    # graph = ReuseGraph(len(corpus))
    # print(f"Reuse graph built in {finish:.2f} seconds")


if __name__ == '__main__':
    run()
