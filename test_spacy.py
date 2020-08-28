import csv
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import spacy
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table as RichTable
from spacy.lang.zh import ChineseDefaults
from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

from dphon.index import Index
from dphon.ngrams import Ngrams
from dphon.phonemes import OOV_PHONEMES, Phonemes

ChineseDefaults.use_jieba = False

logging.basicConfig(level="INFO", format="%(message)s",
                    datefmt="[%X]", handlers=[RichHandler()])


def get_texts(directory: Path) -> List[Tuple[str, Dict[str, Any]]]:
    # load all texts and format with context
    texts = []
    for file in directory.glob("**/*.txt"):
        with file.open() as contents:
            text = contents.read()
            texts.append((text, {"title": file.stem, "len": len(text)}))
    logging.info(f"loaded {len(texts)} texts")
    # return in order with largest texts first, to speed up processing
    return sorted(texts, key=lambda t: t[1]["len"], reverse=True)


if __name__ == "__main__":
    # load texts and sound table
    texts = get_texts(Path("/Users/nbudak/src/ect-krp/txt"))
    with open("./dphon/data/sound_table_zhuyin.json") as file:
        sound_table: dict = json.loads(file.read())
    logging.info("sound table loaded")

    # setup pipeline
    nlp = spacy.blank("zh")
    logging.info("spaCy pipeline created")

    ngrams = Ngrams(nlp, n=4)
    phonemes = Phonemes(nlp, sound_table=sound_table)
    index = Index(nlp, "phonemes", lambda token: token._.phonemes)
    oov = Index(nlp, "oov", lambda token: token.text if token._.phonemes == OOV_PHONEMES else None)

    nlp.add_pipe(phonemes, first=True)
    nlp.add_pipe(ngrams, after="phonemes")
    nlp.add_pipe(index)
    nlp.add_pipe(oov)
    
    logging.info("spaCy pipeline setup complete")

    # store output statistics & visualize progress
    stats: Dict[str, str] = {}
    total_len = sum([context["len"] for text, context in texts])
    progress = Progress(
        "{task.elapsed:.0f}s",
        BarColumn(bar_width=None),
        "{task.percentage:>3.1f}%"
    )

    # process all texts
    with progress:
        docs_task = progress.add_task("docs", total=total_len)
        all_start = time.time()
        start = time.time()
        for doc, context in nlp.pipe(texts, as_tuples=True):
            progress.update(docs_task, advance=context["len"])
            finish = time.time() - start
            logging.debug(f"processed doc {context['title']} in {finish:.3f}s")
            start = time.time()
        all_finish = time.time() - all_start
        logging.info(f"pipeline completed in {all_finish:.3f}s")

    logging.info(f"{len(index)} unique tokens were encountered {index.token_count} times")
    logging.info(f"{len(oov)} unique out-of-vocab tokens were encountered {oov.token_count} times")

    top10 = list(sorted(oov, reverse=True, key=lambda entry: len(entry[1])))[:10]
    total_top10 = sum([len(v) for (k, v) in top10])
    percentage = total_top10 / oov.token_count * 100

    logging.info(f"top 10 out-of-vocab tokens comprise {total_top10}; {percentage:>3.1f}% of total")

    console = Console()
    table = RichTable(title="top 10 out-of-vocab tokens")
    table.add_column("token")
    table.add_column("count", justify="right")
    for k, v in top10:
        table.add_row(nlp.vocab[k].text, f"{len(v)}")
    console.print(table)

    # query match groups from the index and extend them, keeping track of the
    # extent of existing matches so as not to duplicate work

    # build a reuse graph using the extended matches
