"""
Utility functions
"""

import logging
from itertools import chain, groupby
from operator import attrgetter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Deque

from dphon.extend import Extender
from dphon.match import Match


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
