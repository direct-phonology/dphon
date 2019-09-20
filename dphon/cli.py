"""
dphon
 
Usage:
  dphon <text1> <text2> [--output=<file>]
  dphon -h | --help
  dphon -v | --version
 
Options:
  -h --help         Show this screen.
  -v --version      Show program version.
 
Examples:
    dphon 老子甲.txt 老子乙.txt
    dphon 老子丙.txt 老子乙.txt --output=out.txt
 
Help:
  For more information on using this tool, please visit the Github repository:
  https://github.com/direct-phonology/direct
"""

from sys import stderr, stdin, stdout
from docopt import docopt

from . import __version__
from .lib import Comparator


def run():
    """CLI entrypoint."""
    arguments = docopt(__doc__, version=__version__)
    with open(arguments['<text1>'], encoding='utf-8') as file:
        text1 = file.read()
    with open(arguments['<text2>'], encoding='utf-8') as file:
        text2 = file.read()
    c = Comparator(a=text1,
                   b=text2,
                   a_name=arguments['<text1>'],
                   b_name=arguments['<text2>'])
    matches = c.get_matches()
    groups = Comparator.group_matches(matches)
    output = c.resolve_groups(groups)
    if arguments['--output']:
        with open(arguments['--output'], mode='w', encoding='utf8') as file:
            file.write(output)
    else:
        stdout.buffer.write(output.encode('utf-8'))
