"""Tests for the cli module."""

import logging
import sys
from io import StringIO
from unittest import TestCase, skip
from unittest.mock import MagicMock, patch

from dphon.cli import __doc__ as doc
from dphon.cli import __version__ as version
from dphon.cli import process, run, setup, teardown

# disconnect logging for testing
logging.disable(logging.CRITICAL)


class TestCommands(TestCase):
    """Test the --help and --version commands."""

    def test_help(self) -> None:
        """--help command should print cli module docstring"""
        sys.argv = ["dphon", "--help"]
        with patch('sys.stdout', new=StringIO()) as output:
            self.assertRaises(SystemExit, run)
            self.assertEqual(output.getvalue().strip(), doc.strip())

    def test_version(self) -> None:
        """--version command should print program version"""
        sys.argv = ["dphon", "--version"]
        with patch('sys.stdout', new=StringIO()) as output:
            self.assertRaises(SystemExit, run)
            self.assertEqual(output.getvalue().strip(), version.strip())


class TestOptions(TestCase):
    """Test the various options available when running."""

    def setUp(self) -> None:
        """Set up a spaCy pipeline and mock progressbar for testing."""
        self.progress = MagicMock()
        self.nlp = setup()

    def tearDown(self) -> None:
        """Unregister components to prevent name collisions."""
        teardown(self.nlp)

    def test_min(self) -> None:
        """--min option should limit to results with specified minimum length"""
        args = {"--min": "50", "<path>": ["tests/fixtures/laozi/"]}
        results = process(self.nlp, self.progress, args).matches
        for result in results:
            self.assertTrue(len(result) >= 50)

    def test_max(self) -> None:
        """--max option should limit to results with specified maximum length"""
        args = {"--max": "4", "<path>": ["tests/fixtures/laozi/"]}
        results = process(self.nlp, self.progress, args).matches
        for match in results:
            self.assertTrue(len(match) <= 4)

    def test_min_and_max(self) -> None:
        """--min and --max options together should limit to exact length"""
        args = {"--min": "8", "--max": "8",
                "<path>": ["tests/fixtures/laozi/"]}
        results = process(self.nlp, self.progress, args).matches
        for match in results:
            self.assertTrue(len(match) == 8)

    def test_keep_newlines(self) -> None:
        """--keep-newlines flag should preserve newlines in output"""
        args = {"--keep-newlines": True,
                "<path>": ["tests/fixtures/laozi/"],
                "--min": "11",
                "--max": "11"}
        results = list(process(self.nlp, self.progress, args).matches)
        if not results[-3].au:
            self.fail("results were not aligned")
        self.assertTrue("\n" in results[-3].au)

    @skip("todo")
    def test_variants_only(self) -> None:
        """--variants-only flag should limit to results with graphic variation"""

    @skip("todo")
    def test_output_file(self) -> None:
        """--output option should write to a file"""
        pass
