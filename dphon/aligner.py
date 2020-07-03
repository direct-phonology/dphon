"""Alignment algorithms"""

import json
from abc import ABC
from typing import Tuple

import numpy as np
import pkg_resources

from dphon.matcher import Match


class Aligner(ABC):

    def align(self, source: str, target: str) -> Tuple[str, str]:
        """Align the two strings by padding with spaces where required and
        return them in a tuple."""
        raise NotImplementedError

class NeedlemanWunsch(Aligner):

    match_score: float
    misalign_score: float
    mismatch_score: float

    def __init__(self, **kwargs):
        super().__init__()
        self.match_score = kwargs.get('match_score', 1.0)
        self.misalign_score = kwargs.get('misalign_score', -0.5)
        self.mismatch_score = kwargs.get('mismatch_score', -1.0)

    def score(self, char1: str, char2: str) -> float:
        if char1 == char2:
            return self.match_score
        else:
            return self.mismatch_score

    def trim(self, source: str, target: str) -> Tuple[str, str]:
        """
        Due to the matching algorithm used, we may be aligning two strings
        that don't match at the ends. In these cases, we want to shave off the
        endings.
        """

        # by default, trim non-matching end characters
        while source[-1] != target[-1]:
            source = source[:-1]
            target = target[:-1]

        return (source, target)


    def align(self, match: Match) -> Tuple[str, str]:
        source = match.source_text()
        target = match.target_text()
        aligned_source = ""
        aligned_target = ""

        # create alignment matrix
        rows = len(source) + 1
        cols = len(target) + 1
        matrix = np.zeros([rows, cols])
        for row in range(rows):
            matrix[row][0] = -row
        for col in range(cols):
            matrix[0][col] = -col

        # populate alignment matrix
        for row in range(rows - 1):
            for col in range(cols - 1):
                score = self.score(source[row], target[col])
                top_score = matrix[row][col + 1] + self.misalign_score
                left_score = matrix[row + 1][col] + self.misalign_score
                diag_score = matrix[row][col] + score
                best_score = max([top_score, left_score, diag_score])
                matrix[row + 1][col + 1] = best_score

        # perform traceback
        row = rows - 1
        col = cols - 1
        while row > 0 or col > 0:
            top_score = matrix[row - 1][col]
            left_score = matrix[row][col - 1]
            diag_score = matrix[row - 1][col - 1]
            best_score = max([top_score, left_score, diag_score])

            if best_score == diag_score:
                row -= 1
                col -= 1
                aligned_source = source[row] + aligned_source
                aligned_target = target[col] + aligned_target

            elif best_score == left_score:
                col -= 1
                aligned_source = "　" + aligned_source
                aligned_target = target[col] + aligned_target

            elif best_score == top_score:
                row -= 1
                aligned_source = source[row] + aligned_source
                aligned_target = "　" + aligned_target

        # normalize to same length
        while aligned_source[-1] == "　" or aligned_target[-1] == "　":
            aligned_source = aligned_source[:-1]
            aligned_target = aligned_target[:-1]

        return self.trim(aligned_source, aligned_target)

class NeedlemanWunschPhonetic(NeedlemanWunsch):

    homonym_score: float
    phon_dict: dict

    def __init__(self, dict_name: str, **kwargs):
        super().__init__()
        self.homonym_score = kwargs.get('homonym_score', 0.5)

        path = pkg_resources.resource_filename(__package__, dict_name)
        with open(path, encoding="utf-8") as dict_file:
            self.phon_dict = json.loads(dict_file.read())

    def score(self, char1: str, char2: str) -> float:
        if char1 in self.phon_dict and char2 in self.phon_dict:
            if self.phon_dict[char1][2] == self.phon_dict[char2][2]:
                return self.homonym_score
        return super().score(char1, char2)

    def trim(self, source: str, target: str) -> Tuple[str, str]:
        """
        Trim back to the first matching character, taking into account
        phonetic matches.
        """

        c1 = self.phon_dict.get(source[-1], [None, None, source[-1]])[2]
        c2 = self.phon_dict.get(target[-1], [None, None, target[-1]])[2]
        while c1 != c2:
            source = source[:-1]
            target = target[:-1]
            c1 = self.phon_dict.get(source[-1], [None, None, source[-1]])[2]
            c2 = self.phon_dict.get(target[-1], [None, None, target[-1]])[2]

        return (source, target)
