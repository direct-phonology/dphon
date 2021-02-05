#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dphon - a tool for old chinese phonetic analysis
 
Usage:
    dphon -h | --help
    dphon --version
    dphon <path>... [options]
 
Global Options:
    -h, --help                  Show this help text.
    -v, --version               Show program version.
    -o <file>, --output <file>  Write output to a file instead of stdout.
    -f <fmt>, --format <fmt>    Set input file type. Currently, plaintext (.txt) and json-lines (.jsonl)
                                files are supported. [default: txt]

Matching Options:
    -n <n>, --ngram-order <n>   Order of n-grams used to seed matches. Higher means decreased execution
                                time at the expense of total result count. [default: 4]
    -k <k>, --threshold <k>     Similarity threshold below which matches will not be retained. Higher
                                means shorter matches and fewer total results. [default: 0.7]
    -l <l>, --len-limit <l>     Limit on number of tokens to compare to obtain similarity score. Higher
                                means longer matches at the expense of execution time. [default: 50]

Filtering Options:
    -a, --all                   Allow matches without graphic variation. By default, only matches
                                containing at least one token with shared phonemes but differing graphemes 
                                are shown.
    --min <min>                 Limit to matches with total tokens >= min. Has no effect if less than
                                the value for "--ngram-order", above.
    --max <max>                 Limit to matches with total tokens <= max. Must be equal to or greater
                                than the value for "--ngram-order", above.

Examples:
    dphon texts/*.txt --min 8 --output matches.txt
    dphon file1.txt file2.txt -n 8 -k 0.8
    dphon docs.jsonl --format jsonl
 
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
from rich.progress import BarColumn, Progress, SpinnerColumn
from spacy.language import Language
from spacy.tokens import Doc

from . import __version__
from .align import SmithWatermanPhoneticAligner
from .extend import LevenshteinPhoneticExtender
from .fmt import DEFAULT_THEME, SimpleFormatter
from .index import Index
from .io import CorpusLoader, JsonLinesCorpusLoader, PlaintextCorpusLoader
from .match import Match
from .ngrams import Ngrams
from .phonemes import Phonemes, get_sound_table_json
from .reuse import MatchGraph


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=__version__)

    # install logging and exception handlers
    logging.basicConfig(level="INFO", format="%(message)s",
                        datefmt="[%X]", handlers=[RichHandler()])
    logging.captureWarnings(True)
    traceback.install()

    # setup pipeline
    nlp = setup(args)

    # process all texts
    graph = process(nlp, args)
    results = list(graph.matches)
    logging.info(f"{len(results)} total results matching query")

    # sort results by highest total score
    results = sorted(results, key=lambda m: m.weight, reverse=True)

    # set up formatting - colorize for terminal but not for files
    console = Console(theme=DEFAULT_THEME)
    format = SimpleFormatter(gap_char="　")

    # write to a file if requested; otherwise write to stdout
    # NOTE should use rich's builtin to do this:
    # https://rich.readthedocs.io/en/stable/console.html#file-output
    # will automatically strip colors
    if args["--output"]:
        outpath = Path(args["--output"])
        with outpath.open(mode="w", encoding="utf8") as file:
            for match in results:
                file.write(format(match) + "\n\n")
        logging.info(f"wrote {outpath.resolve()}")
    else:
        # NOTE use console.pager(styles=True) for colorized output
        with console.pager(styles=True):
            for match in results:
                console.print((format(match) + "\n"), soft_wrap=False)

    # teardown pipeline
    teardown(nlp)


def setup(args: Dict) -> Language:
    """Set up the spaCy processing pipeline."""
    # get sound table
    sound_table = get_sound_table_json(
        Path("./dphon/data/sound_table_v2.json"))

    # add Doc metadata
    Doc.set_extension("id", default="")

    # setup spaCy model
    nlp = spacy.blank(
        "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
    nlp.add_pipe(Phonemes(nlp, sound_table=sound_table), first=True)
    nlp.add_pipe(Ngrams(nlp, n=int(args["--ngram-order"])), after="phonemes")
    nlp.add_pipe(Index(nlp, val_fn=lambda doc: doc._.ngrams,
                       filter_fn=lambda ngram: ngram.text.isalpha(),
                       key_fn=lambda ngram: "".join(ngram._.phonemes)))
    logging.info("loaded default spaCy model")
    return nlp


def process(nlp: Language, args: Dict) -> MatchGraph:
    """Run the spaCy processing pipeline."""
    # set up graph and loader
    graph = MatchGraph()
    load_texts: CorpusLoader
    if args["--format"] == "jsonl":
        load_texts = JsonLinesCorpusLoader()
    else:
        load_texts = PlaintextCorpusLoader()

    # load and index all documents
    start = time.perf_counter()
    for doc, context in nlp.pipe(load_texts(args["<path>"]), as_tuples=True):
        doc._.id = context["id"]
        graph.add_doc(context["id"], doc)
        logging.debug(f"indexed doc \"{doc._.id}\"")
    stop = time.perf_counter() - start
    logging.info(f"indexed {graph.number_of_docs()} docs in {stop:.1f}s")

    # prune all ngrams from index that only occur once
    groups = list(nlp.get_pipe("index").filter(lambda g: len(g[1]) > 1))

    # create initial pairwise matches from seed groups
    progress = Progress(
        "[progress.description]{task.description}",
        SpinnerColumn(),
        "[progress.description]{task.fields[seed]}",
        BarColumn(bar_width=None),
        "{task.completed}/{task.total}",
        "[progress.percentage]{task.percentage:>3.1f}%",
        transient=True,
    )
    task = progress.add_task("seeding", seed="", total=len(groups))
    start = time.perf_counter()
    with progress:
        for _seed, locations in groups:
            logging.debug(
                f"evaluating seed group \"{locations[0].text}\", size={len(locations)}")
            progress.update(task, seed=locations[0].text)
            for utxt, vtxt in combinations(locations, 2):
                if utxt.doc._.id != vtxt.doc._.id:  # skip same-doc matches
                    graph.add_match(
                        Match(utxt.doc._.id, vtxt.doc._.id, utxt, vtxt, 1.0))
            progress.advance(task)
    stop = time.perf_counter() - start
    logging.info(f"seeded {graph.number_of_matches()} matches in {stop:.1f}s")

    # limit to seeds with graphic variants if requested
    if not args["--all"]:
        graph.filter(nlp.get_pipe("phonemes").has_variant)

    # extend all matches
    graph.extend(LevenshteinPhoneticExtender(
        threshold=float(args["--threshold"]),
        len_limit=int(args["--len-limit"])
    ))

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
