"""Abstract base class and implementations for extending Matches."""

from abc import ABC, abstractmethod

import Levenshtein as Lev
from spacy.tokens import Span

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
        score = self._score(match.left, match.right)
        left = match.left.doc[match.left.start:match.left.end]
        right = match.right.doc[match.right.start:match.right.end]
        left_len, right_len = len(match.left.doc), len(match.right.doc)

        # extend while score is above threshold and we aren't at the end
        while score >= self.threshold and \
                left.end < left_len and right.end < right_len:
            left = left.doc[left.start:left.end + 1]
            right = right.doc[right.start:right.end + 1]

            # track the last score increase and how far we've gone past it
            new_score = self._score(left, right)
            trail = trail + 1 if new_score < score else 0
            score = new_score

        # return match trimmed back to last increasing score
        return Match(left.doc[left.start:left.end - trail],
                     right.doc[right.start:right.end - trail])

    def _extend_rev(self, match: Match) -> Match:
        """Return a copy of a match extended in the reverse direction."""
        trail = 0
        score = self._score(match.left, match.right, rev=True)
        left = match.left.doc[match.left.start:match.left.end]
        right = match.right.doc[match.right.start:match.right.end]

        # extend while score is above threshold and we aren't at the start
        while score >= self.threshold and left.start > 0 and right.start > 0:
            left = left.doc[(left.start-1):left.end]
            right = right.doc[(right.start-1):right.end]

            # track the last score increase and how far we've gone past it
            new_score = self._score(left, right, rev=True)
            trail = trail + 1 if new_score < score else 0
            score = new_score

        # return match trimmed back to last increasing score
        return Match(left.doc[left.start + trail:left.end],
                     right.doc[right.start + trail:right.end])

    def __call__(self, match: Match) -> Match:
        """Extend a match using Levenshtein ratio comparison.

        After extending in both directions, use the results to update the match
        bounds and rescore it."""

        ex_fwd = self._extend_fwd(match)
        ex_rev = self._extend_rev(match)

        # use the extended bounds to update the match and score it
        match.left = match.left.doc[ex_rev.left.start:ex_fwd.left.end]
        match.right = match.right.doc[ex_rev.right.start:ex_fwd.right.end]
        match.score = self._score(match.left, match.right)
        return match


class LevenshteinExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio is above threshold."""

    def _score(self, left: Span, right: Span, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequences."""

        if rev:
            return Lev.ratio(
                left.text[:self.len_limit],
                right.text[:self.len_limit]
            )
        else:
            return Lev.ratio(
                left.text[-self.len_limit:],
                right.text[-self.len_limit:]
            )


class LevenshteinPhoneticExtender(StringDistanceExtender):
    """Add tokens to sequences while Levenshtein ratio of phonemes is above
    threshold."""

    def _score(self, left: Span, right: Span, rev: bool = False) -> float:
        """Compute the Levenshtein ratio of the match sequence phonemes."""

        # if we encounter any OOV tokens, count it as a mismatch
        if OOV_PHONEMES in left._.phonemes or \
           OOV_PHONEMES in right._.phonemes:
            return -1

        # otherwise score based on phonemes
        text1 = "".join(left._.phonemes)
        text2 = "".join(right._.phonemes)

        # score in the provided direction
        if rev:
            return Lev.ratio(text1[:self.len_limit], text2[:self.len_limit])
        else:
            return Lev.ratio(text1[-self.len_limit:], text2[-self.len_limit:])
