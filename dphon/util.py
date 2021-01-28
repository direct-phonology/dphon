#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utility functions."""

from rich.progress import BarColumn, Progress

progress = Progress(
    "{task.elapsed:.0f}s",
    "{task.description}",
    BarColumn(bar_width=None),
    "{task.completed:,}/{task.total:,}",
    "{task.percentage:.1f}%",
    transient=True
)

