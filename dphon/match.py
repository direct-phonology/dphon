#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The Match class for encoding text reuse relationships."""

from typing import List, NamedTuple, Optional

from spacy.tokens import Span


class Match(NamedTuple):
    """A match is a pair of similar textual sequences in two documents."""
    u: str
    v: str
    utxt: Span
    vtxt: Span
    weight: float = 0
    au: Optional[List[str]] = None
    av: Optional[List[str]] = None

    def __len__(self) -> int:
        """Return the length of the longer sequence in the match."""
        return max(len(self.utxt), len(self.vtxt))
