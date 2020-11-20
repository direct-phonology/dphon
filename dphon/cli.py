"""dphon - a tool for old chinese phonetic analysis
 
Usage:
    dphon <path>... [options]
    dphon -h | --help
    dphon --version
 
Options:
    -h --help                   Show this help.
    -v --version                Show program version.
    --variants-only             Limit to matches with true graphic variation.
    --keep-newlines             Preserve newlines in output.
    -a --all                    Include matches with no variation at all.
    -o <file> --output <file>   Write output to a file.
    --min <min>                 Limit to matches with length >= min.
    --max <max>                 Limit to matches with length <= max.
 
Examples:
    dphon texts/ --min 8
    dphon 老子甲.txt 老子丙.txt 老子乙.txt --output matches.txt
    dphon 周南.txt 鹿鳴之什.txt --variants-only
 
Help:
    For more information on using this tool, please visit the Github repository:
    https://github.com/direct-phonology/direct
"""

import logging
import time
from itertools import combinations, filterfalse
from pathlib import Path
from sys import stdout
from typing import Any, Dict, Iterator, List, Tuple

import spacy
from docopt import docopt
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress
from rich.traceback import install
from spacy.language import Language
from spacy.tokens import Doc

from dphon import __version__
from dphon.aligner import SmithWatermanAligner
from dphon.extender import LevenshteinPhoneticExtender
from dphon.index import Index
from dphon.fmt import SimpleFormatter
from dphon.match import Match
from dphon.ngrams import Ngrams
from dphon.phonemes import Phonemes, get_sound_table_json
from dphon.util import extend_matches

# install logging and exception handlers
logging.basicConfig(level="DEBUG", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])
install()


def run() -> None:
    """CLI entrypoint."""
    args = docopt(__doc__, version=__version__)

    # setup pipeline
    nlp = setup()

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
    results = process(nlp, progress, args)
    logging.info(f"{len(results)} total results matching query")

    # write to a file if requested; otherwise write to stdout
    format = SimpleFormatter(gap_char="　", nl_char="＄")
    fmt_results = [format(match) for match in results]
    if args["--output"]:
        with open(args["--output"], mode="w", encoding="utf8") as file:
            for match in fmt_results:
                file.write(match + "\n\n")
        logging.info(f"wrote {args['--output']}")
    else:
        for match in fmt_results:
            stdout.buffer.write((match + "\n\n").encode("utf8"))

    # teardown pipeline
    teardown(nlp)


def setup() -> Language:
    """Set up the spaCy proecssing pipeline."""
    # get sound table
    sound_table = get_sound_table_json(Path("./dphon/data/sound_table.json"))

    # add Doc metadata
    Doc.set_extension("title", default="")

    # setup spaCy model
    nlp = spacy.blank("zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
    nlp.add_pipe(Phonemes(nlp, sound_table=sound_table), first=True)
    nlp.add_pipe(Ngrams(nlp, n=4), after="phonemes")
    nlp.add_pipe(Index(nlp, val_fn=lambda doc: doc._.ngrams,
                       filter_fn=lambda ngram: ngram.text.isalpha(),
                       key_fn=lambda ngram: "".join(ngram._.phonemes)))
    logging.info("loaded default spaCy model")
    return nlp


def process(nlp: Language, progress: Progress, args: Dict) -> List[Match]:
    """Run the spaCy processing pipeline."""

    newlines = args.get("--keep-newlines", False)
    with progress:
        docs_task = progress.add_task("indexing documents")
        all_start = time.perf_counter()
        start = all_start
        for doc, context in nlp.pipe(load_texts(args["<path>"], newlines=newlines), as_tuples=True):
            doc._.title = context["title"]
            progress.update(docs_task, advance=1)
            finish = time.perf_counter() - start
            logging.debug(f"processed doc {context['title']} in {finish:.3f}s")
            start = time.perf_counter()
        progress.remove_task(docs_task)
    all_finish = time.perf_counter() - all_start
    logging.info(f"completed spaCy pipeline in {all_finish:.3f}s")

    # drop all ngrams from index that only occur once
    groups = list(nlp.get_pipe("index").filter(
        lambda entry: len(entry[1]) > 1))

    # create initial pairwise matches from seed groups
    matches: List[Match] = []
    with progress:
        matches_task = progress.add_task(
            "generating matches", total=len(groups))
        start = time.perf_counter()
        for seed, locations in groups:
            for left, right in combinations(locations, 2):
                if left.doc != right.doc:  # skip same-doc matches
                    matches.append(Match(left, right))
            progress.update(matches_task, advance=1)
        progress.remove_task(matches_task)
    finish = time.perf_counter() - start
    logging.info(f"created {len(matches):,} initial matches in {finish:.3f}s")

    # query match groups from the index and extend them
    extender = LevenshteinPhoneticExtender(threshold=0.8, len_limit=50)
    with progress:
        extend_task = progress.add_task(
            "extending matches", total=len(matches))
        start = time.perf_counter()
        results = extend_matches(matches, extender)
        progress.remove_task(extend_task)
    finish = time.perf_counter() - start
    logging.info(f"extended {len(results):,} matches in {finish:.3f}s")

    # align all matches
    aligner = SmithWatermanAligner()
    aligned_results = []
    with progress:
        align_task = progress.add_task("aligning matches", total=len(results))
        start = time.perf_counter()
        for match in results:
            aligned_results.append(aligner.align(match))
            progress.update(align_task, advance=1)
        progress.remove_task(align_task)
    finish = time.perf_counter() - start
    logging.info(f"aligned {len(aligned_results):,} matches in {finish:.3f}s")
    results = aligned_results

    # limit via min and max lengths if requested
    if args.get("--min", None):
        results = list(filterfalse(lambda m: len(m) <
                                   int(args["--min"]), results))
    if args.get("--max", None):
        results = list(filterfalse(lambda m: len(m) >
                                   int(args["--max"]), results))

    # unless --all was requested, drop matches that are equal after normalization
    if not args.get("--all", None):
        results = list(filterfalse(lambda m: m.is_norm_eq, results))

    # TODO drop matches with no graphic variation if requested
    if args.get("--variants-only", None):
        pass

    return results


def teardown(nlp: Language) -> None:
    """Unregister spaCy extensions to prevent name collisions."""
    Doc.remove_extension("title")

    # iterate over all pipeline components and call teardown() if it exists
    for _name, component in nlp.pipeline:
        if hasattr(component, "teardown"):
            component.teardown()


def load_texts(paths: List[str], newlines: bool = False) -> Iterator[Tuple[str, Dict[str, Any]]]:
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

    logging.debug(f"preserve newlines: {newlines}")

    total = 0
    for _path in paths:
        path = Path(_path)
        if path.is_file():
            with path.open(encoding="utf8") as contents:
                file_contents = contents.read()
            if not newlines:
                file_contents = file_contents.replace("\n", "")
            logging.debug(f"loaded text {path.stem}")
            total += 1
            yield (file_contents, {"title": path.stem})
        elif path.is_dir():
            for file in path.glob("**/*.txt"):
                with file.open(encoding="utf8") as contents:
                    file_contents = contents.read()
                if not newlines:
                    file_contents = file_contents.replace("\n", "")
                logging.debug(f"loaded text {file.stem}")
                total += 1
                yield (file_contents, {"title": file.stem})
    logging.info(f"loaded {total} total texts from filesystem")
