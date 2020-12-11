"""
Utility functions
"""

import logging
from collections import deque
from itertools import chain, groupby
from operator import attrgetter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Deque

from py_lapper import Cursor, Interval, Lapper

from dphon.extend import Extender
from dphon.reuse import Match


def condense_matches(matches: List[Match]) -> List[Match]:
    """Combine all overlapping matches in a pairwise document comparison."""
    # ensure list is sorted first to speed up querying
    matches.sort()
    # convert matches into Interval tuples for comparison
    intervals = [(Interval(match.left.start, match.left.end, None),
                  Interval(match.right.start, match.right.end, None))
                  for match in matches]
    stack: Deque[Tuple[Interval]] = deque()
    return matches


def is_norm_eq(match: Match) -> bool:
    """True if a match's sequences are equal after normalization.

    This comparison ignores whitespace, case, and punctuation, returning
    True if all alphanumeric characters of the left location match all
    alphanumeric characters of the right location and False otherwise."""
    left_norm = "".join([c.lower()
                         for c in match.left.text if c.isalnum()])
    right_norm = "".join([c.lower()
                          for c in match.right.text if c.isalnum()])
    return left_norm == right_norm


def group_by_doc(matches: Iterable[Match]) -> List[Match]:
    """Group matches by doc title, sorting by sequence position."""
    return list(sorted(matches, key=attrgetter("left.doc._.title",
                                               "right.doc._.title",
                                               "left.start",
                                               "left.end",
                                               "right.start",
                                               "right.end")))
    temp = []
    def left_doc(match): return match.left.doc._.title
    for _doc, group in groupby(sorted(matches, key=left_doc), key=left_doc):
        temp.append(sorted(group))
    return list(chain.from_iterable(temp))


def extend_matches(matches: Iterable[Match], extend: Extender) -> List[Match]:
    """Extend a list of matches using a provided Extender instance."""

    new_matches: List[Match] = []
    queue: List[Match] = []
    last_left = None
    last_right = None

    # iterate in reverse order
    matches = list(reversed(group_by_doc(matches)))

    # drain the old match list to fill up the new one
    while len(matches) > 0:
        current = matches.pop()

        # if new left doc or new right doc, dump queue and start over
        if current.left.doc != last_left or current.right.doc != last_right:
            new_matches += queue
            queue = [extend(current)]

        # if match is outside current range, dump queue and start over
        elif current.left.start >= queue[0].left.end:
            new_matches += queue
            queue = [extend(current)]

        # if match overlaps in left doc, check the queue
        elif current.left.start >= queue[0].left.start:
            skip = False

            for match in queue:
                # if match is internal to one in queue, skip it
                if current.right.start >= match.right.start and \
                        current.right.start <= match.right.end and \
                        current.right.end <= match.right.end:
                    skip = True
                    break

            # if match hits new location in right doc, add to queue
            if not skip:
                queue.append(extend(current))

        # track doc changes
        last_left = current.left.doc
        last_right = current.right.doc

    # add any remaining matches from queue and return finished list
    new_matches += queue
    return new_matches


def get_texts(directory: Path) -> List[Tuple[str, Dict[str, Any]]]:
    # load all texts and format with context
    texts = []
    for file in directory.glob("**/*.txt"):
        with file.open(encoding="utf8") as contents:
            text = contents.read()
            texts.append((text, {"title": file.stem, "len": len(text)}))
    logging.info(f"loaded {len(texts)} texts from {directory}")
    # return in order with largest texts first, to speed up processing
    # confirmed this is slightly faster on my machine 2020-09-04
    return sorted(texts, key=lambda t: t[1]["len"], reverse=True)
