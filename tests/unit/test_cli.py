"""Tests for the cli module."""

import logging
import sys
from io import StringIO
from unittest import TestCase
from unittest.mock import patch

from dphon.cli import __doc__ as doc
from importlib.metadata import version as pkg_version
from dphon.cli import run

# disconnect logging for testing
logging.captureWarnings(True)
logging.disable(logging.CRITICAL)


class TestCommands(TestCase):
    """Test the --help and --version commands."""

    def test_help(self) -> None:
        """--help command should print cli module docstring"""
        sys.argv = ["dphon", "--help"]
        with patch("sys.stdout", new=StringIO()) as output:
            self.assertRaises(SystemExit, run)
            self.assertEqual(output.getvalue().strip(), str(doc).strip())

    def test_version(self) -> None:
        """--version command should print program version"""
        sys.argv = ["dphon", "--version"]
        with patch("sys.stdout", new=StringIO()) as output:
            self.assertRaises(SystemExit, run)
            self.assertEqual(output.getvalue().strip(), pkg_version("dphon").strip())
