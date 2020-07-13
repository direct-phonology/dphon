"""
Utility functions
"""

from typing import List

from dphon.tokenizer import Token


def has_graphic_variation(tokens: List[Token]) -> bool:
    """Check if provided tokens are graphically identical"""
    texts = [t.meta["orig_text"] for t in tokens]
    return len(set(texts)) > 1
