from dphon.loader import KanripoLoader, SimpleLoader
from dphon.tokenizer import NgramTokenizer
from dphon.filter import NonAlphaFilter, PhoneticFilter
from dphon.index import InMemoryIndex
from dphon.matcher import LevenshteinPhoneticMatcher
from dphon.aligner import NeedlemanWunschPhonetic

# analysis stack
index = InMemoryIndex()
quadgrams = NgramTokenizer(n=4)
schuessler = PhoneticFilter("data/dummy_dict.json")
direct = LevenshteinPhoneticMatcher("data/dummy_dict.json", threshold=0.75, limit=50)
nw_phon = NeedlemanWunschPhonetic("data/dummy_dict.json")

# load corpus
corpus = KanripoLoader("./test/fixtures/krp/", clean=True)
# corpus = SimpleLoader("./test/fixtures/")

# index phonetic content of all documents
for doc in corpus.docs():
    index.add(
        schuessler.process(
            NonAlphaFilter.process(
                quadgrams.tokenize(doc)
            )
        )
    )

# keep only tokens that occur in at least two places
index.drop(lambda tokens: len(tokens) < 1)

# for testing: keep only groups where exactly two texts match
index.drop(lambda tokens: len(tokens) != 2)

# keep only groups with graphic variation
# FIXME this should be done _after_ extension since otherwise we would need to
# extend both directions
# index.drop(lambda tokens: tokens[0].meta["orig_text"] == tokens[1].meta["orig_text"])

# discard documents that match themselves
index.drop(lambda tokens: tokens[0].doc.title == tokens[1].doc.title)

for (seed, tokens) in index.tokens():
    if tokens[0].meta["orig_text"] != tokens[1].meta["orig_text"]:
        match = direct.extend(tokens[0], tokens[1])
        (q1, q2) = nw_phon.align(match)
        print(f"{q1} ({match.source.doc.title})\n{q2} ({match.target.doc.title})\n")
    # print("%.02f" % match.meta["score"])
    # print(match)
