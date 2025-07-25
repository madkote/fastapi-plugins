#!/usr/bin/env python
# -*- coding: utf-8 -*-
# demo

from __future__ import absolute_import

import asyncio
import logging
import os
import time

import fastapi
import pydantic_settings

import fastapi_plugins


class OtherSettings(pydantic_settings.BaseSettings):
    other: str = 'other'


class AppSettings(
        OtherSettings,
        fastapi_plugins.LoggingSettings,
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings
):
    api_name: str = str(__name__)
    logging_level: int = logging.INFO


async def test_redis():
    print('--- do redis test')
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
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
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
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
            await s.spawn(coro(str(i), i / 10))
            # await s.spawn(coro(str(i), i/10 + random.choice([0.1, 0.2, 0.3, 0.4, 0.5])))  # nosec B311 # noqa
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
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings(logging_style=fastapi_plugins.LoggingStyle.logfmt)

    await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    await fastapi_plugins.log_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_sleep = 0.25

        print('- play')
        logger = await fastapi_plugins.log_plugin()
        c = await fastapi_plugins.redis_plugin()
        s = await fastapi_plugins.scheduler_plugin()
        for i in range(num_jobs):
            await s.spawn(coro(c, str(i), i / 10))
        logger.info('- sleep %s' % num_sleep)
        # print('- sleep', num_sleep)
        await asyncio.sleep(num_sleep)
        logger.info('- check')
        # print('- check')
        for i in range(num_jobs):
            logger.info('%s == %s' % (i, await c.get(str(i))))
            # print(i, '==', await c.get(str(i)))
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
        print('---demo done')


async def test_demo_custom_log():
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

    class CustomLoggingSettings(fastapi_plugins.LoggingSettings):
        another_format: str = '%(asctime)s %(levelname)-8s %(name)-15s %(message)s'

    class CustomLoggingPlugin(fastapi_plugins.LoggingPlugin):
        def _create_logger(
            self,
            name: str,
            config: pydantic_settings.BaseSettings = None
        ) -> logging.Logger:
            import sys
            handler = logging.StreamHandler(stream=sys.stderr)
            formatter = logging.Formatter(config.another_format)
            logger = logging.getLogger(name)
            #
            logger.setLevel(config.logging_level)
            handler.setLevel(config.logging_level)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger

    class AppSettings(
            OtherSettings,
            fastapi_plugins.RedisSettings,
            fastapi_plugins.SchedulerSettings,
            CustomLoggingSettings
    ):
        api_name: str = str(__name__)
        logging_level: int = logging.INFO

    print('--- do demo')
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings(logging_style=fastapi_plugins.LoggingStyle.logfmt)
    mylog_plugin = CustomLoggingPlugin()

    await mylog_plugin.init_app(app, config, name=__name__)
    await mylog_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_sleep = 0.25

        print('- play')
        logger = await mylog_plugin()
        c = await fastapi_plugins.redis_plugin()
        s = await fastapi_plugins.scheduler_plugin()
        for i in range(num_jobs):
            await s.spawn(coro(c, str(i), i / 10))
        logger.info('- sleep %s' % num_sleep)
        # print('- sleep', num_sleep)
        await asyncio.sleep(num_sleep)
        logger.info('- check')
        # print('- check')
        for i in range(num_jobs):
            logger.info('%s == %s' % (i, await c.get(str(i))))
            # print(i, '==', await c.get(str(i)))
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await mylog_plugin.terminate()
        print('---demo done')


async def test_demo_orjson_log():
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
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings(logging_style=fastapi_plugins.LoggingStyle.logorjson)

    await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    await fastapi_plugins.log_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_sleep = 0.25

        print('- play')
        logger = await fastapi_plugins.log_plugin()
        c = await fastapi_plugins.redis_plugin()
        s = await fastapi_plugins.scheduler_plugin()
        for i in range(num_jobs):
            await s.spawn(coro(c, str(i), i / 10))
        logger.info('- sleep %s' % num_sleep, extra=dict(bla='bla'))
        # print('- sleep', num_sleep)
        await asyncio.sleep(num_sleep)
        logger.info('- check')
        # print('- check')
        for i in range(num_jobs):
            logger.info('%s == %s' % (i, await c.get(str(i))))
            # print(i, '==', await c.get(str(i)))
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
        print('---demo done')


async def test_demo_json_log():
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
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings(logging_style=fastapi_plugins.LoggingStyle.logjson)

    await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    await fastapi_plugins.log_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_sleep = 0.25

        print('- play')
        logger = await fastapi_plugins.log_plugin()
        c = await fastapi_plugins.redis_plugin()
        s = await fastapi_plugins.scheduler_plugin()
        for i in range(num_jobs):
            await s.spawn(coro(c, str(i), i / 10))
        logger.info('- sleep %s' % num_sleep, extra=dict(bla='bla'))
        # print('- sleep', num_sleep)
        await asyncio.sleep(num_sleep)
        logger.info('- check')
        # print('- check')
        for i in range(num_jobs):
            logger.info('%s == %s' % (i, await c.get(str(i))))
            # print(i, '==', await c.get(str(i)))
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
        print('---demo done')


async def test_memcached():
    print('---test memcached')
    from fastapi_plugins.memcached import MemcachedSettings
    from fastapi_plugins.memcached import memcached_plugin

    class MoreSettings(AppSettings, MemcachedSettings):
        memcached_prestart_tries: int = 5
        memcached_prestart_wait: int = 1

    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = MoreSettings()
    await memcached_plugin.init_app(app=app, config=config)
    await memcached_plugin.init()

    c = await memcached_plugin()
    print(await c.get(b'x'))
    print(await c.set(b'x', str(time.time()).encode()))
    print(await c.get(b'x'))
    await memcached_plugin.terminate()
    print('---test memcached done')


async def test_demo_buffered_log():
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
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings(
        logging_style=fastapi_plugins.LoggingStyle.logjson,
        logging_memory_capacity=25
    )

    await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    await fastapi_plugins.log_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app=app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

    try:
        num_jobs = 10
        num_tasks = 30

        logger = await fastapi_plugins.log_plugin()
        for c_job in range(num_jobs):
            print(f'----- JOB {c_job}')
            for c_task in range(num_tasks):
                logger.info(f'job={c_job} task={c_task} hello world')
                await asyncio.sleep(0.1)
            await asyncio.sleep(0.5)
    finally:
        print('- terminate')
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
        print('---demo done')


# =============================================================================
# ---
# =============================================================================
def main_memcached():
    print(os.linesep * 3)
    print('=' * 50)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_memcached())


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


def main_demo_custom_log():
    print(os.linesep * 3)
    print('=' * 50)
    print('= DEMO CUSTOM LOG')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_demo_custom_log())


def main_demo_json_log():
    print(os.linesep * 3)
    print('=' * 50)
    print('= DEMO JSON LOG')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_demo_json_log())


def main_demo_orjson_log():
    print(os.linesep * 3)
    print('=' * 50)
    print('= DEMO ORJSON LOG')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_demo_orjson_log())


def main_demo_buffered_log():
    print(os.linesep * 3)
    print('=' * 50)
    print('= DEMO BUFFERED LOG')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_demo_buffered_log())


if __name__ == '__main__':
    main_redis()
    main_scheduler()
    main_demo()
    main_demo_custom_log()
    main_demo_json_log()
    main_demo_orjson_log()
    main_demo_buffered_log()

    try:
        main_memcached()
    except Exception as e:
        print(type(e), e)
