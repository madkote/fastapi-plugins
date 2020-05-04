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
import os
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


class AppSettings(
        OtherSettings,
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings
):
    api_name: str = str(__name__)


async def test_redis():
    print('--- do redis test')
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
    print('---test redis done')


async def test_scheduler():
    async def coro(name, timeout):
        try:
            print('> sleep', name, timeout)
            await asyncio.sleep(timeout)
            print('---> sleep done', name, timeout)
        except asyncio.CancelledError as e:
            print('coro cancelled', name)
            raise e

    print('--- do schedule test')
    app = fastapi.FastAPI()
    config = fastapi_plugins.SchedulerSettings()
    config = None
    config = AppSettings(aiojobs_limit=100)
    config = AppSettings()
    # config = AppSettings(aiojobs_limit=1)

    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()
    try:
        print('- play')
        s = await fastapi_plugins.scheduler_plugin()
        # import random
        for i in range(10):
            await s.spawn(coro(str(i), i/10))
            # await s.spawn(coro(str(i), i/10 + random.choice([0.1, 0.2, 0.3, 0.4, 0.5])))  # nosec B311
        # print('----------')
        print('- sleep', 5)
        await asyncio.sleep(5.0)
        print('- terminate')
    finally:
        await fastapi_plugins.scheduler_plugin.terminate()
        print('---test schedule done')


# async def test_scheduler_enable_cancel():
#     async def coro(name, timeout):
#         try:
#             print('> sleep', name, timeout)
#             await asyncio.sleep(timeout)
#             print('---> sleep done', name, timeout)
#         except asyncio.CancelledError as e:
#             print('coro cancelled', name)
#             raise e
#
#     print('--- do schedule test')
#     app = fastapi.FastAPI()
#     config = fastapi_plugins.SchedulerSettings()
#     config = None
#     config = AppSettings(aiojobs_limit=100)
#     config = AppSettings(aiojobs_enable_cancel=True)
#
#     await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
#     await fastapi_plugins.scheduler_plugin.init()
#     try:
#         print('- play')
#         s = await fastapi_plugins.scheduler_plugin()
#         jobs = []
#         for i in range(2):
#             job = await s.spawn(coro(str(i), 12.75))
#             jobs.append(job.id)
#         print('- sleep', 2)
#         await asyncio.sleep(2.0)
#         print('- cancel')
#         for job_id in jobs:
#             await s.cancel_job(job_id)
#         print('- terminate')
#     finally:
#         await fastapi_plugins.scheduler_plugin.terminate()
#         print('---test schedule done')


async def test_demo():
    async def coro(con, name, timeout):
        try:
            await con.set(name, '...')
            print('> sleep', name, timeout)
            await asyncio.sleep(timeout)
            await con.set(name, 'done')
            print('---> sleep done', name, timeout)
        except asyncio.CancelledError as e:
            print('coro cancelled', name)
            raise e

    print('--- do demo')
    app = fastapi.FastAPI()
    config = AppSettings()

    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_sleep = 0.25

        print('- play')
        c = await fastapi_plugins.redis_plugin()
        s = await fastapi_plugins.scheduler_plugin()
        for i in range(num_jobs):
            await s.spawn(coro(c, str(i), i/10))
        print('- sleep', num_sleep)
        await asyncio.sleep(num_sleep)
        print('- check')
        for i in range(num_jobs):
            print(i, '==', await c.get(str(i)))
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        print('---test schedule done')


def main_redis():
    print(os.linesep * 3)
    print('=' * 50)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_redis())


def main_scheduler():
    print(os.linesep * 3)
    print('=' * 50)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_scheduler())
    # loop.run_until_complete(test_scheduler_enable_cancel())


def main_demo():
    print(os.linesep * 3)
    print('=' * 50)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_demo())


if __name__ == '__main__':
    main_redis()
    main_scheduler()
    main_demo()
