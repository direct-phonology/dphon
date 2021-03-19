#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for converting graphemes to phonemes."""

import json
import logging
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Optional, Tuple, List

from spacy.language import Language
from spacy.lookups import Table
from spacy.tokens import Doc, Span, Token

from dphon.match import Match

# private use unicode char that represents phonemes for OOV tokens
OOV_PHONEMES = "\ue000"

# types for sound tables: map a string to a tuple of syllable phonemes
Phonemes_T = Tuple[Optional[str], ...]
SoundTable_T = Mapping[str, Phonemes_T]


class GraphemesToPhonemes:
    """Grapheme-to-phoneme conversion using a `spacy.lookups.Table`.

    Intended for use as a spaCy pipeline component. Docs will be passed through
    the component unmodified. Registers several extension attributes that can be
    used elsewhere in a spaCy pipeline:
    
    - `Doc._.phonemes`: iterator over all phonemes in a `spacy.tokens.Doc`
    - `Span._.phonemes`: iterator over all phonemes in a `spacy.tokens.Span`
    - `Token._.phonemes`: iterator over all phonemes in a `spacy.tokens.Token`
    - `Token._.is_oov`: check whether a token can be converted to phonemes
    
    Args:
        nlp: a spaCy language model.
        sound_table: grapheme-to-phoneme conversion table.
    """

    _table: Table       # uses spaCy's lookup tables (bloom filtered dict)

    def __init__(self, nlp: Language, sound_table: SoundTable_T):
        # infer the syllable segmentation and map it to an empty phoneme set
        syllable_parts = len(next(iter(sound_table.values())))
        self.empty_phonemes = tuple(None for _ in range(syllable_parts))

        # register extensions on spaCy primitives
        if not Doc.has_extension("phonemes"):
            Doc.set_extension("phonemes", getter=self.get_all_phonemes)
        if not Span.has_extension("phonemes"):
            Span.set_extension("phonemes", getter=self.get_all_phonemes)
        if not Span.has_extension("syllables"):
            Span.set_extension("syllables", getter=self._get_syllables)
        if not Token.has_extension("phonemes"):
            Token.set_extension("phonemes", getter=self.get_token_phonemes)
        if not Token.has_extension("is_oov"):
            Token.set_extension("is_oov", getter=self.is_token_oov)

        # store the sound table in the vocab's Lookups
        self.table = nlp.vocab.lookups.add_table("phonemes", sound_table)
        logging.info(f"using {self.__class__}")

    def __call__(self, doc: Doc) -> Doc:
        return doc

    def is_token_oov(self, token: Token) -> bool:
        """`True` if `token` has no phonetic entry in the sound table.
        
        Args:
            token: a single `spacy.tokens.Token` to check.
        """
        return token.text not in self.table

    def has_variant(self, match: Match) -> bool:
        """`True` if `match` contains a graphic variant.

        This is designed to be called on matches that are of the same length,
        so that the match doesn't need to be aligned for it to work.

        Args:
            match: a single `dphon.match.Match`, usually output from the early
            seed stage, to check.
        """

        # compare each token pairwise, True if we find a variant, else False
        for i in range(len(match)):
            if self.are_graphic_variants(match.utxt[i], match.vtxt[i]):
                return True
        return False

    def are_graphic_variants(self, *tokens: Token) -> bool:
        """Check if `tokens` are graphic variants.

        - `False` if any tokens are not in the sound table.
        - `False` if any tokens are non-voiced.
        - `False` if any tokens have identical graphemes.
        - `False` if any tokens have differing phonemes.

        Args:
            tokens: any number of `spacy.tokens.Token` to compare.
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
        """Flattened iterator over all phonemes in `tokens`.

        - Skips parts of the syllable that are not used (stored as None).
        - Skips non-voiced tokens, such as punctuation.
        - Keeps OOV_PHONEMES as an indicator of missing phonetic information.

        Args:
            tokens: iterable of `spacy.tokens.Token` to convert.
        """

        for token in tokens:
            for phoneme in self.get_token_phonemes(token):
                if phoneme:
                    yield phoneme

    def get_token_phonemes(self, token: Token) -> Phonemes_T:
        """Return `token`'s phonemes as an n-tuple.

        - If `token` is non-alphanumeric, all elements of the tuple will be None.
        - If `token` is not in the sound table, all elements of the tuple will
        use a special marker (`OOV_PHONEMES`).
        - If some parts of the syllable are not present, their corresponding
        elements in the tuple will be `None`.
        """

        if not token.is_alpha and not token.like_num:
            return self.empty_phonemes
        elif token._.is_oov:
            logging.debug(f"no phonemes for token: \"{token.text}\"")
            return (OOV_PHONEMES,)
        else:
            return self._select(self.table[token.text])

    def _get_token_syllable(self, token: Token) -> str:
        try:
            return "".join(self.table[token.text])
        except KeyError:
            return ""

    def _get_syllables(self, tokens: Iterable[Token]) -> List[str]:
        return [self._get_token_syllable(token) for token in tokens]

    def _select(self, reading: Phonemes_T) -> Phonemes_T:
        """Filter the syllable to only the segments we're interested in."""
        # NOTE using only initial, nucleus, coda currently
        initial = reading[3]
        nucleus = reading[6]
        coda = reading[7]
        return (initial, nucleus, coda)


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
