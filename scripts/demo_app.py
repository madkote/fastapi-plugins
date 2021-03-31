#!/usr/bin/env python
# -*- coding: utf-8 -*-
# demo
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2019, madkote

demo
----
Demo

uvicorn demo_app:app
'''

from __future__ import absolute_import

import asyncio
import typing
import uuid

import aiojobs
import aioredis
import fastapi
import pydantic
import starlette.status

try:
    import fastapi_plugins
except ImportError:
    import os
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # noqa E501
    import fastapi_plugins

from fastapi_plugins.memcached import MemcachedSettings
from fastapi_plugins.memcached import MemcachedClient
from fastapi_plugins.memcached import depends_memcached
from fastapi_plugins.memcached import memcached_plugin

VERSION = (0, 1, 2)

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2019, madkote'


class OtherSettings(pydantic.BaseSettings):
    other: str = 'other'


@fastapi_plugins.registered_configuration
class AppSettings(
        OtherSettings,
        fastapi_plugins.ControlSettings,
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings,
        MemcachedSettings,
):
    api_name: str = str(__name__)


@fastapi_plugins.registered_configuration(name='sentinel')
class AppSettingsSentinel(AppSettings):
    redis_type = fastapi_plugins.RedisType.sentinel
    redis_sentinels = 'localhost:26379'


@fastapi_plugins.registered_configuration_local
class AppSettingsLocal(AppSettings):
    pass


app = fastapi.FastAPI()
config = fastapi_plugins.get_config()


@app.get("/")
async def root_get(
        cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
        conf: pydantic.BaseSettings=fastapi.Depends(fastapi_plugins.depends_config) # noqa E501
) -> typing.Dict:
    return dict(ping=await cache.ping(), api_name=conf.api_name)


@app.post("/jobs/schedule/<timeout>")
async def job_post(
    timeout: int=fastapi.Query(..., title='the job sleep time'),
    cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
    scheduler: aiojobs.Scheduler=fastapi.Depends(fastapi_plugins.depends_scheduler),  # noqa E501
) -> str:
    async def coro(job_id, timeout, cache):
        await cache.set(job_id, 'processing')
        try:
            await asyncio.sleep(timeout)
            if timeout == 8:
                raise Exception('ugly error')
        except asyncio.CancelledError:
            await cache.set(job_id, 'canceled')
        except Exception:
            await cache.set(job_id, 'erred')
        else:
            await cache.set(job_id, 'success')

    job_id = str(uuid.uuid4()).replace('-', '')
    await cache.set(job_id, 'pending')
    await scheduler.spawn(coro(job_id, timeout, cache))
    return job_id


@app.get("/jobs/status/<job_id>")
async def job_get(
    job_id: str=fastapi.Query(..., title='the job id'),
    cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
) -> typing.Dict:
    status = await cache.get(job_id)
    if status is None:
        raise fastapi.HTTPException(
            status_code=starlette.status.HTTP_404_NOT_FOUND,
            detail='Job %s not found' % job_id
        )
    return dict(job_id=job_id, status=status)


@app.post("/memcached/demo/<key>")
async def memcached_demo_post(
    key: str=fastapi.Query(..., title='the job id'),
    cache: MemcachedClient=fastapi.Depends(depends_memcached),
) -> typing.Dict:
    await cache.set(key.encode(), str(key + '_value').encode())
    value = await cache.get(key.encode())
    return dict(ping=(await cache.ping()).decode(), key=key, value=value)


@app.on_event('startup')
async def on_startup() -> None:
    await fastapi_plugins.config_plugin.init_app(app, config)
    await fastapi_plugins.config_plugin.init()
    await memcached_plugin.init_app(app, config)
    await memcached_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()
    await fastapi_plugins.control_plugin.init_app(
        app,
        config=config,
        version=__version__,
        environ=config.dict()
    )
    await fastapi_plugins.control_plugin.init()


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await fastapi_plugins.control_plugin.terminate()
    await fastapi_plugins.scheduler_plugin.terminate()
    await fastapi_plugins.redis_plugin.terminate()
    await memcached_plugin.terminate()
    await fastapi_plugins.config_plugin.terminate()
