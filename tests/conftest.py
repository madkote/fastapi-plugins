#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.conftest
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote

tests.conftest
--------------
PyTest configuration
'''

from __future__ import absolute_import

from . import VERSION

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote'


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "control: mark test related to Control"
    )
    config.addinivalue_line(
        "markers", "scheduler: mark test related to Scheduler"
    )
    config.addinivalue_line(
        "markers", "memcached: mark test related to Memcached"
    )
    config.addinivalue_line(
        "markers", "redis: mark test related to Redis"
    )
    config.addinivalue_line(
        "markers", "fakeredis: mark test related to Fake Redis"
    )
    config.addinivalue_line(
        "markers", "sentinel: mark test related to Redis Sentinel"
    )
    config.addinivalue_line(
        "markers", "settings: mark test related to Settings and Configuration"
    )
    config.addinivalue_line(
        "markers", "logger: mark test related to Logger"
    )
