"""Matches accept two initial Tokens as input and extend them using some
strategy to find the longest contiguous match."""

import re
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict

import Levenshtein
import pkg_resources

from dphon.tokenizer import Token


class Match():
    _id: int
    source: Token
    target: Token
    meta: Dict[str, Any]

    def __init__(self, _id: int, source: Token, target: Token):
        self._id = _id
        self.source = source
        self.target = target
        self.meta = defaultdict()

    def __repr__(self) -> str:
        return f"<Match id: {self._id}>"

    def __str__(self) -> str:
        return (
            f"{self.clean(self.source_text())} "
            f"({self.source.doc.title}:{self.source.start})\n"
            f"{self.clean(self.target_text())} "
            f"({self.target.doc.title}:{self.target.start})\n"
        )

    @property
    def id(self) -> int:
        return self._id

    def source_text(self) -> str:
        return self.source.doc.text[self.source.start:self.source.stop]

    def target_text(self) -> str:
        return self.target.doc.text[self.target.start:self.target.stop]

    def clean(self, s: str) -> str:
        return re.sub(r'(?:\s|[|¶])*', '', s)


class Matcher(ABC):

    @abstractmethod
    def extend(self, source: Token, target: Token) -> Match:
        raise NotImplementedError


class LevenshteinPhoneticMatcher(Matcher):

    _id:int
    phon_dict: dict
    threshold: float

    def __init__(self, dict_name: str, threshold: float):
        path = pkg_resources.resource_filename(__package__, dict_name)
        with open(path, encoding="utf-8") as dict_file:
            self.phon_dict = json.loads(dict_file.read())

        self.threshold = threshold
        self._id = 0

    def extend(self, source: Token, target: Token) -> Match:
        match = Match(self._id, source, target)
        match.meta["score"] = Levenshtein.ratio(match.source.text, match.target.text)
        match.meta["trail"] = 0
        self._id += 1
        final_score = match.meta["score"]
        extended = 0

        while(match.meta["score"] >= self.threshold):
            if match.target.stop >= len(match.target.doc):
                break
            if match.source.stop >= len(match.source.doc):
                break
            if extended >= 100:
                break

            # continue extending match
            match.source.stop += 1
            match.target.stop += 1
            extended += 1

            next_source_char = match.source.doc.text[match.source.stop]
            next_target_char = match.target.doc.text[match.target.stop]

            if next_source_char in self.phon_dict:
                next_source_char = self.phon_dict[next_source_char][2]

            if next_target_char in self.phon_dict:
                next_target_char = self.phon_dict[next_target_char][2]

            if next_source_char.isalpha():
                match.source.text += next_source_char

            if next_target_char.isalpha():
                match.target.text += next_target_char

            score = Levenshtein.ratio(match.source.text, match.target.text)
            if score < match.meta["score"]:
                match.meta["trail"] += 1
            else:
                final_score = score
                match.meta["trail"] = 0
            match.meta["score"] = score

        match.meta["score"] = final_score
        match.source.stop -= match.meta["trail"]
        match.target.stop -= match.meta["trail"]

        length = match.source.stop - match.source.start
        match.source.text = match.source.text[:length]
        match.target.text = match.target.text[:length]

        return match
