import unittest
from unittest.mock import patch
from subprocess import run

import pytest

from dphon.commands import analyze


class TestCLI(unittest.TestCase):

    @patch('dphon.commands.analyze')
    def test_analyze(self, analyze):
        run(["dphon", "analyze"])
        assert analyze.called_once
