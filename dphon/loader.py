"""Loaders are responsible for retrieving corpora and making them available as
Documents for analysis."""

import re
from pathlib import Path
from typing import Generator, List
from abc import ABC

from dphon.document import Document

class Loader(ABC):

    _id: int
    _docs: List[Document]

    def __init__(self) -> None:
        self._id = 0
        self._docs = []

    def __len__(self) -> int:
        """Number of documents in this corpus."""
        return len(self._docs)

    def docs(self) -> Generator[Document, None, None]:
        """Return a generator of documents in this corpus."""
        return (doc for doc in self._docs)

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
            self._docs.append(doc)

    def file_to_doc(self, path: Path) -> Document:
        doc = Document(self._id, "")
        self._id += 1

        doc.title = path.stem

        with path.open(encoding="utf-8") as file:
            for line in file:
                doc.text += line

        return doc

class KanripoLoader(Loader):
    """Loads a set of Kanripo format (i.e. org-mode) text files from a provided
    directory. Finds all .txt files in the target directory and all nested
    subdirectories."""

    TITLE_RE = re.compile(r"^#\+TITLE: (.+)")
    DATE_RE = re.compile(r"^#\+DATE: (.+)")
    PROP_RE = re.compile(r"^#\+PROPERTY: (\w+)\s+(.+)")

    _clean: bool

    def __init__(self, directory: str, clean: bool) -> None:
        """Find all .txt files in the provided path and eagerly parse them as
        Documents, storing for later access."""
        
        super().__init__()
        self._clean = clean

        paths = Path(directory).glob('**/*.txt')
        for path in paths:
            doc = self.file_to_doc(path)
            self._docs.append(doc)

    @staticmethod
    def clean(string: str) -> str:
        """Remove punctuation and whitespace from text."""
        return "".join(c for c in string if c.isalpha() and not c.isascii())

    def file_to_doc(self, path: Path) -> Document:
        """Parse a single Kanripo format text file into a Document."""

        doc = Document(self._id, "")
        self._id += 1

        with path.open(encoding="utf-8") as file:
            for line in file:
                title = self.TITLE_RE.match(line)
                prop = self.PROP_RE.match(line)
                if title:
                    doc.title = title.group(1)
                elif prop:
                    doc.meta[prop.group(1)] = prop.group(2)
                elif line.startswith("<"):
                    continue
                else:
                    if self._clean:
                        line = self.clean(line)
                    doc.text += line

        return doc
