"""
Utility functions
"""

from typing import List

from dphon.tokenizer import Token
from dphon.graph import Match


def has_graphic_variation(tokens: List[Token]) -> bool:
    """
    Check if provided tokens are not graphically identical.
    """
    texts = [t.meta["orig_text"] for t in tokens]
    return len(set(texts)) > 1


def condense_matches(matches: List[Match]) -> List[Match]:
    """
    Combine matches for a single document that are overlapping, so that only
    maximal matches remain.
    """
    # sort and reverse match list to use it as a stack
    if len(matches) == 0:
        return []
    matches = list(reversed(sorted(matches)))

    # store finished matches and actively worked-on ones in stacks
    new_matches: List[Match] = []
    stack: List[Match] = []
    stack.append(matches.pop())

    # drain the old match list to fill up the new one
    while len(matches) > 0:
        compare = matches.pop()  # FIXME check that this is a ref
        current = stack[-1]  # FIXME check that this is a ref

        # moving to new source/target doc; transfer all of stack and reset
        if current.doc1 != compare.doc1 or current.doc2 != compare.doc2:
            while len(stack) > 0:
                new_matches.append(stack.pop())

        # match is congruent but matches somewhere else; push new current
        elif compare.pos1.start == current.pos1.start:
            stack.append(compare)

        # match overlaps; update current match bounds to include it
        elif compare.pos1.start > current.pos1.start and \
                compare.pos1.start < current.pos1.stop and \
                compare.pos2.start > current.pos2.start and \
                compare.pos2.start < current.pos2.stop and \
                compare.pos2.stop > current.pos2.stop and \
                compare.pos1.stop > current.pos1.stop:
            current.pos1 = slice(current.pos1.start, compare.pos1.stop)
            current.pos2 = slice(current.pos2.start, compare.pos2.stop)

        # match doesn't overlap; pop from stack and push new current
        else:
            new_matches.append(stack.pop())
            stack.append(compare)

    # add any remaining matches from stack and return finished list
    while len(stack) > 0:
        new_matches.append(stack.pop())
    return new_matches
