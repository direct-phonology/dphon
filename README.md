# DIRECT
_Digital Intertextual Resonances in Early Chinese Texts_

[![Build Status](https://travis-ci.org/direct-phonology/direct.svg?branch=master)](https://travis-ci.org/direct-phonology/direct)
![PyPi Version](https://img.shields.io/pypi/v/dphon.svg?style=flat)
![Python Versions](https://img.shields.io/pypi/pyversions/dphon.svg?style=flat)
![License](https://img.shields.io/pypi/l/dphon.svg?style=flat)

## installation

install with pip:

```sh
$ pip install dphon
```

## usage

the basic function of DIRECT is to phonologically compare two early chinese texts. you will need to have the files saved locally in utf-8 encoded plain text (`.txt`) format. to compare two texts:

```sh
$ dphon text_a.txt text_b.txt # search text b against text a
```

the output will be a list of matching n-grams between the two texts, including the line numbers from which the matches are drawn:

```sh
揣而兌之(1277) :: 揣而銳之(531) # line 1277b matches line 531a
不可上保(1282) :: 不可長保(536) # line 1282b matches line 536a
工遂申墜(1307) :: 功遂身退(561) # line 1307b matches line 561a
...
```

you can view the full list of command options with:
```sh
$ dphon --help
```

## development setup

**python 3 is required**. 

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
