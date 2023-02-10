#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_redis

from __future__ import absolute_import

import uuid

import fastapi
import pytest

import fastapi_plugins
from fastapi_plugins._redis import RedisType


pytestmark = [pytest.mark.anyio, pytest.mark.redis]


@pytest.fixture(params=None)
async def redisapp(request):
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    await fastapi_plugins.redis_plugin.init_app(
        app=app,
        config=request.param or fastapi_plugins.RedisSettings(),
    )
    await fastapi_plugins.redis_plugin.init()
    yield app
    await fastapi_plugins.redis_plugin.terminate()


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(
            fastapi_plugins.RedisSettings(redis_url='redis://localhost:6379/1')
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='fakeredis',
                redis_url='redis://localhost:6379/1'
            ),
            marks=pytest.mark.fakeredis
        ),
    ],
    indirect=['redisapp']
)
async def test_connect_redis_url(redisapp):
    pass


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(fastapi_plugins.RedisSettings()),
        pytest.param(
            fastapi_plugins.RedisSettings(redis_type='fakeredis'),
            marks=pytest.mark.fakeredis
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            ),
            marks=pytest.mark.sentinel
        ),
    ],
    indirect=['redisapp']
)
async def test_connect(redisapp):
    pass


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(fastapi_plugins.RedisSettings()),
        pytest.param(
            fastapi_plugins.RedisSettings(redis_type='fakeredis'),
            marks=pytest.mark.fakeredis
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            ),
            marks=pytest.mark.sentinel
        ),
    ],
    indirect=['redisapp']
)
async def test_ping(redisapp):
    assert (await (await fastapi_plugins.redis_plugin()).ping()) is True


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(fastapi_plugins.RedisSettings()),
        pytest.param(
            fastapi_plugins.RedisSettings(redis_type='fakeredis'),
            marks=pytest.mark.fakeredis
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            ),
            marks=pytest.mark.sentinel
        ),
    ],
    indirect=['redisapp']
)
async def test_health(redisapp):
    assert await fastapi_plugins.redis_plugin.health() == dict(
        redis_type=fastapi_plugins.redis_plugin.config.redis_type,
        redis_address=fastapi_plugins.redis_plugin.config.get_sentinels() if fastapi_plugins.redis_plugin.config.redis_type == RedisType.sentinel else fastapi_plugins.redis_plugin.config.get_redis_address(), # noqa E501
        redis_pong=True
    )


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(fastapi_plugins.RedisSettings()),
        pytest.param(
            fastapi_plugins.RedisSettings(redis_type='fakeredis'),
            marks=pytest.mark.fakeredis
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            ),
            marks=pytest.mark.sentinel
        ),
    ],
    indirect=['redisapp']
)
async def test_get_set(redisapp):
    c = await fastapi_plugins.redis_plugin()
    value = str(uuid.uuid4())
    assert await c.set('x', value) is not None
    assert await c.get('x') == value


@pytest.mark.parametrize(
    'redisapp',
    [
        pytest.param(fastapi_plugins.RedisSettings(redis_ttl=61)),
        pytest.param(
            fastapi_plugins.RedisSettings(redis_type='fakeredis'),
            marks=pytest.mark.fakeredis
        ),
        pytest.param(
            fastapi_plugins.RedisSettings(
                redis_type='sentinel',
                redis_sentinels='localhost:26379'
            ),
            marks=pytest.mark.sentinel
        ),
    ],
    indirect=['redisapp']
)
async def test_get_set_ttl(redisapp):
    c = await fastapi_plugins.redis_plugin()
    value = str(uuid.uuid4())
    assert await c.setex('x', c.TTL, value) is not None
    assert await c.get('x') == value
    assert await c.ttl('x') == fastapi_plugins.redis_plugin.config.redis_ttl


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
