#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_memcached

from __future__ import absolute_import

import uuid

import fastapi
import fastapi_plugins
import pytest

from fastapi_plugins.memcached import memcached_plugin, MemcachedSettings


pytestmark = [pytest.mark.anyio, pytest.mark.memcached]


@pytest.fixture
def memcache_config():
    return MemcachedSettings(
        memcached_prestart_tries=10,
        memcached_prestart_wait=1
    )


@pytest.fixture
async def memcache_app(memcache_config):
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    await memcached_plugin.init_app(app=app, config=memcache_config)
    await memcached_plugin.init()
    yield app
    await memcached_plugin.terminate()


async def test_connect(memcache_app):
    pass


async def test_ping(memcache_app):
    assert (await (await memcached_plugin()).ping()) is not None


async def test_health(memcache_app):
    assert await memcached_plugin.health() == dict(
        host=memcached_plugin.config.memcached_host,
        port=memcached_plugin.config.memcached_port,
        version='1.6.18'
    )


async def test_version(memcache_app):
    assert await (await memcached_plugin()).version() is not None


async def test_get_set(memcache_app):
    c = await memcached_plugin()
    value = str(uuid.uuid4()).encode()
    assert await c.set(b'x', value) is not None
    assert await c.get(b'x') == value
