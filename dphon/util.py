"""
Utility functions
"""

import logging
from itertools import chain, groupby
from operator import attrgetter
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Tuple

from rich.progress import BarColumn, Progress

from dphon.extend import Extender
from dphon.match import Match

progress = Progress(
    "{task.elapsed:.0f}s",
    "{task.description}",
    BarColumn(bar_width=None),
    "{task.completed:,}/{task.total:,}",
    "{task.percentage:.1f}%",
    transient=True
)

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
