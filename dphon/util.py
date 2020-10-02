"""
Utility functions
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Iterable
from pathlib import Path

from rich.progress import TaskID, Progress

from dphon.extender import Extender
from dphon.match import Match

'''


def has_graphic_variation(tokens: List[Token]) -> bool:
    """
    Check if provided tokens are not graphically identical.
    """
    # FIXME this should actually check if there's a graphic variant!
    texts = [t.meta["orig_text"] for t in tokens]
    return len(set(texts)) > 1


def condense_matches(matches: List[Match]) -> List[Match]:
    """
    Combine matches for a single document that are overlapping, so that only
    maximal matches remain.
    """
    # if no matches, nothing to do
    if len(matches) == 0:
        return []

    # order matches by location in document 1; keep active matches in a queue
    matches = list(reversed(sorted(matches)))
    new_matches: List[Match] = []
    queue: List[Match] = []

    # drain the old match list to fill up the new one
    queue.append(matches.pop())
    while len(matches) > 0:
        current = matches.pop()

        # if match is outside current range, dump queue and start over
        if current.left.start > queue[0].left.end:
            new_matches += queue
            new_matches.append(current)
            queue = []

        # if match overlaps in doc1, check the queue
        elif current.left.start > queue[0].left.start:
            updated = False

            for match in queue:
                # if match needs to be condensed, extend bounds
                if current.right.start > match.right.start and \
                    current.right.start < match.right.end and \
                    current.right.end > match.right.end:
                    match.left = slice(match.left.start, current.left.end)
                    match.right = slice(match.right.start, current.right.end)
                    updated = True
                    break
                # if match is subsumed by another, remove from queue
                elif current.right.start > match.right.start and \
                    current.right.end < match.right.end:
                    updated = True
                    break

            # if match hits new location in doc2, add to queue
            if not updated:
                queue.append(current)

    # add any remaining matches from queue and return finished list
    new_matches += queue
    return new_matches

'''

def extend_matches(matches: Iterable[Match], extender: Extender) -> List[Match]:
    """Extend matches using a provided extension strategy, returning maximal
    matches."""
    
    # order matches by location in left doc; keep active matches in a queue
    matches = list(reversed(sorted(matches)))
    new_matches: List[Match] = []
    queue: List[Match] = []
    last_left = None
    last_right = None

    # drain the old match list to fill up the new one
    while len(matches) > 0:
        current = matches.pop()

        # if new left doc or new right doc, dump queue and start over
        if current.left.doc != last_left or current.right.doc != last_right:
            new_matches += queue
            queue = [extender.extend(current)]

        # if match is outside current range, dump queue and start over
        elif current.left.start >= queue[0].left.end:
            new_matches += queue
            queue = [extender.extend(current)]

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
                queue.append(extender.extend(current))

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
        with file.open() as contents:
            text = contents.read()
            texts.append((text, {"title": file.stem, "len": len(text)}))
    logging.info(f"loaded {len(texts)} texts from {directory}")
    # return in order with largest texts first, to speed up processing
    # confirmed this is slightly faster on my machine 2020-09-04
    return sorted(texts, key=lambda t: t[1]["len"], reverse=True)