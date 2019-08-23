import sys
import tempfile
from io import StringIO
from os.path import exists
from unittest import TestCase
from unittest.mock import patch
from pytest import raises

from dphon.cli import run, __doc__ as doc, __version__ as version


class TestOptions(TestCase):

    def test_help(self):
        # help command should print module docstring
        sys.argv = ['dphon', '-h']
        with patch('sys.stdout', new=StringIO()) as output:
            with raises(SystemExit):
                run()
            assert output.getvalue().strip() == doc.strip()

    def test_version(self):
        # version command should print module version
        sys.argv = ['dphon', '-v']
        with patch('sys.stdout', new=StringIO()) as output:
            with raises(SystemExit):
                run()
            assert output.getvalue().strip() == version.strip()


class TestDualText(TestCase):

    def test_read_files(self):
        # read two files and compare them
        sys.argv = ['dphon',
                    'tests/fixtures/郭店/老子丙.txt',
                    'tests/fixtures/郭店/老子甲.txt']
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode().splitlines()
        assert results[0] == '猷乎，其 (老子丙: 1)'
        assert results[1] == '猶乎其 (老子甲: 5)'

    def test_write_file(self):
        # --output flag should write to a file
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = '%s/out.txt' % tmpdirname
            sys.argv = ['dphon',
                        'tests/fixtures/郭店/老子丙.txt',
                        'tests/fixtures/郭店/老子甲.txt',
                        '--output=%s' % outfile]
            run()
            with open(outfile) as file:
                results = file.read().splitlines()
            assert results[0] == '猷乎，其 (老子丙: 1)'
            assert results[1] == '猶乎其 (老子甲: 5)'
