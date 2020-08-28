"""SpaCy pipeline component for converting Tokens to phonetic equivalents."""

import logging
from typing import Iterator

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["phonemes"] = lambda nlp, **cfg: Phonemes(nlp, **cfg)

# private use unicode char that represents phonemes for OOV tokens
OOV_PHONEMES = "\ue000"


class Phonemes():
    """A spaCy pipeline component that enables converting Tokens to phonemes."""

    name = "phonemes"  # component name, will show up in the pipeline
    table: Table       # sound lookup table, stored in lookups

    def __init__(self, nlp: Language, sound_table: dict, attr: str = "phonemes"):
        """Initialize the phonemes component."""
        logging.info("initializing phonemes pipeline component")

        # register attribute getters with customizable names; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        Doc.set_extension(attr, getter=self.get_doc_phonemes)
        Span.set_extension(attr, getter=self.get_span_phonemes)
        Token.set_extension(attr, getter=self.get_token_phonemes)

        # store the sound table in the vocab's Lookups using the attr name
        self.table = nlp.vocab.lookups.add_table(attr, sound_table)
        logging.info(f"sound table added to vocab as lookups.{attr}")

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def get_doc_phonemes(self, doc: Doc) -> Iterator[str]:
        """Return an iterator over the phonemes of each Token in a Doc."""
        for token in doc:
            phonemes = self.get_token_phonemes(token)
            if phonemes != "":
                yield phonemes

    def get_span_phonemes(self, span: Span) -> Iterator[str]:
        """Return an iterator over the phonemes of each Token in a Span."""
        for token in span:
            phonemes = self.get_token_phonemes(token)
            if phonemes != "":
                yield phonemes

    def get_token_phonemes(self, token: Token) -> str:
        """Look up a Token in the sound table and return its phonemes.

        If the Token is non-alphabetic, return an empty string. If the Token has 
        no corresponding entry in the sound table, return a special marker that
        indicates an out-of-vocabulary entry."""

        if not token.is_alpha:
            return ""
        if token.text not in self.table:
            # logging.warn(f"no entry for token in sound table: {token.text}")
            return OOV_PHONEMES
        return self.table[token.text]
