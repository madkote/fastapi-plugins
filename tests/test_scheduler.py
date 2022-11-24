#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_scheduler

from __future__ import absolute_import

import asyncio
import typing
import unittest
import uuid

import aiojobs
import redis.asyncio as aioredis
import fastapi
import pytest
import starlette.testclient

import fastapi_plugins

from . import d2json


@pytest.mark.scheduler
class SchedulerTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_app(self, config=None):
        app = fastapi_plugins.register_middleware(fastapi.FastAPI())
        if config is None:
            class AppSettings(
                    fastapi_plugins.RedisSettings,
                    fastapi_plugins.SchedulerSettings
            ):
                api_name: str = str(__name__)
            config = AppSettings()

        @app.post('/jobs/schedule')
        async def job_post(
            timeout: int=fastapi.Query(..., title='the job sleep time'),
            cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),               # noqa E501
            scheduler: aiojobs.Scheduler=fastapi.Depends(fastapi_plugins.depends_scheduler),    # noqa E501
        ) -> str:
            async def coro(job_id, timeout, cache):
                await cache.set(job_id, 'processing')
                try:
                    await asyncio.sleep(timeout)
                    if timeout >= 3:
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

        @app.get('/jobs/status')
        async def job_get(
            job_id: str=fastapi.Query(..., title='the job id'),
            cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),   # noqa E501
        ) -> typing.Dict:
            status = await cache.get(job_id)
            if status is None:
                raise fastapi.HTTPException(
                    status_code=starlette.status.HTTP_404_NOT_FOUND,
                    detail='Job %s not found' % job_id
                )
            return dict(job_id=job_id, status=status)

        @app.get('/demo')
        async def demo_get(
        ) -> typing.Dict:
            return dict(demo=123)

        @app.on_event('startup')
        async def on_startup() -> None:
            await fastapi_plugins.redis_plugin.init_app(app, config=config)
            await fastapi_plugins.redis_plugin.init()
            await fastapi_plugins.scheduler_plugin.init_app(app, config)
            await fastapi_plugins.scheduler_plugin.init()

        @app.on_event('shutdown')
        async def on_shutdown() -> None:
            await fastapi_plugins.scheduler_plugin.terminate()
            await fastapi_plugins.redis_plugin.terminate()

        return app

    def test_basic(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.SchedulerSettings()
            await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config) # noqa E501
            await fastapi_plugins.scheduler_plugin.init()
            try:
                count = 3
                exp = dict([(str(i), str(i)) for i in range(count)])
                res = {}

                async def coro(name, timeout):
                    try:
                        await asyncio.sleep(timeout)
                        res[name] = name
                    except asyncio.CancelledError as e:
                        res[name] = 'cancel'
                        raise e

                s = await fastapi_plugins.scheduler_plugin()
                for i in range(count):
                    await s.spawn(coro(str(i), i / 10))
                await asyncio.sleep(1)
                self.assertTrue(d2json(exp) == d2json(res), 'scheduler failed')
            finally:
                await fastapi_plugins.scheduler_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_health(self):
        async def _test():
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.SchedulerSettings()
            await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config) # noqa E501
            await fastapi_plugins.scheduler_plugin.init()
            try:
                count = 3
                exp = dict([(str(i), str(i)) for i in range(count)])
                res = {}

                async def coro(name, timeout):
                    try:
                        await asyncio.sleep(timeout)
                        res[name] = name
                    except asyncio.CancelledError as e:
                        res[name] = 'cancel'
                        raise e

                s = await fastapi_plugins.scheduler_plugin()
                for i in range(count):
                    await s.spawn(coro(str(i), i / 10))
                await asyncio.sleep(1)
                self.assertTrue(d2json(exp) == d2json(res), 'scheduler failed')
                #
                exp = dict(
                    jobs=0,
                    active=0,
                    pending=0,
                    limit=100,
                    closed=False
                )
                res = await fastapi_plugins.scheduler_plugin.health()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await fastapi_plugins.scheduler_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_endpoints(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(self.make_app())
            with client as c:
                endpoint = '/demo'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                job_timeout = 1
                print()
                print('> submit a job with timeout=%s' % job_timeout)
                endpoint = '/jobs/schedule?timeout=%s' % job_timeout
                response = c.post(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = 'must be uuid'
                res = response.json()
                self.assertTrue(len(res) > 0, '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                job_id = res
                print('> check the job %s' % job_id)
                endpoint = '/jobs/status?job_id=%s' % job_id
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'job_id': job_id, 'status': 'processing'}
                res = response.json()
                self.assertTrue(d2json(res) == d2json(exp), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                tries = 10000
                attempt = 0
                exp = {'job_id': job_id, 'status': 'success'}
                endpoint = '/jobs/status?job_id=%s' % job_id
                while attempt < tries:
                    response = c.get(endpoint)
                    res = response.status_code
                    self.assertTrue(200 == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                    res = response.json()
                    if d2json(res) == d2json(exp):
                        break
                    attempt += 1
                else:
                    self.fail('job %s with timeout %s not finished' % (job_id, job_timeout))    # noqa E501
        finally:
            event_loop.close()


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
