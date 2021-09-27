#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_redis
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote

tests.test_redis
----------------
Redis tests
'''

from __future__ import absolute_import

import asyncio
import unittest
import uuid

# import aioredis
import fastapi
import pytest

import fastapi_plugins

from . import VERSION
from . import d2json

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote'


# def redis_must_be_running(cls):
#     # TODO: This SHOULD be improved
#     try:
#         r = redis.StrictRedis('localhost', port=6379)
#         r.ping()
#     except redis.ConnectionError:
#         redis_running = False
#     else:
#         redis_running = True
#     if not redis_running:
#         for name, attribute in inspect.getmembers(cls):
#             if name.startswith('test_'):
#                 @wraps(attribute)
#                 def skip_test(*args, **kwargs):
#                     pytest.skip("Redis is not running.")
#                 setattr(cls, name, skip_test)
#         cls.setUp = lambda x: None
#         cls.tearDown = lambda x: None
#     return cls


@pytest.mark.redis
class RedisTest(unittest.TestCase):
    def test_connect_redis_url(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_url='redis://localhost:6379/1'
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_connect(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings()
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_ping(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings()
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                r = (await c.ping()).decode()
                self.assertTrue(r == 'PONG', 'ping-pong failed == %s' % r)
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_health(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings()
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                exp = dict(
                    redis_type=config.redis_type,
                    redis_address=config.get_redis_address(),
                    redis_pong='PONG'
                )
                res = await fastapi_plugins.redis_plugin.health()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_get_set(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings()
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                value = str(uuid.uuid4())
                r = await c.set('x', value)
                self.assertTrue(r, 'set failed')
                r = await c.get('x', encoding='utf-8')
                self.assertTrue(r == value, 'get failed')
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_get_set_ttl(self):
        redis_ttl = 61

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(redis_ttl=redis_ttl)
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                value = str(uuid.uuid4())
                r = await c.set('x', value, expire=c.TTL)
                self.assertTrue(r, 'set failed')
                r = await c.get('x', encoding='utf-8')
                self.assertTrue(r == value, 'get failed')
                r = await c.ttl('x')
                self.assertTrue(r == redis_ttl, 'ttl failed')
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()


@pytest.mark.redis
@pytest.mark.sentinel
class RedisSentinelTest(unittest.TestCase):
    def test_connect(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_ping(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                r = (await c.ping()).decode()
                self.assertTrue(r == 'PONG', 'ping-pong failed == %s' % r)
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_health(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                exp = dict(
                    redis_type=config.redis_type,
                    redis_address=config.get_sentinels(),
                    redis_pong='PONG'
                )
                res = await fastapi_plugins.redis_plugin.health()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_get_set(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                value = str(uuid.uuid4())
                r = await c.set('x', value)
                self.assertTrue(r, 'set failed')
                r = await c.get('x', encoding='utf-8')
                self.assertTrue(r == value, 'get failed')
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_get_set_ttl(self):
        redis_ttl = 61

        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379',
                redis_ttl=redis_ttl
            )
            await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
            await fastapi_plugins.redis_plugin.init()
            try:
                c = await fastapi_plugins.redis_plugin()
                value = str(uuid.uuid4())
                r = await c.set('x', value, expire=c.TTL)
                self.assertTrue(r, 'set failed')
                r = await c.get('x', encoding='utf-8')
                self.assertTrue(r == value, 'get failed')
                r = await c.ttl('x')
                self.assertTrue(r == redis_ttl, 'ttl failed')
            finally:
                await fastapi_plugins.redis_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
