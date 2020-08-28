"""SpaCy pipeline component generating n-grams from Docs."""

import logging
from typing import Iterator

from spacy.language import Language
from spacy.tokens import Doc, Span

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["ngrams"] = lambda nlp, **cfg: Ngrams(nlp, **cfg)


class Ngrams():
    """A spaCy pipeline component that enables generating n-grams from Docs."""

    name = "ngrams"  # component name, will show up in the pipeline

    def __init__(self, nlp: Language, n: int, attr: str = "ngrams"):
        """Initialize the n-gram component."""
        logging.info(f"initializing n-grams pipeline component with n={n}")

        # register attribute getter on Doc with customizable name; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        Doc.set_extension(attr, getter=self.get_doc_ngrams)

        # store value for "n", i.e. size of n-grams
        self.n = n

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def get_doc_ngrams(self, doc: Doc) -> Iterator[Span]:
        """Return an iterator over n-grams in a Doc as Spans."""
        return (doc[i:i + self.n] for i in range(len(doc) - self.n))
