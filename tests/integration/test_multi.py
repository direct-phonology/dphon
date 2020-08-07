"""Test an analysis stack that extends and aligns all matches."""
import sys
import time
from itertools import combinations
from progressbar import progressbar

from dphon.aligner import NeedlemanWunschPhoneticAligner
from dphon.extender import LevenshteinPhoneticExtender
from dphon.filter import PhoneticFilter
from dphon.graph import Match
from dphon.index import InMemoryIndex
from dphon.loader import KanripoLoader
from dphon.tokenizer import NgramTokenizer
from dphon.util import has_graphic_variation


def run() -> None:
    """Test text reuse identification with some Kanripo documents."""
    # setup analysis stack
    index = InMemoryIndex()
    ngrams = NgramTokenizer(n=4)
    token_filter = PhoneticFilter("data/dummy_dict.json")
    aligner = NeedlemanWunschPhoneticAligner("data/dummy_dict.json")

    # load corpus
    start = time.time()
    corpus = KanripoLoader("tests/fixtures/krp/", clean=True)
    finish = time.time() - start
    sys.stderr.write(
        f"Loaded {len(corpus)} documents in {finish:.2f} seconds\n")

    # index docs
    start = time.time()
    for doc in corpus.docs():
        index.add(token_filter.process(ngrams.tokenize(doc)))
    index.drop(lambda tokens: len(tokens) < 2)
    finish = time.time() - start
    sys.stderr.write(f"N-gram index built in {finish:.2f} seconds\n")
    sys.stderr.write(f"Indexed {index.token_count():,} unique tokens at "
                     f"{index.location_count():,} document locations\n")

    # create matches from seeds and extend them
    start = time.time()
    matches = []
    count = 0
    extender = LevenshteinPhoneticExtender(
        corpus, "data/dummy_dict.json", threshold=0.75, len_limit=100)
    for _seed, tokens in progressbar(index.tokens()):
        for token1, token2 in combinations(tokens, 2):
            if token1.doc.id != token2.doc.id:  # don't match with same doc
                match = Match(
                    doc1=token1.doc.id,
                    doc2=token2.doc.id,
                    pos1=slice(token1.start, token1.stop, 1),
                    pos2=slice(token2.start, token2.stop, 1)
                )
                matches.append(extender.extend(match))
                count += 1
    finish = time.time() - start
    sys.stderr.write(f"Extended {count:,} seeds in {finish:.2f} seconds\n")

    # TODO drop matches without graphic variation


    # align matches
    start = time.time()
    aligned_matches = []
    matches = matches[:100]
    for match in progressbar(matches):
        source = corpus.get(match.doc1)[match.pos1]
        target = corpus.get(match.doc2)[match.pos2]
        aligned_matches.append(aligner.align(source, target))
    finish = time.time() - start
    sys.stderr.write(f"Aligned matches in {finish:.2f} seconds\n")

    # write results to file
    for i, match in enumerate(matches):
        source, target = aligned_matches[i]
        doc1 = corpus.get(match.doc1)
        doc2 = corpus.get(match.doc2)
        sys.stdout.write(
            f"{source}\t({doc1.title}:{doc1.meta['JUAN']})\n"
            f"{target}\t({doc2.title}:{doc2.meta['JUAN']})\n\n"
        )


if __name__ == '__main__':
    run()
