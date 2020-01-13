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
        sys.argv = ['dphon', '--help']
        with patch('sys.stdout', new=StringIO()) as output:
            with raises(SystemExit):
                run()
            assert output.getvalue().strip() == doc.strip()

    def test_version(self):
        # version command should print module version
        sys.argv = ['dphon', '--version']
        with patch('sys.stdout', new=StringIO()) as output:
            with raises(SystemExit):
                run()
            assert output.getvalue().strip() == version.strip()

    def test_variants_only(self):
        # --variants-only flag should limit to graphic variant matches only
        sys.argv = ['dphon',
                    'tests/fixtures/郭店/老子丙.txt',
                    'tests/fixtures/郭店/老子甲.txt',
                    '--variants-only']
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode().splitlines()
        # only these two matches should be in output
        assert results[0] == '猷乎，其 (老子丙: 1)'
        assert results[1] == '猶乎其 (老子甲: 5)'
        assert results[3] == '右。是以 (老子丙: 3)'
        assert results[4] == '有。是以 (老子甲: 16)'
        assert len(results) == 6

    def test_n(self):
        # --n option should return matches of at least length n
        sys.argv = ['dphon',
                    'tests/fixtures/郭店/老子丙.txt',
                    'tests/fixtures/郭店/老子甲.txt',
                    '--n=5']
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode()
        # longer matches are in output, shorter are not
        assert '為之者敗之，執之者失之' in results
        assert '人欲不欲，不貴難得之貨' in results
        assert '於天下' not in results
        assert '猷乎，其' not in results


class TestIO(TestCase):

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
            with open(outfile, encoding='utf-8') as file:
                results = file.read().splitlines()
            assert results[0] == '猷乎，其 (老子丙: 1)'
            assert results[1] == '猶乎其 (老子甲: 5)'
