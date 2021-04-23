#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the corpus module."""

import logging
from unittest import TestCase

from dphon.corpus import PlaintextCorpusLoader


class TestPlaintextCorpusLoader(TestCase):
    """Test the PlaintextCorpusLoader."""

    def setUp(self) -> None:
        """Create a loader for testing."""
        self.load = PlaintextCorpusLoader()

    def test_no_files(self) -> None:
        """should error if no valid files were found"""
        # pass an empty list of paths; should error since no files found
        with self.assertRaises(SystemExit):
            with self.assertLogs(level="ERROR"):
                for _ in self.load([]):
                    pass

    def test_non_file(self) -> None:
        """should warn if passed something that isn't plaintext"""
        # Pass a python file and a text file; should warn
        # re-enable logging so we can check it in the test
        logging.disable(logging.INFO)
        with self.assertLogs(level="WARNING"):
            for _ in self.load(["tests/unit/test_corpus.py",
                                "tests/fixtures/laozi/laozi.txt"]):
                pass

    def test_single_file(self) -> None:
        """should load contents of a single file"""
        # Use a tiny file with no whitespace, etc. to strip
        path = "tests/fixtures/laozi/tiny.txt"
        docs = list(self.load([path]))
        self.assertEqual(docs[0][1], {"id": "tiny"})
        with open(path, encoding="utf8") as file:
            self.assertEqual(docs[0][0], file.read())

    def test_glob(self) -> None:
        """should load all text files in a directory via glob"""
        docs = list(self.load(["tests/fixtures/laozi/*.txt"]))
        self.assertEqual(len(docs), 4)
        doc_ids = [doc[1]["id"] for doc in docs]
        self.assertIn("gd_laozi", doc_ids)
        self.assertIn("tiny", doc_ids)
        self.assertIn("mwd_laozi", doc_ids)
        self.assertIn("laozi", doc_ids)

    def test_file_and_glob(self) -> None:
        """should allow combination of files and globs"""
        docs = list(self.load(["tests/fixtures/laozi/*laozi.txt",
                               "tests/fixtures/laozi/tiny.txt"]))
        self.assertEqual(len(docs), 4)
        doc_ids = [doc[1]["id"] for doc in docs]
        self.assertIn("gd_laozi", doc_ids)
        self.assertIn("tiny", doc_ids)
        self.assertIn("mwd_laozi", doc_ids)
        self.assertIn("laozi", doc_ids)
