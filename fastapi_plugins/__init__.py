#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.__init__
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2019, madkote

fastapi_plugins
---------------
FastAPI plugins

fake     -> simple dictionary  -> TODO: xxx

# TODO: xxx tests with docker
# TODO: xxx later split into different modules
'''

from __future__ import absolute_import

import enum
import typing

import aioredis
import fastapi
import pydantic
import starlette.requests
import tenacity

from .version import VERSION

__all__ = [
    'PluginError', 'PluginSettings', 'Plugin',

    'RedisError', 'RedisType', 'RedisSettings', 'RedisPlugin',
    'redis_plugin', 'depends_redis'
]
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2019, madkote'


class PluginError(Exception):
    pass


class PluginSettings(pydantic.BaseSettings):
    class Config:
        env_prefix = ''
        use_enum_values = True


class Plugin:
    DEFAULT_CONFIG_CLASS: pydantic.BaseSettings = None

    def __init__(
            self,
            app: fastapi.FastAPI=None,
            config: pydantic.BaseSettings=None
    ):
        self._on_init()
        if app and config:
            self.init_app(app, config)

    def __call__(self) -> typing.Any:
        return self._on_call()

    def _on_init(self) -> None:
        pass

#     def is_initialized(self) -> bool:
#         raise NotImplementedError('implement is_initialied()')

    async def _on_call(self) -> typing.Any:
        raise NotImplementedError('implement _on_call()')

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None
    ) -> None:
        pass

    async def init(self):
        pass

    async def terminate(self):
        pass


class RedisError(PluginError):
    pass


@enum.unique
class RedisType(str, enum.Enum):
    redis = 'redis'
    sentinel = 'sentinel'
    fake = 'fake'


class RedisSettings(PluginSettings):
    redis_type: RedisType = RedisType.redis
    #
    redis_url: str = None
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = None
    redis_db: int = 0
    redis_connection_timeout: int = 2
    #
    redis_pool_minsize: int = 1
    redis_pool_maxsize: int = 10
    #
    # TODO: xxx how to keep track of TTL - time to expire, which is set
    #       only by the command
    # cache_ttl: int = 24 * 3600
    #
    # TODO: xxx the customer validator does not work
    # redis_sentinels: typing.List = None
    redis_sentinels: str = None
    redis_sentinel_master: str = 'mymaster'
    #
    # TODO: xxx here fake redis
    # ...
    #
    redis_prestart_tries: int = 60 * 5  # 5 min
    redis_prestart_wait: int = 1        # 1 second

    def get_redis_address(self) -> str:
        return 'redis://%s:%s/%s' % (
            self.redis_host,
            self.redis_port,
            self.redis_db
        )

    # TODO: xxx the customer validator does not work
    def get_sentinels(self) -> typing.List:
        if self.redis_sentinels:
            try:
                return [
                    (
                        _conn.split(':')[0].strip(),
                        int(_conn.split(':')[1].strip())
                    )
                    for _conn in self.redis_sentinels.split(',')
                    if _conn.strip()
                ]
            except Exception as e:
                raise RuntimeError(
                    'bad sentinels string :: %s :: %s :: %s' % (
                        type(e), str(e), self.redis_sentinels
                    )
                )
        else:
            return []

# TODO: xxx mock connection
# class MyConnection(aioredis.RedisConnection):
#     pass


class RedisPlugin(Plugin):
    DEFAULT_CONFIG_CLASS = RedisSettings

    def _on_init(self) -> None:
        self.redis: aioredis.Redis = None

    async def _on_call(self) -> typing.Any:
        if self.redis is None:
            raise RedisError('Redis is not initialized')
        # TODO: xxx dot it better without IF
        if self.config.redis_type == RedisType.sentinel:
            return self.redis.master_for(self.config.redis_sentinel_master)
        else:
            return self.redis

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise RedisError('Redis configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise RedisError('Redis configuration is not valid')
        app.state.REDIS = self

    async def init(self):
        if self.redis is not None:
            raise RedisError('Redis is already initialized')
        #
        opts = dict(
            db=self.config.redis_db,
            password=self.config.redis_password,
            minsize=self.config.redis_pool_minsize,
            maxsize=self.config.redis_pool_maxsize,
            #
            # TODO: xxx mock connection
            # connection_cls=MyConnection
        )
        #
        if self.config.redis_type == RedisType.redis:
            address = self.config.get_redis_address()
            method = aioredis.create_redis_pool
            opts.update(dict(timeout=self.config.redis_connection_timeout))
        elif self.config.redis_type == RedisType.sentinel:
            address = self.config.get_sentinels()
            method = aioredis.create_sentinel
        else:
            raise NotImplementedError(
                'Redis type %s is not implemented' % self.config.redis_type
            )
        #
        if not address:
            raise ValueError('redis address is empty')

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(self.config.redis_prestart_tries),
            wait=tenacity.wait_fixed(self.config.redis_prestart_wait),
        )
        async def _inner():
            return await method(address, **opts)

        self.redis = await _inner()

    async def terminate(self):
        self.config = None
        if self.redis is not None:
            self.redis.close()
            await self.redis.wait_closed()
            self.redis = None


redis_plugin = RedisPlugin()


async def depends_redis(request: starlette.requests.Request) -> aioredis.Redis:
    return await request.app.state.REDIS()
