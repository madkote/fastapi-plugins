#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup

import codecs
import importlib.util
import os
import sys

from setuptools import setup
from setuptools import find_packages

__author__ = 'madkote <madkote(at)bluewin.ch>'
__copyright__ = 'Copyright 2023, madkote'


if sys.version_info < (3, 6, 0):
    raise RuntimeError("Python 3.6+ required")

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("CHANGES.md", "r") as fh:
    changes_description = fh.read()


def get_version(package_name):
    try:
        version_file = os.path.join(
            os.path.dirname(__file__),
            package_name,
            'version.py'
        )
        spec = importlib.util.spec_from_file_location(
            '%s.version' % package_name,
            version_file
        )
        version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(version_module)
        package_version = version_module.__version__
    except Exception as e:
        raise ValueError(
            'can not determine "%s" version: %s :: %s' % (
                package_name, type(e), e
            )
        )
    else:
        return package_version


def load_requirements(filename):
    def _is_req(s):
        return s and not s.startswith('-r ') and not s.startswith('git+http') and not s.startswith('#')  # noqa E501

    def _read():
        with codecs.open(filename, 'r', encoding='utf-8-sig') as fh:
            for line in fh:
                line = line.strip()
                if _is_req(line):
                    yield line
    return sorted(list(_read()))


def package_files(directory=None):
    paths = []
    if directory:
        for (path, _, filenames) in os.walk(directory):
            for filename in filenames:
                paths.append(os.path.join('..', path, filename))
    return paths


NAME = 'fastapi-plugins'
NAME_PACKAGE = NAME.replace('-', '_')
VERSION = get_version(NAME_PACKAGE)
DESCRIPTION = 'Plugins for FastAPI framework'
URL = 'https://github.com/madkote/%s' % NAME

REQUIRES_INSTALL = [
    'fastapi>=0.74.0',
    'pydantic>=1.0.0,<2.0.0',
    'tenacity>=8.0.0',
    #
    'python-json-logger>=2.0.0',
    'redis[hiredis]>=4.3.0',
    'aiojobs>=1.0.0'
]
REQUIRES_FAKEREDIS = ['fakeredis[lua]>=1.8.0']
REQUIRES_MEMCACHED = ['aiomcache>=0.7.0']
REQUIRES_TESTS = [
    'bandit',
    'docker-compose',
    'flake8',
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'tox',
    'twine',
    #
    'fastapi[all]',
]

REQUIRES_EXTRA = {
    'all': REQUIRES_MEMCACHED,
    'fakeredis': REQUIRES_FAKEREDIS,
    'memcached': REQUIRES_MEMCACHED,
    'dev': REQUIRES_MEMCACHED + REQUIRES_FAKEREDIS + REQUIRES_TESTS,
}

PACKAGES = find_packages(exclude=('scripts', 'tests'))
PACKAGE_DATA = {'': []}


# =============================================================================
# SETUP
# =============================================================================
setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    author='madkote',
    author_email=__author__.replace('(at)', '@'),
    url=URL,
    download_url=URL + '/archive/{}.tar.gz'.format(VERSION),
    license='MIT License',
    keywords=[
        'async', 'redis', 'aioredis', 'json', 'asyncio', 'plugin', 'fastapi',
        'aiojobs', 'scheduler', 'starlette', 'memcached', 'aiomcache'
    ],
    install_requires=REQUIRES_INSTALL,
    tests_require=REQUIRES_TESTS,
    extras_require=REQUIRES_EXTRA,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    python_requires='>=3.6.0',
    include_package_data=True,
    long_description='\n\n'.join((long_description, changes_description)),
    long_description_content_type='text/markdown',
    platforms=['any'],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
        'Framework :: AsyncIO',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
    ]
)
