"""Tests for the cli module."""

import sys
import tempfile
from io import StringIO
from unittest import TestCase, skip
from unittest.mock import patch

from dphon.cli import run, __doc__ as doc, __version__ as version


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

    @skip("todo")
    def test_min(self) -> None:
        """--min option should limit to results with specified minimum length"""
        pass

    @skip("todo")
    def test_max(self) -> None:
        """--max option should limit to results with specified maximum length"""
        pass

    @skip("todo")
    def test_min_and_max(self) -> None:
        """--min and --max options together should limit to exact length"""
        pass

    @skip("todo")
    def test_all(self) -> None:
        """--all flag should include trivial results with little variation"""
        pass

    @skip("todo")
    def test_variants_only(self) -> None:
        """--variants-only flag should limit to results with graphic variation"""
        pass

    @skip("todo")
    def test_output_file(self) -> None:
        """--output option should write to a file"""
        pass
