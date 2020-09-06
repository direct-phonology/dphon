import csv
import json
import logging
import time
from collections import defaultdict
from itertools import combinations, groupby
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import spacy
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table as RichTable
from rich.traceback import install
from spacy.lang.zh import ChineseDefaults
from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

from dphon.index import Index
from dphon.ngrams import Ngrams
from dphon.phonemes import (OOV_PHONEMES, Phonemes, SoundTable_T,
                            get_sound_table_csv)
from dphon.util import get_texts, extend_matches
from dphon.extender import LevenshteinExtender
from dphon.match import Match

# turn off default settings for spacy's chinese model
ChineseDefaults.use_jieba = False

# install logging and exception handlers
logging.basicConfig(level="DEBUG", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])
install()

if __name__ == "__main__":
    # load texts and sound table
    texts = get_texts(Path("/Users/nbudak/src/ect-krp/tmp/史記"))
    sound_table = get_sound_table_csv(
        Path("./dphon/data/BaxterSagartOC_parsed.csv"))

    # setup pipeline
    nlp = spacy.blank("zh")

    ngrams = Ngrams(nlp, n=4)
    phonemes = Phonemes(nlp, "bs_phonemes", syllable_parts=8,
                        sound_table=sound_table)
    index = Index(nlp, "ngram_index",
                  val_fn=lambda doc: doc._.ngrams,
                  filter_fn=lambda ngram: ngram.text.isalpha(),
                  key_fn=lambda ngram: "".join(ngram._.phonemes))
    # index = Index(nlp, "tok_index", val_fn=lambda doc: [token for token in doc if token.is_alpha],
    #               key_fn=lambda token: token.text if not token._.is_oov else None)
    # oov = Index(nlp, "oov_index", val_fn=lambda doc: [token for token in doc if token.is_alpha],
    #             key_fn=lambda token: token.text if token._.is_oov else None)

    nlp.add_pipe(phonemes, first=True)
    nlp.add_pipe(ngrams, after="bs_phonemes")
    nlp.add_pipe(index)

    logging.info(f"loaded spaCy model \"{nlp.meta['name']}\"")

    # store output statistics & visualize progress
    progress = Progress(
        "{task.elapsed:.0f}s",
        "{task.description}",
        BarColumn(bar_width=None),
        "{task.completed:,}/{task.total:,}",
        "{task.percentage:.1f}%",
        transient=True
    )

    # process all texts
    with progress:
        docs_task = progress.add_task("indexing documents", total=len(texts))
        all_start = time.time()
        start = time.time()
        for doc, context in nlp.pipe(texts, as_tuples=True):
            progress.update(docs_task, advance=1)
            finish = time.time() - start
            logging.debug(f"processed doc {context['title']} in {finish:.3f}s")
            start = time.time()
        progress.remove_task(docs_task)
    all_finish = time.time() - all_start
    logging.info(f"completed spaCy pipeline in {all_finish:.3f}s")

    # drop all ngrams that only occur once
    groups = list(index.filter(lambda entry: len(entry[1]) > 1))

    # create initial pairwise matches from seed groups
    matches: List[Match] = []
    with progress:
        matches_task = progress.add_task("generating matches", total=len(groups))
        start = time.time()
        for seed, locations in groups:
            for left, right in combinations(locations, 2):
                if left.doc != right.doc: # skip same-doc matches
                    matches.append(Match(left, right)) # FIXME ignore those without graphic var?
            progress.update(matches_task, advance=1)
        progress.remove_task(matches_task)
    finish = time.time() - start
    logging.info(f"created {len(matches):,} initial matches in {finish:.3f}s")

    # query match groups from the index and extend them, keeping track of the
    # extent of existing matches so as not to duplicate work
    extender = LevenshteinExtender(threshold=0.8, len_limit=50)
    with progress:
        extend_task = progress.add_task("extending matches", total=len(matches))
        start = time.time()
        new_matches = extend_matches(matches, extender, progress, extend_task)
        progress.remove_task(extend_task)
    finish = time.time() - start
    logging.info(f"extended {len(new_matches):,} matches in {finish:.3f}s")

    # write out results
    outfile = Path("./results.txt")
    with outfile.open(mode="w") as file:
        for match in new_matches:
            file.write(f"{match.__repr__()}\t{match}\n")

    '''
    logging.info(
    f"{len(index)} unique phonetic {ngrams.n}-grams were encountered {index.size} times")
    logging.info(
        f"{len(index)} unique tokens were encountered {index.size} times"
    )
    logging.info(
        f"{len(oov)} unique out-of-vocab tokens were encountered {oov.size} times")

    top10 = list(sorted(oov, reverse=True,
                        key=lambda entry: len(entry[1])))[:10]
    total_top10 = sum([len(v) for (k, v) in top10])
    percentage = total_top10 / oov.size * 100

    logging.info(
        f"top 10 out-of-vocab tokens encountered {total_top10} times or {percentage:>3.1f}% of total")

    console = Console()
    table = RichTable(title="top 10 out-of-vocab tokens")
    table.add_column("token")
    table.add_column("count", justify="right")
    for k, v in top10:
        table.add_row(nlp.vocab[k].text, f"{len(v)}")
    console.print(table, justify="center")
    '''


    # build a reuse graph using the extended matches
