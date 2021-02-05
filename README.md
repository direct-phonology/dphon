# dphon
[![ci](https://github.com/direct-phonology/dphon/workflows/ci/badge.svg)](https://github.com/direct-phonology/dphon/actions?query=workflow%3Aci)
[![docs](https://github.com/direct-phonology/dphon/workflows/docs/badge.svg)](https://direct-phonology.github.io/dphon)
[![codecov](https://codecov.io/gh/direct-phonology/dphon/branch/main/graph/badge.svg?token=uGbgB5UFtk)](https://codecov.io/gh/direct-phonology/dphon)
![pyup](https://pyup.io/repos/github/direct-phonology/dphon/shield.svg?t=1568910750251)
[![pypi](https://img.shields.io/pypi/v/dphon.svg?style=flat)](https://pypi.org/project/dphon/)
![pyversions](https://img.shields.io/pypi/pyversions/dphon.svg?style=flat)

## installation

this software is tested on the latest versions of macOS, windows, and ubuntu. you will need a supported version of python (above), along with `pip`.

```sh
$ pip install dphon
```

if you're on windows and are seeing incorrectly formatted output in your terminal, have a look at this [stackoverflow answer](https://stackoverflow.com/questions/49476326/displaying-unicode-in-powershell/49481797#49481797).

## usage

### basics
the main function of `dphon` is to look for instances of text reuse in a corpus of old chinese texts. instead of relying purely on graphemes, it does this by performing grapheme-to-phoneme conversion, and determining possible reuse based on whether passages are likely to have _sounded_ similar (or rhymed) when spoken aloud.

you will need to have files stored locally as utf-8 encoded plain-text (`.txt`) or json-lines (`.jsonl`) format. for the former, one file is assumed to represent one document. for the latter, one file can contain any number of lines, each of which is a document, with required keys `id` (a unique identifier) and `text` (text content) and any number of optional keys. you can obtain a representative corpus of old chinese sourced from the kanseki repository via [`direct-phonology/ect-krp`](https://github.com/direct-phonology/ect-krp).

a simple invocation of `dphon` might look like:

```sh
$ dphon text_a.txt text_b.txt
```

which would look for phonetically similar passages between `text_a` and `text_b`. the output will be a list of sequences, with an identifier based on the file's name and an indicator of where in the text the sequence occurs:

```sh
score 9, weighted 1.0
趙怱及齊將顏聚代之 (text_a 107505–107512)
趙蔥及齊將顏聚代李 (text_b 95016–95024)
```

the numbers next to the identifiers are _token indices_, and may vary depending on how the text is tokenized – `dphon` currently uses character-based tokenization. whitespace will be removed, and the output will be aligned to make it easier to spot differences between the two sequences.

the score is an indicator of how many characters in the sequences were a phonetic match, while the weighted score normalizes the score by the length of the match. results are sorted by score, which results in the longest contiguous matches being listed first.

by default, `dphon` only returns matches that display at least one instance of _graphic variation_ – a case where two different graphemes are used in the same place to represent the same sound. if you're interested in all instances of reuse, regardless of graphic variation, you can use the `--all` flag:

```sh
$ dphon --all text_a.txt text_b.txt
```

you can view the full list of command options with:
```sh
$ dphon --help
```

this tool is under active development, and results may vary. to find the version you are running:
```sh
$ dphon --version
```

### advanced usage
by default, `dphon` uses your system's `$PAGER` to display output, since the results can be quite long. on MacOS and Linux, this will likely be `less`, which supports additional options like searching through the output once it's displayed. for more information, see the man page:

```sh
$ man less
```

`dphon` can colorize output for nicer display in the terminal if your pager supports it. to enable this behavior on MacOS and Linux, set `LESS=R`:

```sh
$ export LESS=R
```

if you want to save the results of the run to a file, you can use redirection, in which case colorization will be automatically disabled:

```sh
$ dphon files/*.txt > results.txt
```

alternatively, you can pipe the output of `dphon` to another utility like `sed` for filtering the results further. for example, you could strip out the ideographic space `　` from results to remove the alignments:

```sh
$ dphon files*.txt | sed 's/　//g'
```

## methodology

matching sequences are determined by a "dictionary" file that represents a particular reconstruction of old chinese phonology. these data structures perform grapheme-to-phoneme conversion, yielding the associated sound for each character:

```
"埃": "qˤə"
"哀": "ʔˤəj"
"藹": "qˤats"
...
```

for characters with multiple readings, `dphon` currently chooses the first available reading for comparison. more work is planned for version 3.0 to address this shortcoming.

in version 1.0, `dphon`'s default reconstruction was based on Schuessler 2007[<sup>1</sup>](#note1), but used a single "dummy" character to represent all the lexemes in a particular sound class. [the dictionary](dphon/data/sound_table_v1.json) was compiled by John O'Leary ([@valgrinderror](https://github.com/valgrinderror)) and Gian Duri Rominger ([@GDRom](https://github.com/GDRom)). since version 2.0, `dphon` uses [a dictionary](dphon/data/sound_table_v2.json) based on the Baxter-Sagart 2014 reconstruction[<sup>2</sup>](#note2), with additional work by Gian Duri Rominger.

the matching algorithm is based on Paul Vierthaler's [`chinesetextreuse`](https://github.com/vierth/chinesetextreuse) project, with some modifications. it uses a [BLAST](https://en.wikipedia.org/wiki/BLAST_(biotechnology))-like strategy to identify initial match candidates, and then extend them via phonetic [edit distance](https://en.wikipedia.org/wiki/Edit_distance) comparison. finally, the results are aligned using a version of the [Smith-Waterman algorithm](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm) that operates on phonemes. 

## development setup

**python >=3.6 is required**. 

first, clone the repository:

```sh
$ git clone https://github.com/direct-phonology/dphon.git
$ cd dphon
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
<sup id="note1">1</sup> Schuessler, Axel (2007), ABC Etymological Dictionary of Old Chinese, Honolulu: University of Hawaii Press, ISBN 978-0-8248-2975-9.

<sup id="note2">2</sup> Baxter, William H.; Sagart, Laurent (2014), Old Chinese: A New Reconstruction, Oxford University Press, ISBN 978-0-19-994537-5.