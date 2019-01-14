import unittest
try:
    from unittest.mock import patch
except ImportError: # python 2.7
    from mock import patch

import pytest

from dphon.util import lookup


class TestUtils(unittest.TestCase):

    def test_lookup(self):
        return True
