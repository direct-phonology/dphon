"""dphon - a tool for old chinese phonetic analysis
 
Usage:
    dphon <path>... [--n=<n>] [--output=<file>] [--variants-only]
    dphon -h | --help
    dphon --version
 
Options:
    -h --help           Show this screen.
    --version           Show program version.
    --variants-only     Limit to matches with graphic variation.
    --n=<n>             Limit to matches with length >= n [default: 3].
 
Examples:
    dphon ./texts --n=8
    dphon 老子甲.txt 老子丙.txt 老子乙.txt --output=matches.txt
    dphon 周南.txt 鹿鳴之什.txt --variants-only
 
Help:
    For more information on using this tool, please visit the Github repository:
    https://github.com/direct-phonology/direct
"""

import logging
import time
from itertools import combinations, filterfalse
from pathlib import Path
from sys import stdin, stdout
from typing import Any, Dict, Iterator, List, Tuple

import spacy
from docopt import docopt
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, TextColumn
from rich.traceback import install
from spacy.lang.zh import ChineseDefaults
from spacy.tokens import Doc

from dphon import __version__
from dphon.index import Index
from dphon.match import Match
from dphon.ngrams import Ngrams
from dphon.phonemes import Phonemes, get_sound_table_json
from dphon.extender import LevenshteinPhoneticExtender
from dphon.util import extend_matches

# turn off default settings for spacy's chinese model
ChineseDefaults.use_jieba = False

# install logging and exception handlers
logging.basicConfig(level="DEBUG", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])
install()


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=__version__)

    # get sound table
    sound_table = get_sound_table_json(Path("./dphon/data/sound_table.json"))

    # add Doc metadata
    Doc.set_extension("title", default="")

    # setup spaCy model
    nlp = spacy.blank("zh")
    nlp.add_pipe(Phonemes(nlp, sound_table=sound_table), first=True)
    nlp.add_pipe(Ngrams(nlp, n=4), after="phonemes")
    nlp.add_pipe(Index(nlp, val_fn=lambda doc: doc._.ngrams,
                       filter_fn=lambda ngram: ngram.text.isalpha(),
                       key_fn=lambda ngram: "".join(ngram._.phonemes)))
    logging.info("loaded default spaCy model")

    # create progress visualization
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
        docs_task = progress.add_task("indexing documents")
        all_start = time.perf_counter()
        start = all_start
        for doc, context in nlp.pipe(load_texts(args["<path>"]), as_tuples=True):
            doc._.title = context["title"]
            progress.update(docs_task, advance=1)
            finish = time.perf_counter() - start
            logging.debug(f"processed doc {context['title']} in {finish:.3f}s")
            start = time.perf_counter()
        progress.remove_task(docs_task)
    all_finish = time.perf_counter() - all_start
    logging.info(f"completed spaCy pipeline in {all_finish:.3f}s")

    # drop all ngrams from index that only occur once
    groups = list(nlp.get_pipe("index").filter(lambda entry: len(entry[1]) > 1))

    # create initial pairwise matches from seed groups
    matches: List[Match] = []
    with progress:
        matches_task = progress.add_task("generating matches", total=len(groups))
        start = time.perf_counter()
        for seed, locations in groups:
            for left, right in combinations(locations, 2):
                if left.doc != right.doc: # skip same-doc matches
                    matches.append(Match(left, right)) # FIXME ignore those without graphic var?
            progress.update(matches_task, advance=1)
        progress.remove_task(matches_task)
    finish = time.perf_counter() - start
    logging.info(f"created {len(matches):,} initial matches in {finish:.3f}s")

    # query match groups from the index and extend them
    extender = LevenshteinPhoneticExtender(threshold=0.8, len_limit=50)
    with progress:
        extend_task = progress.add_task("extending matches", total=len(matches))
        start = time.perf_counter()
        new_matches = extend_matches(matches, extender)
        progress.remove_task(extend_task)
    finish = time.perf_counter() - start
    logging.info(f"extended {len(new_matches):,} matches in {finish:.3f}s")

    # drop matches with length < n if requested
    if args["--n"]:
        new_matches = list(filterfalse(lambda m: len(m) < int(args["--n"]), new_matches))

    # drop matches with no variation if requested
    if args["--variants-only"]:
        new_matches = list(filterfalse(lambda m: m.left.text == m.right.text, new_matches))

    # write to a file if requested; otherwise write to stdout
    if args["--output"]:
        with open(args["--output"], mode="w", encoding="utf-8") as file:
            for match in new_matches:
                file.write(f"{match}\n")
    else:
        for match in new_matches:
            stdout.buffer.write(f"{match}\n".encode("utf-8"))


def load_texts(paths: List[str]) -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Load texts from all provided file or directory paths.

    All provided paths will be searched. If the path is a text file its contents
    will be loaded; if it is a directory all text files within will be loaded.

    The output is a list of tuples containing the document text and a context
    dict that maps arbitrary string keys to values; this will be passed to
    spaCy and can be used to assign metadata to documents. Currently, the only
    piece of metadata set is "title", which is mapped to the text's filename.

    Args:
        paths: List of file or directory paths to search.

    Yields:
        A tuple of (text, metadata) for the next document found in all paths.
    """

    total = 0
    for _path in paths:
        path = Path(_path)
        if path.is_file():
            with path.open() as contents:
                file_contents = contents.read()
            logging.debug(f"loaded text {path.stem}")
            total += 1
            yield (file_contents, {"title": path.stem})
        elif path.is_dir():
            for file in path.glob("**/*.txt"):
                with file.open() as contents:
                    file_contents = contents.read()
                logging.debug(f"loaded text {file.stem}")
                total += 1
                yield (file_contents, {"title": file.stem})
    logging.info(f"loaded {total} total texts from filesystem")
