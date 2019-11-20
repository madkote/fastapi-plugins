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

import typing

import aioredis
import fastapi
import pydantic

import fastapi_plugins

VERSION = (0, 1, 0)

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2019, madkote'


class OtherSettings(pydantic.BaseSettings):
    other: str = 'other'


class AppSettings(OtherSettings, fastapi_plugins.RedisSettings):
    api_name: str = str(__name__)


app = fastapi.FastAPI()
config = AppSettings()


@app.get("/")
async def root_get(
        cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
) -> typing.Dict:
    return dict(ping=await cache.ping())


@app.on_event('startup')
async def on_startup() -> None:
    await fastapi_plugins.redis_plugin.init_app(app, config=config)
    await fastapi_plugins.redis_plugin.init()


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await fastapi_plugins.redis_plugin.terminate()
