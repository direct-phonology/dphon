# dphon
[![ci](https://github.com/direct-phonology/direct/workflows/ci/badge.svg)](https://github.com/direct-phonology/direct/actions?query=workflow%3Aci)
[![docs](https://github.com/direct-phonology/direct/workflows/docs/badge.svg)](https://direct-phonology.github.io/direct)
[![codecov](https://codecov.io/gh/direct-phonology/direct/branch/main/graph/badge.svg?token=uGbgB5UFtk)](https://codecov.io/gh/direct-phonology/direct)
![pyup](https://pyup.io/repos/github/direct-phonology/direct/shield.svg?t=1568910750251)
[![pypi](https://img.shields.io/pypi/v/dphon.svg?style=flat)](https://pypi.org/project/dphon/)
![pyversions](https://img.shields.io/pypi/pyversions/dphon.svg?style=flat)

## installation

this software is tested on the latest versions of macOS, windows, and ubuntu. you will need a supported version of python (above), along with `pip`.

```sh
$ pip install dphon
```

if you're on windows and are seeing incorrectly formatted output in your terminal, have a look at this [stackoverflow answer](https://stackoverflow.com/questions/49476326/displaying-unicode-in-powershell/49481797#49481797).

## usage

the main function of `dphon` is to look for instances of text reuse in a corpus of old chinese texts. instead of relying purely on graphemes, it does this by performing grapheme-to-phoneme conversion, and determining possible reuse based on whether passages are likely to have _sounded_ similar (or rhymed) when spoken aloud.

a simple invocation of `dphon` might look like:

```sh
$ dphon text_a.txt text_b.txt
```

which would look for phonetically similar passages between `text_a` and `text_b`. the output will be a list of sequences, with an identifier based on the file's name and an indicator of where in the text the sequence occurs:

```sh
趙怱及齊將顏聚代之 (text_a 107505–107512)
趙蔥及齊將顏聚代李 (text_b 95016–95024)
```

the numbers next to the identifiers are _token indices_, and may vary depending on how the text is tokenized – `dphon` currently uses character-based tokenization.

the output will be aligned to make it easier to spot differences between the two sequences. in some cases, matches will span multiple lines in the source text, which will be reflected in the output (line breaks will be represented by the ⏎ character).

by default, `dphon` only returns matches that display at least one instance of _graphic variation_ – a case where two different graphemes are used in the same place to represent the same sound. if you're interested in all instances of reuse, regardless of graphic variation, you can use the `--all` flag:

```sh
$ dphon text_a.txt text_b.txt --all
```

you can view the full list of command options with:
```sh
$ dphon --help
```

this tool is under active development, and results may vary. to find the version you are running:
```sh
$ dphon --version
```

## methodology

matching sequences are determined by a "dictionary" file that represents a particular reconstruction of old chinese phonology (you can see some examples in the `dphon/data/` folder). these data structures perform grapheme-to-phoneme conversion, yielding an associated sound for each character:

```
"埃": "qˤə"
"哀": "ʔˤəj"
"藹": "qˤats"
...
```

in version 1.0, `dphon`'s default reconstruction was based on Schuessler 2007[<sup>1</sup>](). since version 2.0, `dphon` uses the Baxter-Sagart 2014 reconstruction[<sup>2</sup>](), with additional work by Gian Duri Rominger (@GDRom).

the matching algorithm is based on Paul Vierthaler's [`chinesetextreuse`](https://github.com/vierth/chinesetextreuse) project, with some modifications. it uses a [BLAST](https://en.wikipedia.org/wiki/BLAST_(biotechnology))-like strategy to identify initial match candidates, and then extend them via phonetic [edit distance](https://en.wikipedia.org/wiki/Edit_distance) comparison. finally, the results are aligned using a version of the [Smith-Waterman algorithm](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm) that operates on phonemes. 

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
$ pip install -r dev-requirements.txt
```

finally, install the package itself in development mode:

```sh
$ pip install -e .
```

now your changes will be automatically picked up when you run `dphon`.

**pull requests should be made against the `develop` branch.**

## code documentation
code documentation is [available on github pages](https://direct-phonology.github.io/dphon) and is automatically generated with `pdoc3` on pushes to `main`.

to build documentation locally:
```sh
$ pdoc --html --output-dir docs dphon
```

## tests
unit tests are written with `unittest`. you can run them with:

```sh
$ python -m unittest
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
<hr/>
<sup>1</sup> Schuessler, Axel (2007), ABC Etymological Dictionary of Old Chinese, Honolulu: University of Hawaii Press, ISBN 978-0-8248-2975-9.

<sup>2</sup> Baxter, William H.; Sagart, Laurent (2014), Old Chinese: A New Reconstruction, Oxford University Press, ISBN 978-0-19-994537-5.