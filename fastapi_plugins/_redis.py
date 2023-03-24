#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins._redis

from __future__ import absolute_import

import enum
import typing

import fastapi
import pydantic
import redis.asyncio as aioredis
import redis.asyncio.sentinel as aioredis_sentinel
import starlette.requests
import tenacity

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin

from .control import ControlHealthMixin
from .utils import Annotated

__all__ = [
    'RedisError', 'RedisType', 'RedisSettings', 'RedisPlugin',
    'redis_plugin', 'depends_redis', 'TRedisPlugin'
]


class RedisError(PluginError):
    pass


@enum.unique
class RedisType(str, enum.Enum):
    redis = 'redis'
    sentinel = 'sentinel'
    fakeredis = 'fakeredis'
    # cluster = 'cluster'


class RedisSettings(PluginSettings):
    redis_type: RedisType = RedisType.redis
    #
    redis_url: str = None
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_user: str = None
    redis_password: str = None
    redis_db: int = None
    # redis_connection_timeout: int = 2
    #
    # redis_pool_minsize: int = 1
    # redis_pool_maxsize: int = None
    redis_max_connections: int = None
    redis_decode_responses: bool = True
    #
    redis_ttl: int = 3600
    #
    # TODO: xxx the customer validator does not work
    # redis_sentinels: typing.List = None
    redis_sentinels: str = None
    redis_sentinel_master: str = 'mymaster'
    #
    # TODO: xxx - should be shared across caches
    redis_prestart_tries: int = 60 * 5  # 5 min
    redis_prestart_wait: int = 1        # 1 second

    def get_redis_address(self) -> str:
        if self.redis_url:
            return self.redis_url
        elif self.redis_db:
            return 'redis://%s:%s/%s' % (
                self.redis_host,
                self.redis_port,
                self.redis_db
            )
        else:
            return 'redis://%s:%s' % (self.redis_host, self.redis_port)

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


class RedisPlugin(Plugin, ControlHealthMixin):
    DEFAULT_CONFIG_CLASS = RedisSettings

    def _on_init(self) -> None:
        self.redis: typing.Union[aioredis.Redis, aioredis_sentinel.Sentinel] = None # noqa E501

    async def _on_call(self) -> typing.Any:
        if self.redis is None:
            raise RedisError('Redis is not initialized')
        #
        if self.config.redis_type == RedisType.sentinel:
            conn = self.redis.master_for(self.config.redis_sentinel_master)
        elif self.config.redis_type == RedisType.redis:
            conn = self.redis
        elif self.config.redis_type == RedisType.fakeredis:
            conn = self.redis
        else:
            raise NotImplementedError(
                'Redis type %s is not implemented' % self.config.redis_type
            )
        #
        conn.TTL = self.config.redis_ttl
        return conn

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
            username=self.config.redis_user,
            password=self.config.redis_password,
            # minsize=self.config.redis_pool_minsize,
            # maxsize=self.config.redis_pool_maxsize,
            max_connections=self.config.redis_max_connections,
            decode_responses=self.config.redis_decode_responses,
        )
        #
        if self.config.redis_type == RedisType.redis:
            address = self.config.get_redis_address()
            method = aioredis.from_url
            # opts.update(dict(timeout=self.config.redis_connection_timeout))
        elif self.config.redis_type == RedisType.fakeredis:
            try:
                import fakeredis.aioredis
            except ImportError:
                raise RedisError(f'{self.config.redis_type} requires fakeredis to be installed')    # noqa E501
            else:
                address = self.config.get_redis_address()
                method = fakeredis.aioredis.FakeRedis.from_url
        elif self.config.redis_type == RedisType.sentinel:
            address = self.config.get_sentinels()
            method = aioredis_sentinel.Sentinel
        else:
            raise NotImplementedError(
                'Redis type %s is not implemented' % self.config.redis_type
            )
        #
        if not address:
            raise ValueError('Redis address is empty')

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(self.config.redis_prestart_tries),
            wait=tenacity.wait_fixed(self.config.redis_prestart_wait),
        )
        async def _inner():
            return method(address, **opts)

        self.redis = await _inner()
        await self.ping()

    async def terminate(self):
        self.config = None
        if self.redis is not None:
            # del self.redis
            self.redis = None
            # self.redis.close()
            # await self.redis.wait_closed()
            # self.redis = None

    async def health(self) -> typing.Dict:
        return dict(
            redis_type=self.config.redis_type,
            redis_address=self.config.get_sentinels() if self.config.redis_type == RedisType.sentinel else self.config.get_redis_address(),  # noqa E501
            redis_pong=(await self.ping())
        )

    async def ping(self):
        if self.config.redis_type == RedisType.redis:
            return await self.redis.ping()
        elif self.config.redis_type == RedisType.fakeredis:
            return await self.redis.ping()
        elif self.config.redis_type == RedisType.sentinel:
            return await self.redis.master_for(self.config.redis_sentinel_master).ping()    # noqa E501
        else:
            raise NotImplementedError(
                'Redis type %s.ping() is not implemented' % self.config.redis_type          # noqa E501
            )


redis_plugin = RedisPlugin()


async def depends_redis(
    conn: starlette.requests.HTTPConnection
) -> aioredis.Redis:
    return await conn.app.state.REDIS()


TRedisPlugin = Annotated[typing.Any, fastapi.Depends(depends_redis)]
