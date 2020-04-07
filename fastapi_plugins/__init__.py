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

# import abc
# import asyncio
import enum
import typing
# import uuid

import aiojobs
import aioredis
import fastapi
import pydantic
import starlette.requests
import tenacity

from .version import VERSION

__all__ = [
    'PluginError', 'PluginSettings', 'Plugin',

    'RedisError', 'RedisType', 'RedisSettings', 'RedisPlugin',
    'redis_plugin', 'depends_redis',

    'SchedulerError', 'SchedulerSettings', 'SchedulerPlugin',
    'scheduler_plugin', 'depends_scheduler',
    # 'MadnessScheduler',
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


class SchedulerError(PluginError):
    pass


# class MadnessScheduler(aiojobs.Scheduler):
#     def __init__(self, *args, **kwargs):
#         super(MadnessScheduler, self).__init__(*args, **kwargs)
#         self._job_map = {}
#
#     async def spawn(self, coro):
#         job = await aiojobs.Scheduler.spawn(self, coro)
#         self._job_map[job.id] = job
#         return job
#
#     def _done(self, job) -> None:
#         if job.id in self._job_map:
#             self._job_map.pop(job.id)
#         return aiojobs.Scheduler._done(self, job)
#
#     async def cancel_job(self, job_id: str) -> None:
#         if job_id in self._job_map:
#             await self._job_map[job_id].close()
#
#
# async def create_madness_scheduler(
#     *args,
#     close_timeout=0.1,
#     limit=100,
#     pending_limit=10000,
#     exception_handler=None
# ) -> MadnessScheduler:
#     if exception_handler is not None and not callable(exception_handler):
#         raise TypeError(
#             'A callable object or None is expected, got {!r}'.format(
#                 exception_handler
#             )
#         )
#     loop = asyncio.get_event_loop()
#     return MadnessScheduler(
#         loop=loop,
#         close_timeout=close_timeout,
#         limit=limit,
#         pending_limit=pending_limit,
#         exception_handler=exception_handler
#     )


# TODO: test settings (values)
# TODO: write unit tests
class SchedulerSettings(PluginSettings):
    aiojobs_close_timeout: float = 0.1
    aiojobs_limit: int = 100
    aiojobs_pending_limit: int = 10000
    # aiojobs_enable_cancel: bool = False


class SchedulerPlugin(Plugin):
    DEFAULT_CONFIG_CLASS = SchedulerSettings

    def _on_init(self) -> None:
        self.scheduler: aiojobs.Scheduler = None

    async def _on_call(self) -> aiojobs.Scheduler:
        if self.scheduler is None:
            raise SchedulerError('Scheduler is not initialized')
        return self.scheduler

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise SchedulerError('Scheduler configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise SchedulerError('Scheduler configuration is not valid')
        app.state.AIOJOBS_SCHEDULER = self

    async def init(self):
        if self.scheduler is not None:
            raise SchedulerError('Scheduler is already initialized')
        factory = aiojobs.create_scheduler
        #
        # TODO: monkey patching is not preferred way, but waiting for aoilibs
        #
        # TODO: provide a pull request (custom, job, better scheduler)
        #
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#         if self.config.aiojobs_enable_cancel:
#             class _PatchJob(aiojobs._scheduler.Job):
#                 def __init__(self, *args, **kwargs):
#                     super(_PatchJob, self).__init__(*args, **kwargs)
#                     self._id = str(uuid.uuid4())
#
#                 @property
#                 def id(self):
#                     return self._id
#             aiojobs._scheduler.Job = _PatchJob
#             factory = create_madness_scheduler
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.scheduler = await factory(
            close_timeout=self.config.aiojobs_close_timeout,
            limit=self.config.aiojobs_limit,
            pending_limit=self.config.aiojobs_pending_limit
        )

    async def terminate(self):
        self.config = None
        if self.scheduler is not None:
            await self.scheduler.close()
            self.scheduler = None


scheduler_plugin = SchedulerPlugin()


async def depends_scheduler(
    request: starlette.requests.Request
) -> aiojobs.Scheduler:
    return await request.app.state.AIOJOBS_SCHEDULER()


# TODO: health
# TODO: databases
# TODO: mq - activemq, rabbitmq, kafka
# TODO: celery
# TODO: logging - simple? or more complex example? -> will decide later
# ... more?
