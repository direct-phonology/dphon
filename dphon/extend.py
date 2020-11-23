"""Abstract base class and implementations for extending Matches."""

from abc import ABC, abstractmethod

import Levenshtein as Lev

from dphon.reuse import Match
from dphon.phonemes import OOV_PHONEMES


class Extender(ABC):
    """Extenders use heuristics to lengthen and return match sequences."""

    @abstractmethod
    def __call__(self, match: Match) -> Match:
        """Extend the match as far as possible and return it."""
        raise NotImplementedError


class LevenshteinExtender(Extender):
    """Extends a match by adding tokens to both sequences until their
    Levenshtein ratio drops below a given threshold.

    This strategy is borrowed and adapted from Paul Vierthaler's chinesetextreuse
    project, specifically:
    https://github.com/vierth/chinesetextreuse/blob/master/detect_intertexuality.py#L189-L249
    """

    threshold: float    # if the Levenshtein ratio falls below this, match ends
    len_limit: int      # only score this many tokens at the end of the match

    def __init__(self, threshold: float, len_limit: int) -> None:
        """Create a new LevenshteinExtender."""
        self.threshold = threshold
        self.len_limit = len_limit

    def score(self, match: Match) -> float:
        """Compare the two Spans of a Match to generate a similarity score."""
        text1 = match.left.text
        text2 = match.right.text
        return Lev.ratio(text1[-self.len_limit:], text2[-self.len_limit:])

    def __call__(self, match: Match) -> Match:
        """Extend a match using edit distance comparison.

        Compare the two Spans via their Levenshtein ratio, and extend both
        Spans until that ratio falls below the stored threshold. Compare only 
        the final len_limit characters when scoring.
        """
        # get the docs and their bounds
        doc1 = match.left.doc
        doc2 = match.right.doc
        doc1_len = len(match.left.doc)
        doc2_len = len(match.right.doc)

        # extend until we drop below the threshold or reach end of texts
        score = self.score(match)
        extended = 0
        trail = 0
        while score >= self.threshold and match.left.end < doc1_len and match.right.end < doc2_len:
            # extend by one character and rescore
            match.left = doc1[match.left.start:match.left.end + 1]
            match.right = doc2[match.right.start:match.right.end + 1]
            extended += 1
            new_score = self.score(match)

            # keep track of consecutive decreases so we can discard the "trail"
            if new_score < score:
                trail += 1
            else:
                trail = 0
            score = new_score

        # when finished, return match with the "trail" removed, if any
        match.left = doc1[match.left.start:match.left.end - trail]
        match.right = doc2[match.right.start:match.right.end - trail]
        return match


class LevenshteinPhoneticExtender(LevenshteinExtender):
    """Extends a match by adding tokens to both sequences until the Levenshtein
    ratio of their phonemes drops below a given threshold.
    """

    def score(self, match: Match) -> float:
        """Score the Match using the Levenshtein ratio of its phonemes."""
        # if we encounter any OOV tokens, end the match
        if OOV_PHONEMES in match.left._.phonemes or \
           OOV_PHONEMES in match.right._.phonemes:
            return -1

        # otherwise score based on phonemes
        text1 = "".join(match.left._.phonemes)
        text2 = "".join(match.right._.phonemes)
        return Lev.ratio(text1[-self.len_limit:], text2[-self.len_limit:])
