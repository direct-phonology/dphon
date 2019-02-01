"""
dphon
 
Usage:
  dphon [-p] (- | <text>) <search> [--output=<file>]
  dphon -h | --help
  dphon --version
 
Options:
  -h --help         Show this screen.
  -p --punctuation  Include punctuation in matches.
  --version         Show version.
 
Examples:

 
Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/direct-phonology/direct
"""

from inspect import getmembers
from sys import stderr, stdin, stdout

from docopt import docopt

from . import __version__
from .commands import search


def run():
    """CLI entrypoint."""
    import dphon.commands
    arguments = docopt(__doc__, version=__version__)
    # TODO handle stdin
    if arguments['-']:
        pass
    else:
        with open(arguments['<text>']) as file:
            text_string = file.read()
    # we always get the search from a file
    with open(arguments['<search>']) as file:
        search_string = file.read()
    # get the matches
    matches = search(text_string, search_string, arguments['--punctuation'])
    output = ''
    for match in matches:
        output += "{}({}) :: {}({})\n".format(
            match['search_ngram'],
            match['search_pos'],
            match['corpus_ngram'],
            match['corpus_pos']
        )
    if arguments['--output']: # TODO handle stdout
        pass
    else:
        stdout.buffer.write(output.encode('utf-8'))
