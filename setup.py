"""Packaging settings for dphon."""

import pathlib

from setuptools import find_packages, setup

from dphon import __version__

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf8")

setup(
    name="dphon",
    version=__version__,
    description="Tools and algorithms for phonology-aware Early Chinese NLP.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/direct-phonology/dphon",
    include_package_data=True,
    author="Nick Budak",
    author_email="nbudak@princeton.edu",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Traditional)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Utilities",
    ],
    keywords="old chinese, phonology, linguistics, nlp",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=["docopt", "spacy>=3",
                      "python-levenshtein", "lingpy", "rich", "jsonlines"],
    extras_require={
        "dev": ["check-manifest", "mypy", "pylint"],
        "test": ["coverage"],
    },
    entry_points={
        "console_scripts": [
            "dphon=dphon.cli:run",
        ],
        "spacy_factories": [
            "ngrams=dphon.ngrams:create_ngrams",
            "g2p=dphon.g2p:create_graphemes_to_phonemes",
            "ngram_phonemes_index=dphon.index:create_ngram_phonemes_lookup_index",
        ]
    },
    project_urls={
        "Source": "https://github.com/direct-phonology/dphon",
        "Tracker": "https://github.com/direct-phonology/dphon/issues",
    },
)
