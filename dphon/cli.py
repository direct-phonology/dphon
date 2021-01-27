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

import glob
import logging
import time
from collections import OrderedDict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import spacy
from docopt import docopt
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install
from spacy.language import Language
from spacy.tokens import Doc

from dphon import __version__
from dphon.align import SmithWatermanPhoneticAligner
from dphon.extend import LevenshteinPhoneticExtender
from dphon.fmt import DEFAULT_THEME, SimpleFormatter
from dphon.index import Index
from dphon.match import Match
from dphon.ngrams import Ngrams
from dphon.phonemes import Phonemes, get_sound_table_json
from dphon.reuse import MatchGraph
from dphon.util import progress

# install logging and exception handlers
logging.basicConfig(level="DEBUG", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])
install()


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
    format = SimpleFormatter(gap_char="　", nl_char="＄")

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
    Doc.set_extension("title", default="")

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
    with progress:
        docs_task = progress.add_task("indexing documents")
        all_start = time.perf_counter()
        start = all_start
        for doc, context in nlp.pipe(load_texts(args["<path>"]), as_tuples=True):
            doc._.title = context["title"]
            graph.add_doc(context["title"], doc)
            progress.update(docs_task, advance=1)
            finish = time.perf_counter() - start
            logging.debug(
                f"indexed doc \"{context['title']}\" in {finish:.3f}s")
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
                    Match(utxt.doc._.title, vtxt.doc._.title, utxt, vtxt, 1.0))

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
    Doc.remove_extension("title")

    # iterate over all pipeline components and call teardown() if it exists
    for _name, component in nlp.pipeline:
        if hasattr(component, "teardown"):
            component.teardown()


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
        newlines: Whether to preserve newlines in text. False by default.

    Yields:
        A tuple of (text, metadata) for the next document found in all paths.
    """

    # check all provided paths and get their filesize, if valid
    logging.debug("checking paths...")
    total = 0
    files: Dict[str, Tuple[Path, int]] = {}
    for path in paths:
        for file in map(Path, glob.glob(path)):
            if file.is_file():
                files[file.stem] = file, file.stat().st_size
                total += 1
                logging.debug(f"found \"{file}\", size={file.stat().st_size}")
            else:
                logging.warn(f"path \"{file}\" isn't a file")
    logging.debug(f"found {total} total files")

    # sort files by size, longest first, and yield with filename info
    by_size = OrderedDict(
        sorted(files.items(), key=lambda f: f[1][1], reverse=True))
    progress.add_task("indexing")
    for name, attrs in by_size.items():
        with attrs[0].open(encoding="utf8") as contents:
            logging.debug(f"loaded doc \"{name}\" with size={attrs[1]}B")
            yield (contents.read(), {"title": name})


if __name__ == "__main__":
    run()
