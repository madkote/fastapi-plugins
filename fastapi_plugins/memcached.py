#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.memcached

from __future__ import absolute_import

import typing

try:
    import aiomcache
except ImportError:
    raise RuntimeError('aiomcache is not installed')

import fastapi
import pydantic
import starlette.requests
import tenacity

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin

from .control import ControlHealthMixin
from .utils import Annotated

__all__ = [
    'MemcachedError', 'MemcachedSettings', 'MemcachedClient',
    'MemcachedPlugin', 'memcached_plugin', 'depends_memcached',
    'TMemcachedPlugin'
]


class MemcachedError(PluginError):
    pass


class MemcachedSettings(PluginSettings):
    memcached_host: str = 'localhost'
    memcached_port: int = 11211
    memcached_pool_size: int = 10
    memcached_pool_minsize: int = 1
    #
    # TODO: xxx - should be shared across caches
    memcached_prestart_tries: int = 60 * 5  # 5 min
    memcached_prestart_wait: int = 1        # 1 second


class MemcachedClient(aiomcache.Client):
    async def ping(self) -> bytes:
        return await self.version()


class MemcachedPlugin(Plugin, ControlHealthMixin):
    DEFAULT_CONFIG_CLASS = MemcachedSettings

    def _on_init(self) -> None:
        self.memcached: MemcachedClient = None

    async def _on_call(self) -> MemcachedClient:
        if self.memcached is None:
            raise MemcachedError('Memcached is not initialized')
        return self.memcached

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise MemcachedError('Memcached configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise MemcachedError('Memcached configuration is not valid')
        app.state.MEMCACHED = self

    async def init(self):
        if self.memcached is not None:
            raise MemcachedError('Memcached is already initialized')
        self.memcached = MemcachedClient(
            host=self.config.memcached_host,
            port=self.config.memcached_port,
            pool_size=2,
            pool_minsize=None
        )

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(
                self.config.memcached_prestart_tries
            ),
            wait=tenacity.wait_fixed(
                self.config.memcached_prestart_wait
            ),
        )
        async def _init_memcached():
            await self.memcached.version()

        try:
            await _init_memcached()
        except Exception as e:
            raise MemcachedError(
                'Memcached initialization failed :: %s :: %s' % (type(e), e)
            )

    async def terminate(self):
        self.config = None
        if self.memcached is not None:
            await self.memcached.flush_all()
            await self.memcached.close()
            self.memcached = None

    async def health(self) -> typing.Dict:
        return dict(
            host=self.config.memcached_host,
            port=self.config.memcached_port,
            version=(await self.memcached.ping()).decode()
        )


memcached_plugin = MemcachedPlugin()


async def depends_memcached(
    conn: starlette.requests.HTTPConnection
) -> MemcachedClient:
    return await conn.app.state.MEMCACHED()


TMemcachedPlugin = Annotated[MemcachedClient, fastapi.Depends(depends_memcached)]   # noqa E501
