#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_memcached
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2020, madkote

tests.test_memcached
--------------------
Module
'''

from __future__ import absolute_import

import asyncio
import unittest
import uuid

import fastapi
import pytest

from . import VERSION

__all__ = []
__author__ = 'roman-telepathy-ai <roman.schroeder(at)telepathy.ai>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2020, Telepathy Labs'


@pytest.mark.memcached
class MemcachedTest(unittest.TestCase):
    def fixture_get_config(self):
        from fastapi_plugins.memcached import MemcachedSettings
        return MemcachedSettings(
            memcached_prestart_tries=10,
            memcached_prestart_wait=1
        )

    def test_connect(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi.FastAPI()
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_ping(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi.FastAPI()
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            try:
                c = await memcached_plugin()
                r = await c.ping()
                self.assertTrue(r, 'set failed')
            finally:
                await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_version(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi.FastAPI()
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            try:
                c = await memcached_plugin()
                r = await c.version()
                self.assertTrue(r, 'set failed')
            finally:
                await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_get_set(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi.FastAPI()
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            try:
                c = await memcached_plugin()
                value = str(uuid.uuid4()).encode()
                r = await c.set(b'x', value)
                self.assertTrue(r, 'set failed')
                r = await c.get(b'x')
                self.assertTrue(r == value, 'get failed')
            finally:
                await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
