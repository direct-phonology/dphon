"""Abstract base class and implementations for extending Matches."""

import json
from abc import ABC, abstractmethod

import Levenshtein as Lev
import pkg_resources

from dphon.match import Match


class Extender(ABC):
    """Extenders lengthen a match as far as possible and return a new match.

    Each Extender accepts a single match at a time to extend() and uses its
    Docs to determine if the match can be extended, returning a longer match.
    """

    @abstractmethod
    def extend(self, match: Match) -> Match:
        """Extend the match as far as possible and return it."""
        raise NotImplementedError


class LevenshteinExtender(Extender):
    """Extends a match by adding characters to both sequences until their
    Levenshtein ratio drops below a given threshold.

    This strategy is borrowed and adapted from Paul Vierthaler's chinesetextreuse
    project, specifically:
    https://github.com/vierth/chinesetextreuse/blob/master/detect_intertexuality.py#L189-L249
    """

    threshold: float    # if the Levenshtein ratio falls below this, match ends
    len_limit: int      # length at which edit distance measurement will reset

    def __init__(self, threshold: float, len_limit: int) -> None:
        """Create a new LevenshteinExtender."""
        self.threshold = threshold
        self.len_limit = len_limit

    def score(self, match: Match) -> float:
        """Compare the two Spans of a Match to generate a similarity score."""
        text1 = match.left.text
        text2 = match.right.text
        return Lev.ratio(text1[:self.len_limit], text2[:self.len_limit])

    def extend(self, match: Match) -> Match:
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
            match = Match(
                doc1[match.left.start:match.left.end+1],
                doc2[match.right.start:match.right.end+1]
            )
            extended += 1
            new_score = self.score(match)

            # keep track of consecutive decreases so we can discard the "trail"
            if new_score < score:
                trail += 1
            else:
                trail = 0
            score = new_score

        # when finished, return match with the "trail" removed, if any
        if trail > 0:
            return Match(
                doc1[match.left.start:match.left.end - trail],
                doc2[match.right.start:match.right.end - trail]
            )
        else:
            return match

'''
class LevenshteinPhoneticExtender(LevenshteinExtender):
    """The Levenshtein Phonetic extender uses the python-levenshtein module to
    make fast edit distance comparisons as it extends a match, taking into
    account phonetic correspondence between characters.

    It accepts a path to a specially formatted JSON file containing phonetic
    information, which it uses to determine if two characters are a sound match.
    Matches made in this way are scored the same as if the characters were the
    same graphically.

    This strategy is borrowed and adapted from Paul Vierthaler's chinesetextreuse
    project, specifically:
    https://github.com/vierth/chinesetextreuse/blob/master/detect_intertexuality.py#L189-L249
    """

    phon_dict: dict     # contains phonetic information for character lookup

    def __init__(self, corpus: Loader, threshold: float, len_limit: int, dict_fname: str) -> None:
        super().__init__(corpus, threshold, len_limit)
        path = pkg_resources.resource_filename(__package__, dict_fname)
        with open(path, encoding="utf-8") as dict_file:
            self.phon_dict = json.loads(dict_file.read())

    def extend(self, match: Match) -> Match:
        """Extend a match using phonetic-equivalent edit distance comparison.

        Compare the two sequences via their Levenshtein ratio, and extend both
        sequences until that ratio falls below the stored threshold. Treat the
        characters as their phonetic equivalents for the purpose of scoring.
        Compare only the final len_limit characters when scoring.
        """
        # get the two documents the match connects
        doc1 = self.corpus.get(match.doc1)
        doc2 = self.corpus.get(match.doc2)

        # get the text of the two sequences and convert to phonetic tokens
        text1 = "".join(
            [self.phon_dict[c][2] if c in self.phon_dict else c for c in doc1[match.pos1]])
        text2 = "".join(
            [self.phon_dict[c][2] if c in self.phon_dict else c for c in doc2[match.pos2]])

        # get the initial ratio (score)
        score = Levenshtein.ratio(
            text1[:self.len_limit], text2[:self.len_limit])

        # extend until we drop below the threshold
        extended = 0
        trail = 0
        while score >= self.threshold:
            match.pos1 = slice(match.pos1.start, match.pos1.stop + 1)
            match.pos2 = slice(match.pos2.start, match.pos2.stop + 1)
            extended += 1

            # don't go past end of texts
            if match.pos1.stop >= len(doc1) or match.pos2.stop >= len(doc2):
                break

            # add the phonetic tokens for the characters we extended to
            next1 = doc1[match.pos1.stop]
            next2 = doc2[match.pos2.stop]
            text1 += self.phon_dict[next1][2] if next1 in self.phon_dict else next1
            text2 += self.phon_dict[next2][2] if next2 in self.phon_dict else next2

            # calculate a new score using the last len_limit characters
            new_score = Levenshtein.ratio(
                text1[:self.len_limit], text2[:self.len_limit])

            # keep track of consecutive decreases so we can discard the "tail"
            if new_score < score:
                trail += 1
            else:
                trail = 0
            score = new_score

        # when finished, remove the "tail" and return the match
        if trail > 0:
            match.pos1 = slice(match.pos1.start, match.pos1.stop - trail + 1)
            match.pos2 = slice(match.pos2.start, match.pos2.stop - trail + 1)
        return match

'''