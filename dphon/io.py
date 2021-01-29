#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes for loading document corpora and passing them to an NLP pipeline."""

import logging
import string
import jsonlines
from abc import ABC, abstractmethod
from collections import OrderedDict
from glob import glob
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from rich.progress import track

# Type for a doc ready to be indexed by spaCy's `nlp.pipe(as_tuples=True)`:
# (content, metadata) where content is a string and metadata is a dict
DocInfo_T = Tuple[str, Dict[str, Any]]

# Translation table for text content, used for fast text preprocessing
# currently converts all whitespace to `None` (i.e. strips it out)
WS_NONE = {k: None for k in list(string.whitespace)}
OC_TEXT = str.maketrans(WS_NONE)


class CorpusLoader(ABC):
    """Abstract base class; implements loading of document corpora."""

    filetype: str

    @abstractmethod
    def __call__(self, paths: Iterable[str]) -> Iterable[DocInfo_T]:
        """Load valid files from all paths, returning contents and metadata.

        Output is a single tuple of (contents, metadata) where "contents" is the
        contents of the file as a string and "metadata" is an arbitrary dict.

        One tuple per doc should be returned for consumption by spaCy's 
        `nlp.pipe(as_tuples=True)`.
        """
        raise NotImplementedError

    def _check(self, paths: Iterable[str]) -> Dict[Path, Any]:
        """Check each of the provided paths and output a list of valid files."""

        # track how many valid files we found, and store valid ones with their
        # metadata for loading
        total = 0
        files = {}

        # try to create a `pathlib.Path` from each expanded path; store it
        # if we succeed so that we can later open the file using it
        for path in paths:
            for file in map(Path, glob(path)):
                if file.is_file() and file.suffix == self.filetype:
                    size = file.stat().st_size
                    files[file] = {"size": size, "id": file.stem}
                    total += 1
                    logging.debug(f"found {file.resolve()}, size={size}B")
                else:
                    logging.warning(
                        f"path {file.resolve()} isn't a {self.filetype} file")

        # if no valid files were found, warn the user. otherwise report the
        # total number of files
        if not total:
            logging.warning("no valid files found")
        else:
            logging.debug(f"found {total} total files")
        return files


class PlaintextCorpusLoader(CorpusLoader):
    """Loads documents stored as one or more .txt files."""

    filetype = ".txt"

    def __call__(self, paths: Iterable[str]) -> Iterable[DocInfo_T]:
        """Load valid files and metadata and yield in order of size, desc.

        All provided paths will be searched, and globs will be expanded, e.g.
        /my/home/dir/*.txt will yield all plaintext files in /my/home/dir/.

        File metadata consists of the file's name, minus extension (the "stem")
        and the file size on disk in bytes.

        Args:
            paths: Iterable of .txt file paths to load.

        Yields:
            A tuple of (contents, metadata) for each valid document found.
        """

        # sort files by size, largest first, to speed up processing by spaCy
        files = self._check(paths)
        files_by_size = OrderedDict(sorted(files.items(),
                                           key=lambda f: f[1]["size"],
                                           reverse=True))

        # open each file and yield contents with metadata as DocInfo_T
        for file, meta in track(files_by_size.items(), description="loading files"):
            with file.open(encoding="utf8") as contents:
                logging.debug(
                    f"loaded doc \"{meta['id']}\" from {file.resolve()}")
                yield contents.read().translate(OC_TEXT), {"id": meta["id"]}


class JsonLinesCorpusLoader(CorpusLoader):
    """Loads documents stored as lines in one or more .jsonl files."""

    filetype = ".jsonl"

    def __call__(self, paths: Iterable[str]) -> Iterable[DocInfo_T]:
        """Parse .jsonl files and yield document text and metadata.

        All provided paths will be searched, and globs will be expanded, e.g.
        /my/home/dir/*.jsonl will yield all jsonlines files in /my/home/dir/.

        Each .jsonl file is assumed to consist of lines where each line is a
        valid JSON object. The only required properties are "id", a unique name
        for the document, and "text", the text of the document itself. All
        other properties will be passed through to spaCy.

        Args:
            paths: Iterable of .jsonl file paths to load.

        Yields:
            A tuple of (contents, metadata) for each valid document found.
        """

        # open each file and yield each line, with all properties except "text"
        # being passed as second element in tuple
        files = self._check(paths)
        for file in track(files.keys(), description="loading files"):
            with jsonlines.open(file) as reader:
                for doc in reader:
                    meta = {k: v for k, v in doc.items() if k != "text"}
                    logging.debug(
                        f"loaded doc \"{doc['id']}\" from {file.resolve()}")
                    yield doc["text"].translate(OC_TEXT), meta
