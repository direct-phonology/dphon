"""
Utility functions
"""

from typing import List, Dict
from collections import defaultdict

from dphon.tokenizer import Token
from dphon.graph import Match
from dphon.extender import Extender


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
        if current.pos1.start > queue[0].pos1.stop:
            new_matches += queue
            new_matches.append(current)
            queue = []

        # if match overlaps in doc1, check the queue
        elif current.pos1.start > queue[0].pos1.start:
            updated = False

            for match in queue:
                # if match needs to be condensed, extend bounds
                if current.pos2.start > match.pos2.start and \
                    current.pos2.start < match.pos2.stop and \
                    current.pos2.stop > match.pos2.stop:
                    match.pos1 = slice(match.pos1.start, current.pos1.stop)
                    match.pos2 = slice(match.pos2.start, current.pos2.stop)
                    updated = True
                    break
                # if match is subsumed by another, remove from queue
                elif current.pos2.start > match.pos2.start and \
                    current.pos2.stop < match.pos2.stop:
                    updated = True
                    break

            # if match hits new location in doc2, add to queue
            if not updated:
                queue.append(current)

    # add any remaining matches from queue and return finished list
    new_matches += queue
    return new_matches


def extend_matches(matches: List[Match], extender: Extender) -> List[Match]:
    """Extend matches using a provided extension strategy, returning maximal
    matches."""
    # if no matches, nothing to do
    if len(matches) == 0:
        return []

    # order matches by location in document 1; keep active matches in a queue
    matches = list(reversed(sorted(matches)))
    new_matches: List[Match] = []
    queue: List[Match] = []

    # drain the old match list to fill up the new one
    while len(matches) > 0:
        current = matches.pop()

        # if queue is empty, extend and add the match to it
        if len(queue) == 0:
            queue.append(extender.extend(current))
            continue

        # if match is outside current range, dump queue and start over
        if current.pos1.start >= queue[0].pos1.stop:
            new_matches += queue
            queue = [extender.extend(current)]

        # if match overlaps in doc1, check the queue
        elif current.pos1.start >= queue[0].pos1.start:
            skip = False

            for match in queue:
                # if match is internal to one in queue, skip it
                if current.pos2.start >= match.pos2.start and \
                    current.pos2.start <= match.pos2.stop and \
                    current.pos2.stop <= match.pos2.stop:
                    skip = True
                    break

            # if match hits new location in doc2, add to queue
            if not skip:
                queue.append(extender.extend(current))

    # add any remaining matches from queue and return finished list
    new_matches += queue
    return new_matches
