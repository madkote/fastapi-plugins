#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.conftest

from __future__ import absolute_import

import asyncio

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "control: tests for Control")
    config.addinivalue_line("markers", "scheduler: tests for Scheduler")
    config.addinivalue_line("markers", "memcached: tests for Memcached")
    config.addinivalue_line("markers", "redis: tests for Redis")
    config.addinivalue_line("markers", "fakeredis: tests for Fake Redis")
    config.addinivalue_line("markers", "sentinel: tests for Redis Sentinel")
    config.addinivalue_line("markers", "settings: tests for Settings and Configuration")    # noqa E501
    config.addinivalue_line("markers", "logger: tests for Logger")


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='session', autouse=True)
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
