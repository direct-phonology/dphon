#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the input/output module."""

from unittest import TestCase

from dphon.io import PlaintextCorpusLoader

class TestPlaintextCorpusLoader(TestCase):
    """Test the PlaintextCorpusLoader."""

    def setUp(self) -> None:
        """Create a loader for testing."""
        self.load = PlaintextCorpusLoader()

    def test_no_files(self) -> None:
        """should not fail if no files were found"""
        # pass an empty list of paths; output should be empty list
        files = self.load([])
        self.assertEqual(list(files), [])

    def test_bad_file(self) -> None:
        pass

    def test_glob(self) -> None:
        pass

    def test_file_and_glob(self) -> None:
        pass