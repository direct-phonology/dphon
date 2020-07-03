"""Loaders are responsible for retrieving corpora and making them available as
Documents for analysis."""

import re
from pathlib import Path
from typing import Generator, Dict
from abc import ABC

from dphon.document import Document

class Loader(ABC):

    _id: int
    _docs: Dict[int, Document]

    def __init__(self):
        self._id = 0
        self._docs = {}

    def docs(self) -> Generator[Document, None, None]:
        """Return a generator of documents in this corpus."""
        return (doc for (doc_id, doc) in self._docs.items())

    def get(self, doc_id: int) -> Document:
        """Fetch a single Document in the corpus via its ID."""
        return self._docs[doc_id]

class SimpleLoader(Loader):
    """Loads all plaintext files in the current directory. Does not examine
    subdirectories."""

    def __init__(self, directory: str):
        super().__init__()

        paths = Path(directory).glob('*.txt')
        for path in paths:
            doc = self.file_to_doc(path)
            self._docs[doc.id] = doc

    def file_to_doc(self, path: Path) -> Document:
        doc = Document(self._id, "")
        self._id += 1

        doc.title = path.stem

        with path.open(encoding="utf-8") as file:
            for line in file:
                doc.text += line

        return doc

class KanripoLoader():
    """Loads a set of Kanripo format (i.e. org-mode) text files from a provided
    directory. Finds all .txt files in the target directory and all nested
    subdirectories."""

    TITLE_RE = re.compile(r"^#\+TITLE: (.+)")
    DATE_RE = re.compile(r"^#\+DATE: (.+)")
    PROP_RE = re.compile(r"^#\+PROPERTY: (\w+)\s+(.+)")

    _id: int
    _docs: Dict[int, Document]

    def __init__(self, directory: str):
        """Find all .txt files in the provided path and eagerly parse them as
        Documents, storing for later access."""

        self._id = 0
        self._docs = {}

        paths = Path(directory).glob('**/*.txt')
        for path in paths:
            doc = self.file_to_doc(path)
            self._docs[doc.id] = doc

    def docs(self) -> Generator[Document, None, None]:
        """Return a generator of documents in this corpus."""

        return (doc for (doc_id, doc) in self._docs.items())

    def get(self, doc_id: int) -> Document:
        """Fetch a single Document in the corpus via its ID."""
        return self._docs[doc_id]

    def file_to_doc(self, path: Path) -> Document:
        """Parse a single Kanripo format text file into a Document. Uses the
        org-mode metadata at the top of the file."""

        doc = Document(self._id, "")
        self._id += 1

        with path.open(encoding="utf-8") as file:
            for line in file:
                title = self.TITLE_RE.match(line)
                if title:
                    doc.title = title.group(1)
                elif line.startswith("<"):
                    continue
                else:
                    doc.text += line

        return doc
