#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dphon - a tool for old chinese phonetic analysis
 
Usage:
    dphon -h | --help
    dphon --version
    dphon [options] <path>... 
 
Options:
    -h, --help                   Show this help.
    -v, --version                Show program version.
    -a, --all                    Allow matches without graphic variation.
    -o <file>, --output <file>   Write output to a file.
    --min <min>                  Limit to matches with total tokens >= min.
    --max <max>                  Limit to matches with total tokens <= max.
 
Examples:
    dphon texts/ --min 8
    dphon 老子甲.txt 老子丙.txt 老子乙.txt --output matches.txt
    dphon 周南.txt 鹿鳴之什.txt --all
 
Help:
    For more information on using this tool, visit the Github repository:
    https://github.com/direct-phonology/direct
"""

import logging
import time
from itertools import combinations
from pathlib import Path
from typing import Dict

import spacy
from docopt import docopt
from rich import traceback
from rich.console import Console
from rich.logging import RichHandler
from spacy.language import Language
from spacy.tokens import Doc

from . import __version__
from .align import SmithWatermanPhoneticAligner
from .extend import LevenshteinPhoneticExtender
from .fmt import DEFAULT_THEME, SimpleFormatter
from .index import Index
from .io import JsonLinesCorpusLoader, PlaintextCorpusLoader
from .match import Match
from .ngrams import Ngrams
from .phonemes import Phonemes, get_sound_table_json
from .reuse import MatchGraph
from .util import progress

# install logging and exception handlers
logging.basicConfig(level="DEBUG", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])
logging.captureWarnings(True)
traceback.install()


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=__version__)

    # setup pipeline
    nlp = setup()

    # process all texts
    graph = process(nlp, args)
    results = list(graph.matches)
    logging.info(f"{len(results)} total results matching query")

    # set up formatting - colorize for terminal but not for files
    console = Console(theme=DEFAULT_THEME)
    format = SimpleFormatter(gap_char="　")

    # write to a file if requested; otherwise write to stdout
    if args["--output"]:
        with open(args["--output"], mode="w", encoding="utf8") as file:
            for match in results:
                file.write(format(match) + "\n")
        logging.info(f"wrote {args['--output']}")
    else:
        for match in results:
            console.print((format(match) + "\n"))

    # teardown pipeline
    teardown(nlp)


def setup() -> Language:
    """Set up the spaCy processing pipeline."""
    # get sound table
    sound_table = get_sound_table_json(Path("./dphon/data/sound_table.json"))

    # add Doc metadata
    Doc.set_extension("id", default="")

    # setup spaCy model
    nlp = spacy.blank(
        "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
    nlp.add_pipe(Phonemes(nlp, sound_table=sound_table), first=True)
    nlp.add_pipe(Ngrams(nlp, n=4), after="phonemes")
    nlp.add_pipe(Index(nlp, val_fn=lambda doc: doc._.ngrams,
                       filter_fn=lambda ngram: ngram.text.isalpha(),
                       key_fn=lambda ngram: "".join(ngram._.phonemes)))
    logging.info("loaded default spaCy model")
    return nlp


def process(nlp: Language, args: Dict) -> MatchGraph:
    """Run the spaCy processing pipeline."""

    # load and index all documents
    graph = MatchGraph()
    load_texts = JsonLinesCorpusLoader()
    with progress:
        docs_task = progress.add_task("indexing documents")
        all_start = time.perf_counter()
        start = all_start
        for doc, context in nlp.pipe(load_texts(args["<path>"]), as_tuples=True):
            doc._.id = context["id"]
            graph.add_doc(context["id"], doc)
            progress.update(docs_task, advance=1)
            finish = time.perf_counter() - start
            logging.debug(
                f"indexed doc \"{context['id']}\" in {finish:.3f}s")
            start = time.perf_counter()
        progress.remove_task(docs_task)
    all_finish = time.perf_counter() - all_start
    logging.info(f"indexing completed in {all_finish:.3f}s")

    # drop all ngrams from index that only occur once
    groups = nlp.get_pipe("index").filter(lambda g: len(g[1]) > 1)

    # create initial pairwise matches from seed groups; perfect score of 1.0
    for _seed, locations in groups:
        for utxt, vtxt in combinations(locations, 2):
            if utxt.doc != vtxt.doc:  # skip same-doc matches
                graph.add_match(
                    Match(utxt.doc._.id, vtxt.doc._.id, utxt, vtxt, 1.0))

    # limit to seeds with graphic variants if requested
    if not args["--all"]:
        graph.filter(nlp.get_pipe("phonemes").has_variant)

    # extend all matches
    graph.extend(LevenshteinPhoneticExtender(threshold=0.7, len_limit=50))

    # align all matches
    graph.align(SmithWatermanPhoneticAligner())

    # limit via min and max lengths if requested
    if args["--min"]:
        graph.filter(lambda m: len(m) >= int(args["--min"]))
    if args["--max"]:
        graph.filter(lambda m: len(m) <= int(args["--max"]))

    # return completed reuse graph
    return graph


def teardown(nlp: Language) -> None:
    """Unregister spaCy extensions to prevent name collisions."""
    Doc.remove_extension("id")

    # iterate over all pipeline components and call teardown() if it exists
    for _name, component in nlp.pipeline:
        if hasattr(component, "teardown"):
            component.teardown()


if __name__ == "__main__":
    run()
