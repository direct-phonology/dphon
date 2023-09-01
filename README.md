# dphon
[![ci](https://github.com/direct-phonology/dphon/workflows/ci/badge.svg)](https://github.com/direct-phonology/dphon/actions?query=workflow%3Aci)
[![codecov](https://codecov.io/gh/direct-phonology/dphon/branch/main/graph/badge.svg?token=uGbgB5UFtk)](https://codecov.io/gh/direct-phonology/dphon)
![pyversions](https://img.shields.io/pypi/pyversions/dphon.svg?style=flat)
[![zenodo](https://zenodo.org/badge/DOI/10.5281/zenodo.4641277.svg)](https://zenodo.org/record/4641277)
[![spaCy](https://img.shields.io/static/v1?label=made%20with%20%E2%9D%A4%20and&message=spaCy&color=09a3d5)](https://spacy.io)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

which would look for phonetically similar passages between `text_a` and `text_b`. the output will be a list of sequences and their phonemic transcriptions, with an identifier based on the file's name and an indicator of where in the text the sequence occurs:

```sh
1.  text_a (2208–2216)：
    夏后啟曰以為可為故為之為之天下弗能
    *ləʔ ɢʷraj kʰˤajʔ ɢʷraj kˤaʔs ɢʷraj tə ɢʷraj tə
2.  text_b (3340–3348)：
    不可弗爲以爲可　故爲之爲之繇其道物
    *ləʔ ɢʷraj kʰˤajʔ kˤaʔs ɢʷraj tə ɢʷraj tə pit
```

the numbers next to the identifiers are _token indices_, and may vary depending on how the text is tokenized – `dphon` currently uses character-based tokenization. whitespace will be removed, and the output will be aligned to make it easier to spot differences between the two sequences. by default, insertions are highlighted in green, and mismatches (differences between the two sequences) are highlighted in red. additional (non-matching) context added to either side of match sequences is displayed using a dimmed color (see "advanced usage" below for more information on colorization).

matches are sorted by the ratio of their phomenic similarity to their graphic similarity – in other words, matches between texts that sound highly similar but were written very differently will be at the top of the list. 

by default, `dphon` only returns matches that display at least one instance of _graphic variation_ – a case where two different graphemes are used in the same place to represent the same sound. these cases are highlighted in blue. if you're interested in all instances of reuse, regardless of graphic variation, you can use the `--all` flag:

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

if you want to save the results of the run to a file, you can use redirection. this is useful when writing structured formats like .csv and .jsonl. you can also write html to preserve colors:

```sh
$ dphon -o html files/*.txt > results.html
```

alternatively, you can pipe the output of `dphon` to another utility like `sed` for filtering the results further. for example, you could strip out the ideographic space `　` from results to remove the alignments:

```sh
$ dphon files/*.txt | sed 's/　//g'
```

## methodology

matching sequences are determined by a "dictionary" file that represents a particular reconstruction of old chinese phonology. these data structures perform grapheme-to-phoneme conversion, yielding the associated sound for each character:

```
"埃": "qˤə"
"哀": "ʔˤəj"
"藹": "qˤats"
...
```

if two characters have the same phonemes, they're treated as a match. for characters with multiple readings, `dphon` currently chooses the first available reading for comparison. more work is planned for version 3.0 to address this shortcoming.

in version 1.0, `dphon`'s default reconstruction was based on Schuessler 2007[<sup>1</sup>](#note1), but used a single "dummy" character to represent all the lexemes in a rhyming group. [the dictionary](dphon/data/sound_table_v1.json) was compiled by John O'Leary ([@valgrinderror](https://github.com/valgrinderror)) and Gian Duri Rominger ([@GDRom](https://github.com/GDRom)). since version 2.0, `dphon` uses [a dictionary](dphon/data/sound_table_v2.json) based on the Baxter-Sagart 2014 reconstruction[<sup>2</sup>](#note2), with additional work by Rominger.

the matching algorithm is based on Paul Vierthaler's [`chinesetextreuse`](https://github.com/vierth/chinesetextreuse) project[<sup>3</sup>](#note3), with some modifications. it uses a [BLAST](https://en.wikipedia.org/wiki/BLAST_(biotechnology))-like strategy to identify initial match candidates, and then extend them via phonetic [edit distance](https://en.wikipedia.org/wiki/Edit_distance) comparison. finally, the results are aligned using a version of the [Smith-Waterman algorithm](https://en.wikipedia.org/wiki/Smith%E2%80%93Waterman_algorithm) that operates on phonemes, powered by the `lingpy` library[<sup>4</sup>](#note4).

## development setup

**python >=3.7 is required**. 

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

pull requests can be made against `main`.
## code documentation
code documentation is [available on github pages](https://direct-phonology.github.io/dphon) and is generated with `pdoc3`.

to build the docs:
```sh
$ pdoc --html --output-dir docs dphon
```

## tests
unit tests are written with `unittest`. you can run them with:

```sh
$ python -m unittest
```


## releases

the package is built and published to pyPI automatically using `twine` when using GitHub's release functionality.

**make sure the version number in `dphon/__init__.py` is correct!**

<hr/>
<sup id="note1">1</sup> Schuessler, Axel (2007), _ABC Etymological Dictionary of Old Chinese_, Honolulu: University of Hawaii Press, ISBN 978-0-8248-2975-9.

<sup id="note2">2</sup> Baxter, William H.; Sagart, Laurent (2014), _Old Chinese: A New Reconstruction_, Oxford University Press, ISBN 978-0-19-994537-5.

<sup id="note3">3</sup> Vierthaler, Paul, and Mees Gelein. “A BLAST-Based, Language-Agnostic Text Reuse Algorithm with a MARKUS Implementation and Sequence Alignment Optimized for Large Chinese Corpora,” April 26, 2019. https://doi.org/10.31235/osf.io/7xpqe.

<sup id="note4">4</sup> List, Johann-Mattis; Greenhill, Simon; Tresoldi, Tiago; and Forkel, Robert (2019): **LingPy. A Python library for historical linguistics**. Version 2.6.5. URL: http://lingpy.org, DOI: https://zenodo.org/badge/latestdoi/5137/lingpy/lingpy. With contributions by Christoph Rzymski, Gereon Kaiping, Steven Moran, Peter Bouda, Johannes Dellert, Taraka Rama, Frank Nagel. Jena: Max Planck Institute for the Science of Human History.
