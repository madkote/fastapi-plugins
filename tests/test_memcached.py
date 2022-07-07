#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_memcached
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote

tests.test_memcached
--------------------
Memcached tests
'''

from __future__ import absolute_import

import asyncio
import unittest
import uuid

import fastapi
import fastapi_plugins
import pytest

from . import VERSION
from . import d2json

__all__ = []
__author__ = 'roman-telepathy-ai <roman.schroeder(at)telepathy.ai>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, Telepathy Labs'


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
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_ping(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
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
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_health(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = self.fixture_get_config()
            await memcached_plugin.init_app(app=app, config=config)
            await memcached_plugin.init()
            try:
                exp = dict(
                    host=config.memcached_host,
                    port=config.memcached_port,
                    version='1.6.15'
                )
                res = await memcached_plugin.health()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await memcached_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_version(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
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
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_get_set(self):
        from fastapi_plugins.memcached import memcached_plugin

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
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
        event_loop.run_until_complete(_test())
        event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
