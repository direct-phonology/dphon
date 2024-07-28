#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dphon - a tool for old chinese phonetic analysis

Usage:
    dphon -h | --help
    dphon --version
    dphon [-v | -vv] [options] <path>...

Global Options:
    -h, --help
        Show this help text and exit.

    --version
        Show program version and exit.

    -v, -vv
        Increase verbosity of logs sent to stderr. Default log level is WARN;
        -v corresponds to INFO and -vv to DEBUG.

    -i <FMT>, --input-format <FMT>  [default: txt]
        Set input format. Currently, plaintext (txt) and JSON lines (jsonl) are
        supported.

    -o <FMT>, --output-format <FMT> [default: txt]
        Set output format. Currently, plaintext (txt), JSON lines (jsonl),
        comma-separated values (csv), and html (html) are supported. Note that
        you still need to redirect to a file in order to save the output.

Matching Options:
    -n <NUM>, --ngram-order <NUM>   [default: 4]
        Order of n-grams used to seed matches. A higher number will speed up
        execution time, but smaller matches won't be returned.

    -k <NUM>, --threshold <NUM>     [default: 0.7]
        Discard matches with an overall similarity ratio below NUM. A higher
        number will result in fewer matches with less variance.

    -l <NUM>, --len-limit <NUM>     [default: 50]
        Compare at most NUM tokens when obtaining the similarity score. A
        higher number will slow down execution time but return more matches.

    -c <NUM>, --context <NUM>       [default: 4]
        Add NUM tokens of context to each side of matches. Context displays with
        a dimmed appearance if color is supported in the terminal.

Filtering Options:
    -a, --all
        Allow matches without graphic variation. By default, only matches
        containing at least one token with shared phonemes but differing
        graphemes (a graphic variant) are shown.

    --min-length <NUM>               [default: 8]
        Limit to matches with total number of tokens >= NUM. Has no effect if
        less than the value for "--ngram-order".

    --max-length <NUM>               [default: 64]
        Limit to matches with total number of tokens <= NUM. Must be equal to
        or greater than the value for "--ngram-order".

    --min-graphic-similarity <NUM>   [default: 0]
        Limit to matches with a graphic similarity ratio >= NUM. The default is
        to allow matches with no graphic similarity at all (0).

    --max-graphic-similarity <NUM>   [default: 0.9]
        Limit to matches with a graphic similarity ratio <= NUM. The default is
        to exclude matches that are almost graphically identical (0.9).

    --min-phonetic-similarity <NUM>  [default: 0.7]
        Limit to matches with a phonetic similarity ratio >= NUM. The default is
        to allow matches with some phonetic variance (0.7).

    --max-phonetic-similarity <NUM>  [default: 1]
        Limit to matches with a phonetic similarity ratio <= NUM. The default is
        to allow matches that are phonetically identical (1).

Display options:
    -g, --group                [default: False]
        Group matches by shared text. By default, matches are displayed as
        individual pairs of similar sequences.

Examples:
    dphon texts/*.txt > matches.txt
    dphon file1.txt file2.txt --ngram-order 8 --threshold 0.8
    dphon docs.jsonl --input-format jsonl --output-format jsonl > matches.jsonl

Help:
    For more information on using this tool, visit the Github repository:
    https://github.com/direct-phonology/dphon
"""

import csv
import logging
import os
import sys
import time
from itertools import combinations
from pathlib import Path
from typing import Dict

import jsonlines
import pkg_resources
import spacy
from docopt import docopt
from rich import traceback
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, SpinnerColumn
from spacy.language import Language
from spacy.tokens import Doc

from . import __version__
from .align import SmithWatermanPhoneticAligner
from .console import MatchHighlighter, console, err_console
from .corpus import CorpusLoader, JsonLinesCorpusLoader, PlaintextCorpusLoader
from .extend import LevenshteinPhoneticExtender
from .g2p import get_sound_table_json
from .match import Match
from .reuse import MatchGraph

# Available log levels: default is WARN, -v is INFO, -vv is DEBUG
LOG_LEVELS = {
    0: "WARN",
    1: "INFO",
    2: "DEBUG",
}


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=__version__)

    # install global logging and exception handlers
    logging.basicConfig(
        level=LOG_LEVELS[args["-v"]],
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=err_console)],
    )
    logging.captureWarnings(True)
    traceback.install()

    # setup pipeline
    nlp = setup(args)

    # setup match highlighting
    console.highlighter = MatchHighlighter(
        g2p=nlp.get_pipe("g2p"), context=int(args["--context"]), gap_char="　"
    )

    # process all texts
    graph = process(nlp, args)
    results = list(graph.matches)
    logging.info(f"{len(results)} total results matching query")

    # sort results by highest total score
    results = sorted(results, key=lambda m: m.weighted_score, reverse=True)

    # output depending on provided option
    if args["--output-format"] == "jsonl":
        with jsonlines.Writer(sys.stdout) as writer:
            for match in results:
                writer.write(match.as_dict())
    elif args["--output-format"] == "csv":
        fieldnames = Match("", "", "", "").as_dict().keys()
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        for match in results:
            writer.writerow(match.as_dict())
    elif args["--output-format"] == "html":
        console.record = True
        with console.capture():
            for doc in graph.docs:
                for group in doc._.groups:
                    console.print(group)
        sys.stdout.write(console.export_html())
    else:
        # use system pager by default; colorize if LESS=R
        with console.pager(styles=os.getenv("LESS", "") == "R"):
            for doc in graph.docs:
                for group in doc._.groups:
                    console.print(group)


def setup(args: Dict) -> Language:
    """Set up the spaCy processing pipeline."""
    # get sound table
    v2_path = pkg_resources.resource_filename(__package__, "data/sound_table_v2.json")
    sound_table = get_sound_table_json(Path(v2_path))

    # add Doc metadata
    if not Doc.has_extension("id"):
        Doc.set_extension("id", default="")
    if not Doc.has_extension("groups"):
        Doc.set_extension("groups", default=[])

    # setup spaCy model
    nlp = spacy.blank("zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
    nlp.add_pipe("g2p", config={"sound_table": sound_table})
    nlp.add_pipe("ngrams", config={"n": int(args["--ngram-order"])})
    nlp.add_pipe("ngram_phonemes_index", name="index")
    logging.info("loaded default spaCy model")
    return nlp


def process(nlp: Language, args: Dict) -> MatchGraph:
    """Run the spaCy processing pipeline."""
    # set up graph and loader
    graph = MatchGraph()
    load_texts: CorpusLoader
    if args["--input-format"] == "jsonl":
        load_texts = JsonLinesCorpusLoader()
    else:
        load_texts = PlaintextCorpusLoader()

    # load and index all documents
    start = time.perf_counter()
    for doc, context in nlp.pipe(load_texts(args["<path>"]), as_tuples=True):
        doc._.id = context["id"]
        graph.add_doc(doc)
        logging.debug(f'indexed doc "{doc._.id}"')
    stop = time.perf_counter() - start
    logging.info(f"indexed {graph.number_of_docs} docs in {stop:.1f}s")

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
        console=err_console,
        transient=True,
    )
    task = progress.add_task("seeding", seed="", total=len(groups))
    start = time.perf_counter()
    with progress:
        for _seed, locations in groups:
            logging.debug(
                f'evaluating seed group "{locations[0].text}", size={len(locations)}'
            )
            progress.update(task, seed=locations[0].text)
            for utxt, vtxt in combinations(locations, 2):
                if utxt.doc._.id != vtxt.doc._.id:  # skip same-doc matches
                    graph.add_match(
                        Match(utxt.doc._.id, vtxt.doc._.id, utxt, vtxt, 1.0)
                    )
            progress.advance(task)
    stop = time.perf_counter() - start
    logging.info(f"seeded {graph.number_of_matches} matches in {stop:.1f}s")

    # limit to seeds with graphic variants if requested
    if not args["--all"]:
        has_variant = nlp.get_pipe("g2p").has_variant
        graph.filter(has_variant)

    # extend all matches
    graph.extend(
        LevenshteinPhoneticExtender(
            threshold=float(args["--threshold"]), len_limit=int(args["--len-limit"])
        )
    )

    # align all matches
    graph.align(SmithWatermanPhoneticAligner(gap_char="　"))

    # filter if requested
    if args["--min-length"]:
        graph.filter(lambda m: len(m) >= int(args["--min-length"]))
    if args["--max-length"]:
        graph.filter(lambda m: len(m) <= int(args["--max-length"]))
    if args["--min-graphic-similarity"]:
        graph.filter(
            lambda m: m.graphic_similarity >= float(args["--min-graphic-similarity"])
        )
    if args["--max-graphic-similarity"]:
        graph.filter(
            lambda m: m.graphic_similarity <= float(args["--max-graphic-similarity"])
        )
    if args["--min-phonetic-similarity"]:
        graph.filter(
            lambda m: m.phonetic_similarity >= float(args["--min-phonetic-similarity"])
        )
    if args["--max-phonetic-similarity"]:
        graph.filter(
            lambda m: m.phonetic_similarity <= float(args["--max-phonetic-similarity"])
        )

    # group all matches
    graph.group()

    # return completed reuse graph
    return graph


if __name__ == "__main__":
    run()
