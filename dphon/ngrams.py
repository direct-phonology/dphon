"""SpaCy pipeline component for generating Token n-grams from Docs."""

import logging
from typing import Iterator

from spacy.language import Language
from spacy.tokens import Doc, Span

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["ngrams"] = lambda nlp, **cfg: Ngrams(nlp, **cfg)


class Ngrams():
    """A spaCy pipeline component for generating Token n-grams from Docs."""

    name = "ngrams"  # will appear in spaCy pipeline
    attr = "ngrams"  # name for getter for ngrams, e.g. doc._.ngrams
    n = 4            # number of tokens per n-gram

    def __init__(self, nlp: Language, n: int = None, name: str = None, attr: str = None):
        """Initialize the n-gram component."""
        # register attribute getter on Doc with customizable name; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        self.attr = attr if attr else self.attr
        Doc.set_extension(self.attr, getter=self.get_doc_ngrams)

        # store other properties if provided
        self.name = name if name else self.name
        self.n = n if n else self.n
        logging.info(
            f"created {self.__class__} as \"{self.name}\" with n={n}, attr=Doc._.{self.attr}")

    def __del__(self) -> None:
        """Unregister the n-gram custom extension."""
        # this is mostly used for tests, to prevent name collisions
        Doc.remove_extension(self.attr)

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def get_doc_ngrams(self, doc: Doc) -> Iterator[Span]:
        """Return an iterator over n-grams in a Doc as Spans."""
        # if empty doc, nothing should happen
        if len(doc) == 0:
            return iter([])
        return (doc[i:i + self.n] for i in range(max(len(doc) - self.n + 1, 1)))
