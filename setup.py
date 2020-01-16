"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from dphon import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=direct', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name='dphon',
    description='Tools for Old Chinese phonological analysis.',
    version=__version__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/direct-phonology/direct',
    include_package_data=True,  # include extra data files, e.g. dictionaries
    author='John O\'Leary, Nick Budak, Gian Rominger',
    author_email='jo10@princeton.edu, nbudak@princeton.edu, gianr@princeton.edu',
    license='MIT',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Chinese (Traditional)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6',
    keywords='cli old chinese phonology linguistics',
    project_urls={
        'Source': 'https://github.com/direct-phonology/direct',
        'Tracker': 'https://github.com/direct-phonology/direct/issues',
    },
    packages=find_packages(),
    install_requires=['docopt'],
    extras_require={
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    entry_points={
        'console_scripts': [
            'dphon=dphon.cli:run',
        ],
    },
    cmdclass={'test': RunTests},
)
