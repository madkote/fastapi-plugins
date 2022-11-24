#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.conftest

from __future__ import absolute_import


def pytest_configure(config):
    config.addinivalue_line("markers", "control: tests for Control")
    config.addinivalue_line("markers", "scheduler: tests for Scheduler")
    config.addinivalue_line("markers", "memcached: tests for Memcached")
    config.addinivalue_line("markers", "redis: tests for Redis")
    config.addinivalue_line("markers", "fakeredis: tests for Fake Redis")
    config.addinivalue_line("markers", "sentinel: tests for Redis Sentinel")
    config.addinivalue_line("markers", "settings: tests for Settings and Configuration")    # noqa E501
    config.addinivalue_line("markers", "logger: tests for Logger")
