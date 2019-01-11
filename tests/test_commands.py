import unittest
from unittest.mock import patch
from subprocess import run

import pytest

from dphon.commands import analyze


class TestAnalyze(unittest.TestCase):

    def test_file_must_exist(self):
        result = run(["dphon", "analyze", "foo.txt"])
        assert result.returncode == 1
