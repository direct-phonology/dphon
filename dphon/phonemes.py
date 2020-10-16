"""SpaCy pipeline component for converting Tokens to phonetic equivalents."""

import csv
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple

from spacy.language import Language
from spacy.lookups import Lookups, Table
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

    name = "phonemes"   # will appear in spaCy pipeline
    attr = "phonemes"   # name for getter for phonemes, e.g. doc._.phonemes
    table: Table        # reference to sound table in spaCy lookups
    lookups: Lookups    # reference to all LUTs for language model

    def __init__(self, nlp: Language, sound_table: SoundTable_T, name: str = None, attr: str = None):
        """Initialize the phonemes component."""
        # store the name that will appear in the pipeline
        self.name = name if name else self.name
        self.attr = attr if attr else self.attr
        self.syllable_parts = len(next(iter(sound_table.values())))
        self.empty_phonemes = tuple(None for part in range(self.syllable_parts))

        # register attribute getters with customizable names; see:
        # https://spacy.io/usage/processing-pipelines#custom-components-best-practices
        Doc.set_extension(self.attr, getter=self.get_all_phonemes)
        Span.set_extension(self.attr, getter=self.get_all_phonemes)
        Token.set_extension(self.attr, getter=self.get_token_phonemes)
        Token.set_extension("is_oov", getter=self.is_token_oov)

        # store the sound table in the vocab's Lookups using the attr name
        self.lookups = nlp.vocab.lookups
        self.table = self.lookups.add_table(self.attr, sound_table)
        logging.info(f"created component \"{self.name}\"")

    def teardown(self) -> None:
        """Unregister the sound table and attributes to prevent collisions."""
        self.lookups.remove_table(self.attr)
        Doc.remove_extension(self.attr)
        Span.remove_extension(self.attr)
        Token.remove_extension(self.attr)
        Token.remove_extension("is_oov")

    def __call__(self, doc: Doc) -> Doc:
        """Return the Doc unmodified."""
        return doc

    def is_token_oov(self, token: Token) -> bool:
        """Check if a token has a phonetic entry in the sound table."""
        return token.text not in self.table

    def graphic_variants(self, tokens: Iterable[Token]) -> bool:
        """Check if a set of tokens are graphic variants of the same word."""
        # TODO implement
        raise NotImplementedError

    def get_all_phonemes(self, tokens: Iterable[Token]) -> Iterator[str]:
        """Return a flattened iterator over all phonemes in a Span or Doc.
        
        Skips parts of the syllable that are not used (stored as None)."""
        for token in tokens:
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

def get_sound_table_csv(path: Path) -> SoundTable_T:
    sound_table: SoundTable_T = defaultdict(tuple)
    parts = ["Preinitial1", "Preinitial 2", "Initial", "Medial",
             "Nucleus", "Final", "Postcoda *-ʔ", "Postcoda *-s"]
    with open(path, encoding="utf8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["\ufeffzi"] == "":
                continue
            sound_table[row["\ufeffzi"]] = tuple(
                [row[part].strip() if row[part].strip() !=
                 "" else None for part in parts]
            )
    logging.info(f"loaded sound table \"{path.stem}\"")
    return sound_table

def get_sound_table_json(path: Path) -> SoundTable_T:
    sound_table: SoundTable_T = defaultdict(tuple)
    with open(path, encoding="utf8") as file:
        entries = json.loads(file.read())
        for char, entry in entries.items():
            sound_table[char] = tuple(entry)
    logging.info(f"sound table {path.stem} loaded")
    return dict(sound_table)
