#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Abstract base class and implementations for extending Matches."""

from abc import ABC, abstractmethod
from typing import List

import Levenshtein as Lev
from spacy.tokens import Span

from .match import Match
from .phonemes import OOV_PHONEMES


class Extender(ABC):
    """Extenders use heuristics to lengthen and return match sequences."""

    @abstractmethod
    def __call__(self, match: Match) -> Match:
        """Extend the match as far as possible and return it."""
        raise NotImplementedError


class StringDistanceExtender(Extender):
    """Add tokens to sequences while string distance metric is above threshold.

    Subclass and implement the _score() method to implement the desired string
    distance measure, e.g. Levenshtein ratio.
    """

    threshold: float    # if the score falls below this, match gets cut off
    len_limit: int      # only score this many tokens at the end of the match

    def __init__(self, threshold: float, len_limit: int) -> None:
        """Create a new LevenshteinExtender."""
        self.threshold = threshold
        self.len_limit = len_limit

    @abstractmethod
    def _score(self, left: Span, right: Span, rev: bool = False) -> float:
        """Compare the match sequences using a string distance measurement.

        Compares only up to len_limit characters when scoring, to speed up
        calculation and improve accuracy for long sequences. When looking in
        reverse, set rev=True to compare the start of the match instead of the
        ends."""
        raise NotImplementedError

    def _extend_fwd(self, match: Match) -> Match:
        """Return a copy of a match extended in the forward direction."""
        trail = 0
        score = self._score(match.utxt, match.vtxt)
        utxt = match.utxt.doc[match.utxt.start:match.utxt.end]
        vtxt = match.vtxt.doc[match.vtxt.start:match.vtxt.end]
        ulen, vlen = len(match.utxt.doc), len(match.vtxt.doc)

        # extend while score is above threshold and we aren't at the end
        while score >= self.threshold and utxt.end < ulen and vtxt.end < vlen:
            utxt = utxt.doc[utxt.start:utxt.end + 1]
            vtxt = vtxt.doc[vtxt.start:vtxt.end + 1]

            # track the last score increase and how far we've gone past it
            new_score = self._score(utxt, vtxt)
            trail = trail + 1 if new_score < score else 0
            score = new_score

        # return match trimmed back to last increasing score
        return Match(match.u, match.v, utxt.doc[utxt.start:utxt.end - trail],
                     vtxt.doc[vtxt.start:vtxt.end - trail])

    def _extend_rev(self, match: Match) -> Match:
        """Return a copy of a match extended in the reverse direction."""
        trail = 0
        score = self._score(match.utxt, match.vtxt, rev=True)
        utxt = match.utxt.doc[match.utxt.start:match.utxt.end]
        vtxt = match.vtxt.doc[match.vtxt.start:match.vtxt.end]

        # extend while score is above threshold and we aren't at the start
        while score >= self.threshold and utxt.start > 0 and vtxt.start > 0:
            utxt = utxt.doc[(utxt.start-1):utxt.end]
            vtxt = vtxt.doc[(vtxt.start-1):vtxt.end]

            # track the last score increase and how far we've gone past it
            new_score = self._score(utxt, vtxt, rev=True)
            trail = trail + 1 if new_score < score else 0
            score = new_score

        # return match trimmed back to last increasing score
        return Match(match.u, match.v, utxt.doc[utxt.start + trail:utxt.end],
                     vtxt.doc[vtxt.start + trail:vtxt.end])

    def __call__(self, match: Match) -> Match:
        """Extend a match using Levenshtein ratio comparison.

        After extending in both directions, use the results to update the match
        bounds and rescore it."""

        ex_fwd = self._extend_fwd(match)
        ex_rev = self._extend_rev(match)
        utxt = match.utxt.doc[ex_rev.utxt.start:ex_fwd.utxt.end]
        vtxt = match.vtxt.doc[ex_rev.vtxt.start:ex_fwd.vtxt.end]
        score = self._score(utxt, vtxt)
        return Match(match.u, match.v, utxt, vtxt, score)


class LevenshteinExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio is above threshold."""

    def _score(self, utxt: Span, vtxt: Span, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequences."""

        if rev:
            return Lev.ratio(
                utxt.text[:self.len_limit],
                vtxt.text[:self.len_limit]
            )
        else:
            return Lev.ratio(
                utxt.text[-self.len_limit:],
                vtxt.text[-self.len_limit:]
            )


class LevenshteinPhoneticExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio of phonemes is above
    threshold."""

    def _score(self, utxt: Span, vtxt: Span, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequence phonemes."""

        # if we encounter any OOV tokens, count it as a mismatch
        if OOV_PHONEMES in utxt._.phonemes or OOV_PHONEMES in vtxt._.phonemes:
            return -1

        # otherwise score based on phonemes
        text1 = "".join(utxt._.phonemes)
        text2 = "".join(vtxt._.phonemes)

        # score in the provided direction
        if rev:
            return Lev.ratio(text1[:self.len_limit], text2[:self.len_limit])
        else:
            return Lev.ratio(text1[-self.len_limit:], text2[-self.len_limit:])


def extend_matches(matches: List[Match], extend: Extender) -> List[Match]:
    """Extend a list of matches using a provided Extender instance."""
    # track working matches in a queue; store finished ones separately
    working: List[Match] = []
    done: List[Match] = []

    # track unprocessed matches in a queue; sort then reverse so we can pop()
    # matches from the queue until it's empty, starting at the front
    todo = list(reversed(sorted(matches)))
    while todo:
        current = todo.pop()

        # if we're not working on any matches yet, or if the current match is
        # outside working point in U, clear and reset the working area
        if not working or current.utxt.start >= working[0].utxt.end:
            done += working
            working = [extend(current)]

        # if we overlap in U, check to see if we also overlap in V for any
        # matches we're working on
        else:
            skip = False
            for match in working:
                # if match is fully internal to one in the working area, skip
                # it, as we no longer need it
                if current.vtxt.start >= match.vtxt.start and \
                   current.vtxt.start <= match.vtxt.end and \
                   current.vtxt.end <= match.vtxt.end:
                    skip = True
                    break
            # if match hits new location in V, extend it and add it to
            # the working area
            if not skip:
                working.append(extend(current))

    # finish any remaining work and return extended matches
    done += working
    return done
