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

    -o <PATH>, --output-file <PATH>
        Set output filename. By default, output is sent to the terminal. The
        output format is determined by the file extension. Supported formats
        are JSON lines (jsonl), CSV (csv), and HTML (html).

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
    --within-doc               [default: False]
        Allow matches within the same document. Overlapping spans are
        automatically excluded.

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

    --focus <ID>
        One-to-many mode: only find matches where at least one span is from
        the document whose ID starts with ID. Results are ordered by position
        in the focus text.

Display options:
    --transcribe-context        [default: False]
        Include phonemic transcription for context tokens as well as matched
        tokens.
    -g, --group                [default: False]
        Group matches by shared text. By default, matches are displayed as
        individual pairs of similar sequences.

Examples:
    dphon texts/*.txt > matches.txt
    dphon file1.txt file2.txt --ngram-order 8 --threshold 0.8 --group
    dphon docs.jsonl --input-format jsonl --output-format jsonl > matches.jsonl

Help:
    For more information on using this tool, visit the Github repository:
    https://github.com/direct-phonology/dphon
"""

import csv
import logging
import os
import time
from itertools import combinations
from pathlib import Path
from typing import Dict, List
from importlib.metadata import version as pkg_version
from importlib import resources as pkg_resources

import jsonlines
import spacy
from docopt import docopt
from rich import traceback
from rich.logging import RichHandler
from rich.padding import Padding
from rich.progress import BarColumn, Progress, SpinnerColumn
from spacy.language import Language
from spacy.tokens import Doc

from .align import SmithWatermanPhoneticAligner
from .console import MatchHighlighter, console, err_console
from .corpus import CorpusLoader, JsonLinesCorpusLoader, PlaintextCorpusLoader
from .extend import LevenshteinPhoneticExtender
from .g2p import get_sound_table_json
from .match import Match
from .reuse import MatchGraph, MatchGroup

# Available log levels: default is WARN, -v is INFO, -vv is DEBUG
LOG_LEVELS = {
    0: "WARN",
    1: "INFO",
    2: "DEBUG",
}


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=pkg_version("dphon"))

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
        g2p=nlp.get_pipe("g2p"), context=int(args["--context"]), gap_char="　", transcribe_context=args["--transcribe-context"]
    )

    # process all texts
    graph = process(nlp, args)

    # check if we're outputting to a file and find out the format
    output_format = None
    if args["--output-file"]:
        output_path = Path(args["--output-file"])
        output_format = output_path.suffix.lstrip(".").lower()
        if output_format not in ["jsonl", "csv", "html"]:
            raise ValueError(f"unsupported output format: {output_format}")

    # if requested output match groups, otherwise output matches
    results: List[MatchGroup] | List[Match] = []
    if args["--group"]:
        graph.group()
        results = graph.groups
    else:
        results = list(graph.matches)

    # sort results
    if args["--focus"]:
        # order by position in source text
        source = args["--focus"]
        def source_position(match):
            if match.u.startswith(source):
                return (match.u, match.utxt.start)
            else:
                return (match.v, match.vtxt.start)
        results= sorted(results, key=source_position)
    else:
        # sort results by highest weighted score
        results = sorted(results, key=lambda result: result.weighted_score, reverse=True)

    # normalize so focus is always the first (u) position
    if args["--focus"]:
        normalized = []
        for match in results:
            if match.v.startswith(args["--focus"]) and not match.u.startswith(args["--focus"]):
                normalized.append(Match(match.v, match.u, match.vtxt, match.utxt,
                                       match.weight, match.av, match.au))
            else:
                normalized.append(match)
        results = normalized

    # output depending on provided option
    if output_format == "jsonl":
         with open(output_path, "w") as f, jsonlines.Writer(f) as writer:
            for result in results:
                writer.write(result.as_dict())
    elif output_format == "csv":
        fieldnames = results[0].as_dict().keys()
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(result.as_dict())
    elif output_format == "html":
        console.record = True
        for result in results:
            console.print(Padding(result, (0, 0, 1, 0)))
        console.save_html(output_path)
    else:
        # use system pager by default; colorize if LESS=R
        with console.pager(styles=os.getenv("LESS", "") == "R"):
            for result in results:
                console.print(Padding(result, (0, 0, 1, 0)))


def setup(args: Dict) -> Language:
    """Set up the spaCy processing pipeline."""
    # get sound table
    v2_path = pkg_resources.files(__package__).joinpath("data/sound_table_v2.json")
    sound_table = get_sound_table_json(v2_path)

    # add Doc metadata
    if not Doc.has_extension("id"):
        Doc.set_extension("id", default="")

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
                # source filter: skip pairs where neither doc is the source
                if args["--focus"]:
                    u_is_source = utxt.doc._.id.startswith(args["--focus"])
                    v_is_source = vtxt.doc._.id.startswith(args["--focus"])
                    if not u_is_source and not v_is_source:
                        continue
                if utxt.doc._.id != vtxt.doc._.id or (args["--within-doc"] and (utxt.end <= vtxt.start or vtxt.end <= utxt.start)):
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
    
    # remove same-doc matches that overlap after extension
    if args["--within-doc"]:
        def no_overlap(match: Match) -> bool:
            if match.u != match.v:
                return True
            return match.utxt.end <= match.vtxt.start or match.vtxt.end <= match.utxt.start
        graph.filter(no_overlap)

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

    # return completed reuse graph
    return graph


if __name__ == "__main__":
    run()
