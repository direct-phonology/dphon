"""
dphon
 
Usage:
  dphon ingest (- | <text>) [--output=<file>]
  dphon match [-p] (- | <search>) <corpus> [--output=<file>]
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


def run():
    """CLI entrypoint."""
    import dphon.commands
    arguments = docopt(__doc__, version=__version__)

    # if there's a command that matches the user's argument, run it
    for (arg, value) in arguments.items():
        if hasattr(dphon.commands, arg) and value:
            command = getattr(dphon.commands, arg)
            output = command(arguments)

    # if there was a result, print to stdout or a file
    if output:
        if arguments['--output']:
            pass
        else:
            stdout.buffer.write(output)
