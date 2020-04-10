"""Loaders are responsible for retrieving corpora and making them available as
Documents for analysis."""

import re
from pathlib import Path
from typing import Generator
from collections.abc import Iterable

from dphon.document import Document

class KanripoLoader(Iterable):
    """Loads a set of Kanripo format (i.e. org-mode) text files from a provided
    directory. Finds all .txt files in the target directory and all nested
    subdirectories."""

    TITLE_RE = re.compile(r"^#\+TITLE: (.+)")
    DATE_RE = re.compile(r"^#\+DATE: (.+)")
    PROP_RE = re.compile(r"^#\+PROPERTY: (\w+)\s+(.+)")

    _id: int

    def __init__(self, directory: str):
        self.paths = Path(directory).glob('**/*.txt')

    def __iter__(self) -> Generator[Document, None, None]:
        self._id = 0
        return (self.file_to_doc(path) for path in self.paths)

    def file_to_doc(self, path: Path) -> Document:
        """Parse a single Kanripo format text file into a Document. Uses the
        org-mode metadata at the top of the file."""

        doc = Document(self._id, "")
        self._id += 1

        with path.open(encoding="utf-8") as file:
            for line in file:
                if line.startswith("#"):
                    continue
                elif line.startswith("<"):
                    continue
                else:
                    doc.text += line

        return doc
