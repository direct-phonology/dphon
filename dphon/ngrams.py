#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
    n: int           # number of tokens per n-gram (order)

    def __init__(self, nlp: Language, n: int, name: str = None, attr: str = None):
        """Initialize the n-gram component."""
        # register attribute getter on Doc with customizable name; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        self.attr = attr if attr else self.attr
        Doc.set_extension(self.attr, getter=self.get_doc_ngrams)

        # store other properties
        self.n = n
        self.name = name if name else self.name
        logging.info(f"using {self.__class__}\" with n={self.n}, name={self.name}")

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def teardown(self) -> None:
        """Unregister the attribute to prevent collisions."""
        Doc.remove_extension(self.attr)

    def get_doc_ngrams(self, doc: Doc) -> Iterator[Span]:
        """Return an iterator over n-grams in a Doc as Spans."""
        # if empty doc, nothing should happen
        if len(doc) == 0:
            return iter([])
        return (doc[i:i + self.n] for i in range(max(len(doc) - self.n + 1, 1)))
