#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the corpus module."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase, skip

from dphon.corpus import PlaintextCorpusLoader


class TestPlaintextCorpusLoader(TestCase):
    """Test the PlaintextCorpusLoader."""

    def setUp(self) -> None:
        """Create a loader for testing."""
        self.load = PlaintextCorpusLoader()

    @skip("fixme")
    def test_no_files(self) -> None:
        """should warn but not fail if no files were found"""
        # pass an empty list of paths; should warn no files found
        with self.assertLogs(level="WARN") as logged:
            files = list(self.load([]))
        self.assertTrue("no valid files found" in logged.output)

        # still passes empty list to spaCy
        self.assertEqual(files, [])

    @skip("fixme")
    def test_non_file(self) -> None:
        """should warn but not fail if passed a non-file"""
        # create a directory and pass it instead of a file; should warn
        with TemporaryDirectory() as tmp:
            with self.assertLogs(level="WARN") as logged:
                files = list(self.load([tmp]))
        self.assertTrue(f"path {tmp} isn't a file" in logged.output)

        # still passes empty list to spaCy
        self.assertEqual(files, [])

    @skip("fixme")
    def test_single_file(self) -> None:
        """should load contents of a single file"""
        # create a temporary file with some content
        with NamedTemporaryFile() as tmp:
            tmp.write("hello! welcome".encode("utf8"))
            files = list(self.load([tmp.name]))

        # output includes file's contents and doc id (filename)
        doc_id = Path(tmp.name).stem
        self.assertEqual(files, [("hello! welcome", {"id": doc_id})])

    @skip("todo")
    def test_glob(self) -> None:
        pass

    @skip("todo")
    def test_file_and_glob(self) -> None:
        pass
