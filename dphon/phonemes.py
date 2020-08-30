"""SpaCy pipeline component for converting Tokens to phonetic equivalents."""

import logging
from typing import Iterator, Tuple, Dict, Optional

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

# register the pipeline component factory; see:
# https://spacy.io/usage/processing-pipelines#custom-components-factories
Language.factories["phonemes"] = lambda nlp, **cfg: Phonemes(nlp, **cfg)

# private use unicode char that represents phonemes for OOV tokens
OOV_PHONEMES = "\ue000"

# types for sound tables: map a string to a tuple of syllable phonemes
Phonemes_T = Tuple[Optional[str], ...]
SoundTable_T = Dict[str, Phonemes_T]

class Phonemes():
    """A spaCy pipeline component that enables converting Tokens to phonemes."""

    def __init__(self, nlp: Language, name: str, sound_table: SoundTable_T, syllable_parts: int, attr: str = "phonemes"):
        """Initialize the phonemes component."""
        # register attribute getters with customizable names; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        Doc.set_extension(attr, getter=self.get_doc_phonemes)
        Span.set_extension(attr, getter=self.get_span_phonemes)
        Token.set_extension(attr, getter=self.get_token_phonemes)
        Token.set_extension("is_oov", getter=self.is_token_oov)

        # store the name that will appear in the pipeline
        self.name = name if name else "phonemes"
        self.syllable_parts = syllable_parts
        self.empty_phonemes = tuple(None for part in range(self.syllable_parts))

        # store the sound table in the vocab's Lookups using the attr name
        self.table = nlp.vocab.lookups.add_table(attr, sound_table)
        logging.info(f"created {self.__class__} as {self.name}")

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def is_token_oov(self, token: Token) -> bool:
        """Check if a token has a phonetic entry in the sound table."""
        return token.is_alpha and token.text not in self.table

    def get_doc_phonemes(self, doc: Doc) -> Iterator[str]:
        """Return a flattened iterator over all phonemes in a Doc."""
        for token in doc:
            for phoneme in self.get_token_phonemes(token):
                if phoneme:
                    yield phoneme

    def get_span_phonemes(self, span: Span) -> Iterator[str]:
        """Return a flattened iterator over all phonemes in a Span."""
        for token in span:
            for phoneme in self.get_token_phonemes(token):
                if phoneme:
                    yield phoneme

    def get_token_phonemes(self, token: Token) -> Phonemes_T:
        """Return a Token's phonemes as an n-tuple.

        - If a Token is non-alphabetic, all elements of the tuple will be None.
        - If a Token is not in the sound table, all elements of the tuple will
        use a special marker token (OOV_PHONEMES).
        - If some parts of the syllable are not present, their corresponding
        elements in the tuple will be None.
        """

        if not token.is_alpha:
            return self.empty_phonemes
        elif token.text not in self.table:
            # logging.warn(f"no entry for token in sound table: {token.text}")
            return (OOV_PHONEMES,)
        else:
            return self.table[token.text]
