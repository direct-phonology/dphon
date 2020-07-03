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
    limit: int

    def __init__(self, dict_name: str, threshold: float, limit: int):
        path = pkg_resources.resource_filename(__package__, dict_name)
        with open(path, encoding="utf-8") as dict_file:
            self.phon_dict = json.loads(dict_file.read())

        self.threshold = threshold
        self.limit = limit
        self._id = 0

    def extend(self, source: Token, target: Token) -> Match:
        match = Match(self._id, source, target)
        match.meta["score"] = Levenshtein.ratio(match.source.text, match.target.text)
        match.meta["trail"] = 0
        self._id += 1
        final_score = match.meta["score"]
        extended = 0

        while(match.meta["score"] >= self.threshold):
            # continue extending match
            match.source.stop += 1
            match.target.stop += 1
            extended += 1

            # ensure we don't go past end of texts
            if match.target.stop >= len(match.target.doc):
                break
            if match.source.stop >= len(match.source.doc):
                break

            # if the match is over 100 characters we stop extending
            if extended >= 100:
                break

            # get the next character to append
            next_source_char = match.source.doc.text[match.source.stop]
            next_target_char = match.target.doc.text[match.target.stop]

            # use the converted phonetic token, if one exists
            if next_source_char in self.phon_dict:
                next_source_char = self.phon_dict[next_source_char][2]

            if next_target_char in self.phon_dict:
                next_target_char = self.phon_dict[next_target_char][2]

            match.source.text += next_source_char
            match.target.text += next_target_char

            score = Levenshtein.ratio(match.source.text[:self.limit],
                                      match.target.text[:self.limit])
            if score < match.meta["score"]:
                match.meta["trail"] += 1
            else:
                final_score = score
                match.meta["trail"] = 0
            match.meta["score"] = score

        match.meta["score"] = final_score
        match.source.stop -= match.meta["trail"] - 1
        match.target.stop -= match.meta["trail"] - 1

        return match


class VierthalerMatcher(Matcher):

    _id:int
    threshold: float
    limit: int

    def __init__(self, threshold, limit):
        super().__init__()
        self.threshold = threshold
        self.limit = limit
        self._id = 0


    # Extend the two matching seeds until they fall below the set matching threshold.
    # Returns their final length and the final similarity.
    def extend(self, source, target):

        sourcetext = source.doc.text
        targettext = target.doc.text

        ss = source.start
        ts = target.start

        # determine the end of the strings
        se = source.stop + 1
        te = target.stop + 1

        # Make sure the end of the string does not extend past the end of the document in question
        if se >= len(sourcetext):
            se = len(sourcetext)
        if te >= len(targettext):
            te = len(targettext)

        # Get the string slices
        sourcestring = sourcetext[ss:se]
        targetstring = targettext[ts:te]

        # Measure initial similarity
        similarity = Levenshtein.ratio(sourcestring, targetstring)

        # Establish tracking information
        # How far has the quote extended?
        extender = 0
        # How many instances of straight decrease?
        straightdecrease = 0

        # Track the similarity in the last loop
        previoussimilarity = similarity

        # Save the final high similarity. I do this so I don't need to remeasure similarity after
        # backing the quote up.
        finalsimilarity = similarity

        # While similarity is above the matching threshold, and the end of the quotes are within the two texts
        # keep extending the matches
        while similarity >= self.threshold and se +extender <= len(sourcetext) and te + extender <= len(targettext):
            extender += 1

            # If the length is over a certain amount then limit the Lev measurement
            if (se + extender - ss >= self.limit) and self.limit:
                adjust = se + extender - ss - self.limit
            else:
                adjust = 0

            # Check similarity of extended quote
            cmp1 = sourcetext[ss+adjust:se+extender]
            cmp2 = targettext[ts+adjust:te+extender]

            similarity = Levenshtein.ratio(cmp1, cmp2)

            # If the similarity is less than the previous instance, increment straight decrease
            # Otherwise, reset straight decrease to 0 and reset final similarity to similarity
            if similarity < previoussimilarity:
                straightdecrease += 1
            else:
                straightdecrease = 0
                finalsimilarity = similarity

            # Save similarity to previous similarity variable for use in the next iteration
            previoussimilarity = similarity
        # Back the length of the resulting quote up to the last time where its value began falling
        # and ended below the threshhold
        length = se+extender-straightdecrease - ss

        # return the length and final similarity
        # return length, finalsimilarity

        source.stop = source.start + length
        target.stop = target.start + length

        match = Match(0, source, target)
        match.meta["score"] = finalsimilarity

        return match
