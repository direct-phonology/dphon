"""Abstract base class and implementations for extending Matches."""

from abc import ABC, abstractmethod

import Levenshtein as Lev

from dphon.phonemes import OOV_PHONEMES
from dphon.reuse import Match


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
    def _score(self, match: Match, rev: bool = False) -> float:
        """Compare the match sequences using a string distance measurement.
        
        Compares only up to len_limit characters when scoring, to speed up
        calculation and improve accuracy for long sequences. When looking in
        reverse, set rev=True to compare the start of the match instead of the
        ends."""
        raise NotImplementedError

    def _extend_fwd(self, match: Match) -> Match:
        """Extend the match forward and return it, updating the score."""
        trail = 0
        score = final_score = self._score(match)
        left_len, right_len = len(match.left.doc), len(match.right.doc)

        # extend while score is above threshold and we aren't at the end
        while score >= self.threshold and \
                match.left.end < left_len and match.right.end < right_len:
            match.left = match.left.doc[match.left.start:match.left.end + 1]
            match.right = match.right.doc[match.right.start:match.right.end + 1]

            # track the last score increase and how far we've gone past it
            new_score = self._score(match)
            trail = trail + 1 if new_score < score else 0
            final_score = new_score if new_score > score else final_score
            score = new_score

        # return match trimmed back to last increasing score, with final score
        match.left = match.left.doc[match.left.start:match.left.end - trail]
        match.right = match.right.doc[match.right.start:match.right.end - trail]
        match.score = final_score
        return match

    def _extend_rev(self, match: Match) -> Match:
        """Extend the match backwards and return it, updating the score."""
        trail = 0
        score = final_score = self._score(match, rev=True)

        # extend while score is above threshold and we aren't at the start
        while score >= self.threshold and \
                match.left.start > 0 and match.right.start > 0:
            match.left = match.left.doc[(match.left.start-1):match.left.end]
            match.right = match.right.doc[(match.right.start-1):match.right.end]

            # track the last score increase and how far we've gone past it
            new_score = self._score(match, rev=True)
            trail = trail + 1 if new_score < score else 0
            final_score = new_score if new_score > score else final_score
            score = new_score

        # return match trimmed back to last increasing score, with final score
        match.left = match.left.doc[match.left.start + trail:match.left.end]
        match.right = match.right.doc[match.right.start +
                                      trail:match.right.end]
        match.score = final_score
        return match

    def __call__(self, match: Match) -> Match:
        """Extend a match using Levenshtein ratio comparison."""
        return self._extend_rev(self._extend_fwd(match))


class LevenshteinExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio is above threshold."""

    def _score(self, match: Match, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequences."""

        if rev:
            return Lev.ratio(
                match.left.text[:self.len_limit],
                match.right.text[:self.len_limit]
            )
        else:
            return Lev.ratio(
                match.left.text[-self.len_limit:],
                match.right.text[-self.len_limit:]
            )


class LevenshteinPhoneticExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio of phonemes is above
    threshold."""

    def _score(self, match: Match, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequence phonemes."""

        # if we encounter any OOV tokens, count it as a mismatch
        if OOV_PHONEMES in match.left._.phonemes or \
           OOV_PHONEMES in match.right._.phonemes:
            return -1

        # otherwise score based on phonemes
        text1 = "".join(match.left._.phonemes)
        text2 = "".join(match.right._.phonemes)

        # score in the provided direction
        if rev:
            return Lev.ratio(text1[:self.len_limit], text2[:self.len_limit])
        else:
            return Lev.ratio(text1[-self.len_limit:], text2[-self.len_limit:])
