#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SpaCy pipeline components for converting graphemes to phonemes."""

import json
import logging
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Optional, Tuple

from spacy.language import Language
from spacy.lookups import Lookups, Table
from spacy.tokens import Doc, Span, Token

from dphon.match import Match

# private use unicode char that represents phonemes for OOV tokens
OOV_PHONEMES = "\ue000"

# types for sound tables: map a string to a tuple of syllable phonemes
Phonemes_T = Tuple[Optional[str], ...]
SoundTable_T = Mapping[str, Phonemes_T]


class GraphemesToPhonemes:
    """A spaCy pipeline component that converts graphemes to phonemes."""

    table: Table        # reference to sound table in spaCy lookups
    lookups: Lookups    # reference to all LUTs for language model

    def __init__(self, nlp: Language, sound_table: SoundTable_T):
        """Initialize the phonemes component."""
        # infer the syllable segmentation and map it to an empty phoneme set
        syllable_parts = len(next(iter(sound_table.values())))
        self.empty_phonemes = tuple(None for _ in range(syllable_parts))

        # register extensions on spaCy primitives
        if not Doc.has_extension("phonemes"):
            Doc.set_extension("phonemes", getter=self.get_all_phonemes)
        if not Span.has_extension("phonemes"):
            Span.set_extension("phonemes", getter=self.get_all_phonemes)
        if not Token.has_extension("phonemes"):
            Token.set_extension("phonemes", getter=self.get_token_phonemes)
        if not Token.has_extension("is_oov"):
            Token.set_extension("is_oov", getter=self.is_token_oov)

        # store the sound table in the vocab's Lookups
        self.lookups = nlp.vocab.lookups
        self.table = self.lookups.add_table("phonemes", sound_table)
        logging.info(f"using {self.__class__}")

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def is_token_oov(self, token: Token) -> bool:
        """Check if a token has a phonetic entry in the sound table."""
        return token.text not in self.table

    def has_variant(self, match: Match) -> bool:
        """True if a seed contains a graphic variant.

        This is designed to be called on seeds that are of the same length,
        so that the match doesn't need to be aligned for it to work."""

        # compare each token pairwise, True if we find a variant, else False
        for i in range(len(match)):
            if self.are_graphic_variants(match.utxt[i], match.vtxt[i]):
                return True
        return False

    def are_graphic_variants(self, *tokens: Token) -> bool:
        """Check if a set of tokens are graphic variants of the same word.

        - If any tokens are not in the sound table, returns False.
        - If any tokens are non-voiced, returns False.
        - If any tokens have identical text (graphs), returns False.
        - If any tokens have differing phonemes, returns False.
        """

        # O(n) implementation: compare all tokens against first one
        base_text = tokens[0].text
        base_phon = self.get_token_phonemes(tokens[0])
        if base_phon == self.empty_phonemes or base_phon == (OOV_PHONEMES,):
            return False
        for token in tokens[1:]:
            phonemes = self.get_token_phonemes(token)
            if phonemes == self.empty_phonemes or \
               phonemes == (OOV_PHONEMES,) or \
               phonemes != base_phon or \
               token.text == base_text:
                return False
        return True

    def get_all_phonemes(self, tokens: Iterable[Token]) -> Iterator[str]:
        """Return a flattened iterator over all phonemes in a Span or Doc.

        - Skips parts of the syllable that are not used (stored as None).
        - Skips non-voiced tokens, such as punctuation.
        - Skips tokens with no phonetic entry in the sound table.
        """

        for token in tokens:
            for phoneme in self.get_token_phonemes(token):
                if phoneme and phoneme != OOV_PHONEMES:
                    yield phoneme

    def get_token_phonemes(self, token: Token) -> Phonemes_T:
        """Return a Token's phonemes as an n-tuple.

        - If a Token is non-alphanumeric, all elements of the tuple will be None.
        - If a Token is not in the sound table, all elements of the tuple will
        use a special marker token (OOV_PHONEMES).
        - If some parts of the syllable are not present, their corresponding
        elements in the tuple will be None.
        """

        if not token.is_alpha and not token.like_num:
            return self.empty_phonemes
        elif token._.is_oov:
            # logging.warning(f"no entry for token in sound table: {token.text}")
            return (OOV_PHONEMES,)
        else:
            return self.table[token.text]


def get_sound_table_json(path: Path) -> SoundTable_T:
    """Load a sound table as JSON."""
    sound_table: SoundTable_T = {}

    # open the file and load all readings
    with open(path, encoding="utf8") as file:
        entries = json.loads(file.read())
        for char, readings in entries.items():

            # FIXME just using first reading for now, ignoring multiple
            # NOTE final two entries in current table are source info; ignore
            *reading, _src, _src2 = readings[0]
            sound_table[char] = tuple(reading)  # type: ignore

    # log and return finished table
    logging.info(f"sound table {path.resolve()} loaded")
    return sound_table


@Language.factory("g2p")
def create_graphemes_to_phonemes(nlp: Language, name: str, sound_table: SoundTable_T) -> GraphemesToPhonemes:
    return GraphemesToPhonemes(nlp, sound_table)
