# DIRECT
_Digital Intertextual Resonances in Early Chinese Texts_

![CI Status](https://github.com/direct-phonology/direct/workflows/test/badge.svg)
![Dependency Status](https://pyup.io/repos/github/direct-phonology/direct/shield.svg?t=1568910750251)
[![PyPi Version](https://img.shields.io/pypi/v/dphon.svg?style=flat)](https://pypi.org/project/dphon/)
![Python Versions](https://img.shields.io/pypi/pyversions/dphon.svg?style=flat)

## installation

this software is tested on the latest versions of macOS, windows, and ubuntu. you will need a supported version of python (above), along with `pip`.

```sh
$ pip install dphon
```

if you're on windows and are seeing incorrectly formatted output in your terminal, have a look at this [stackoverflow answer](https://stackoverflow.com/questions/49476326/displaying-unicode-in-powershell/49481797#49481797).

## usage

the basic function of DIRECT is to phonologically compare two early chinese texts. you will need to have the files saved locally in utf-8 encoded plain text (`.txt`) format. to compare two texts:

```sh
$ dphon text_a.txt text_b.txt # search text b against text a
```

the output will be a list of character sequences in text_a that have rhyming counterparts in text_b, including the texts and line numbers from which the sequences are drawn:

```sh
滋章盜賊多有 (a: 16)    # this sequence of characters from a line 16 matches
滋彰，盜賊多有 (b: 57)  # this sequence of characters from b line 57
...
不可得 (a: 15)         # this sequence from a on line 15 matches two separate 
不可識 (b: 15)         # locations in b, and both of them are on line 15 in b
不可識 (b: 15)
...
解其忿 (a: 15)         # in this sequence, we see three separate graphic
解其紛 (b: 4)          # variations for the third character - one on a line 15
解其分 (b: 56)         # and two from b on lines 4 and 56
```

note that the matches ignore non-word characters, including punctuation and numbers.
this means that matches could span multiple lines, which will be reflected in the output (line breaks will be represented by the ⏎ character).

you can view the full list of command options with:
```sh
$ dphon --help
```

by default, all matches are shown, including those where the text is identical. to limit to instances
where actual graphic variation has occurred, you can use the `--variants-only` flag:
```sh
$ dphon text_a.txt text_b.txt --variants-only
```

this tool is under active development, and results may vary. to find the version you are running:
```sh
$ dphon --version
```

## methodology

matching sequences are determined by a dictionary file that represents a particular reconstruction of old chinese phonology (you can see some examples in the `dphon/data/` folder). these data structures map an input character to an arbitrary sound token ("dummy") that can be matched against other such tokens.

the core process of DIRECT is to accept plaintext input, tokenize it according to a particular phonological reconstruction, and search for matches amongst the tokenized text. these matches thus represent resonance: sequences that could have rhymed when they were originally read aloud, despite dissimilarity in their written forms.

## development setup

**python >=3.6 is required**. 

first, clone the repository:

```sh
$ git clone https://github.com/direct-phonology/direct.git
$ cd direct
```

then, to create and activate a virtual environment (recommended):

```sh
$ python -m venv venv
$ source venv/bin/activate
```

install dependencies:

```sh
$ pip install -r requirements.txt
$ pip install -r dev-requirements.txt
```

finally, install the package itself in development mode:

```sh
$ pip install -e .
```

now your changes will be automatically picked up when you run `dphon`.

**pull requests should be made against the `develop` branch.**

## tests

unit tests are written with pytest. you can run them with:

```sh
$ pytest
```

## releases

**make sure the version number in `dphon/__init__.py` is correct!**

if there are any built files in `dist/` from older releases, remove them before
you start this process:

```sh
$ rm dist/*
```

to build a source archive and distribution for a release:

```sh
$ python setup.py sdist bdist_wheel
```

to publish the release on [test PyPI](https://test.pypi.org/) (useful for making sure everything worked):

```sh
$ twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

if everything is OK, publish the package to PyPI:

```sh
$ twine upload dist/*
```
