#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2019, madkote

setup
-----
Setup script

https://pypi.org/pypi?%3Aaction=list_classifiers
'''

from __future__ import absolute_import

import imp
import os
import sys

from setuptools import setup
from setuptools import find_packages

__author__ = 'madkote <madkote(at)bluewin.ch>'
__copyright__ = 'Copyright 2019, madkote'


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
        version_module = imp.load_source(
            '%s.version' % package_name,
            version_file
        )
        package_version = version_module.__version__
    except Exception as e:
        raise ValueError('can not determine "%s" version: %s :: %s' % (
            package_name, type(e), e)
        )
    else:
        return package_version


NAME = 'fastapi-plugins'
NAME_PACKAGE = NAME.replace('-', '_')
VERSION = get_version(NAME_PACKAGE)
DESCRIPTION = 'Plugins for FastAPI framework'
URL = 'https://github.com/madkote/fastapi-plugins'
REQUIRES_INSTALL = [
    'aioredis==1.3.*',
    'fastapi>=0.41.*',
]
REQUIRES_DEV = [
    'docker-compose',
    'm2r',
    'uvicorn',
]
REQUIRES_TESTS = REQUIRES_DEV + [
    'flake8',
    'pytest',
    'pytest-cov',
    'tox',
]
REQUIRES_EXTRA = {
    'dev':  REQUIRES_DEV,
    'test': REQUIRES_TESTS
}
PACKAGES = find_packages(exclude=('scripts', 'tests'))


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
        'async', 'redis', 'aioredis', 'json', 'asyncio', 'plugin', 'fastapi'
    ],
    install_requires=REQUIRES_INSTALL,
    tests_require=REQUIRES_TESTS,
    extras_require=REQUIRES_EXTRA,
    packages=PACKAGES,
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
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
        'Framework :: AsyncIO',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
    ]
)
