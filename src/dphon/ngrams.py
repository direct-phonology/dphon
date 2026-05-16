#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SpaCy pipeline component for generating Token n-grams from Docs."""

import logging
from typing import Iterator

from spacy.language import Language
from spacy.tokens import Doc, Span


class Ngrams:
    """A spaCy pipeline component for generating Token n-grams from Docs."""

    n: int  # number of tokens per n-gram (order)

    def __init__(self, nlp: Language, n: int):
        """Initialize the n-gram component."""
        self.n = n
        if not Doc.has_extension("ngrams"):
            Doc.set_extension("ngrams", getter=self.get_doc_ngrams)
        logging.info(f'using {self.__class__}" with n={self.n}')

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def get_doc_ngrams(self, doc: Doc) -> Iterator[Span]:
        """Return an iterator over n-grams in a Doc as Spans."""
        # if empty doc, nothing should happen
        if len(doc) == 0:
            return iter([])
        return (doc[i : i + self.n] for i in range(max(len(doc) - self.n + 1, 1)))


@Language.factory("ngrams")
def create_ngrams(nlp: Language, name: str, n: int) -> Ngrams:
    return Ngrams(nlp, n)
