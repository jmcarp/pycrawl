#!/usr/bin/env python

import re
from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'aiohttp>=0.15.3',
    'furl>=0.4.7',
    'pyquery>=1.2.9',
]

test_requirements = [
    'pytest',
]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version


setup(
    name='pycrawl',
    version=find_version('pycrawl/__init__.py'),
    description="Minimal web crawler built on asyncio",
    long_description=readme + '\n\n' + history,
    author="Joshua Carp",
    author_email='jm.carp@gmail.com',
    url='https://github.com/jmcarp/pycrawl',
    packages=['pycrawl'],
    package_dir={'pycrawl': 'pycrawl'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='pycrawl',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
