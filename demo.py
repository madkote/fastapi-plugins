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
'''

from __future__ import absolute_import

import asyncio
import time

import fastapi
import pydantic

import fastapi_plugins

VERSION = (1, 0, 0)

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2019, madkote'


class OtherSettings(pydantic.BaseSettings):
    other: str = 'other'


class AppSettings(OtherSettings, fastapi_plugins.RedisSettings):
# class AppSettings(OtherSettings):
    api_name: str = str(__name__)
    #


async def test_redis():
    print('--- do test')
    app = fastapi.FastAPI()
    config = fastapi_plugins.RedisSettings()
    config = None
    config = AppSettings(redis_host='127.0.0.1')
    config = AppSettings()

    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    c = await fastapi_plugins.redis_plugin()
    print(await c.get('x'))
    print(await c.set('x', str(time.time())))
    print(await c.get('x'))
    await fastapi_plugins.redis_plugin.terminate()
    print('---test done')


def main_redis():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_redis())


if __name__ == '__main__':
    main_redis()
