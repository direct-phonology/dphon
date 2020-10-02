import sys
import tempfile
from io import StringIO
from unittest import TestCase, main
from unittest.mock import patch

from dphon.cli import __doc__ as doc
from dphon.cli import __version__ as version
from dphon.cli import run


class TestOptions(TestCase):

    def test_help(self):
        # help command should print module docstring
        sys.argv = ['dphon', '--help']
        with patch('sys.stdout', new=StringIO()) as output:
            with self.assertRaises(SystemExit):
                 run()
            self.assertEqual(output.getvalue().strip(), doc.strip())

    def test_version(self):
        # version command should print module version
        sys.argv = ['dphon', '--version']
        with patch('sys.stdout', new=StringIO()) as output:
            with self.assertRaises(SystemExit):
                run()
            self.assertEqual(output.getvalue().strip(), version.strip())

    def test_variants_only(self):
        # --variants-only flag should limit to graphic variant matches only
        sys.argv = ['dphon',
                    'tests/fixtures/laozi.txt',
                    'tests/fixtures/xiaojing.txt',
                    '--variants-only']
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode().splitlines()
        # only these two matches should be in output
        self.assertEqual(results[0], '以智治 (laozi: 65)')
        self.assertEqual(results[1], '以知之 (xiaojing: 1)')
        self.assertEqual(results[3], '以智治 (laozi: 65)')
        self.assertEqual(results[4], '以知之 (xiaojing: 1)')
        self.assertEqual(len(results), 6)

    def test_n(self):
        # --n option should return matches of at least length n
        sys.argv = ['dphon',
                    'tests/fixtures/shijing1.txt',
                    'tests/fixtures/shijing2.txt',
                    '--n=4']
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode()
        # longer matches are in output, shorter are not
        self.assertIn('未見君子 (shijing1: 58)', results)
        self.assertIn('既見君子 (shijing1: 59)', results)
        self.assertNotIn('葉萋萋 (shijing1: 9)' , results)


class TestIO(TestCase):

    def test_read_files(self):
        # read two files and compare them
        sys.argv = ['dphon',
                    'tests/fixtures/shijing1.txt',
                    'tests/fixtures/shijing2.txt',]
        with patch('sys.stdout.buffer.write') as output:
            run()
            results = output.call_args[0][0].decode().splitlines()
        self.assertEqual(results[0], '君子好 (shijing1: 3)')
        self.assertEqual(results[1], '君子、憂 (shijing2: 64)')

    def test_write_file(self):
        # --output flag should write to a file
        with tempfile.TemporaryDirectory() as tmpdirname:
            outfile = '%s/out.txt' % tmpdirname
            sys.argv = ['dphon',
                        'tests/fixtures/shijing1.txt',
                        'tests/fixtures/shijing2.txt',
                        '--output=%s' % outfile]
            run()
            with open(outfile, encoding='utf-8') as file:
                results = file.read().splitlines()
        self.assertEqual(results[0], '君子好 (shijing1: 3)')
        self.assertEqual(results[1], '君子、憂 (shijing2: 64)')
