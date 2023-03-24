#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_scheduler

from __future__ import absolute_import

import asyncio
import contextlib
import typing
import uuid

import fastapi
import pytest
import starlette.testclient

import fastapi_plugins


pytestmark = [pytest.mark.anyio, pytest.mark.scheduler]


def make_app(config=None):
    if config is None:
        class AppSettings(
                fastapi_plugins.RedisSettings,
                fastapi_plugins.SchedulerSettings
        ):
            api_name: str = str(__name__)
        config = AppSettings()

    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI):
        await fastapi_plugins.redis_plugin.init_app(app, config=config)
        await fastapi_plugins.redis_plugin.init()
        await fastapi_plugins.scheduler_plugin.init_app(app, config)
        await fastapi_plugins.scheduler_plugin.init()
        yield
        await fastapi_plugins.scheduler_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()

    app = fastapi_plugins.register_middleware(
        fastapi.FastAPI(lifespan=lifespan)
    )

    @app.post('/jobs/schedule')
    async def job_post(
        cache: fastapi_plugins.TRedisPlugin,
        scheduler: fastapi_plugins.TSchedulerPlugin,
        timeout: int=fastapi.Query(..., title='the job sleep time')
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
        cache: fastapi_plugins.TRedisPlugin,
        job_id: str=fastapi.Query(..., title='the job id')
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

    return app


@pytest.fixture(params=[{}])
def client(request):
    with starlette.testclient.TestClient(make_app(**request.param)) as c:
        yield c


@pytest.fixture
async def schedulerapp():
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = fastapi_plugins.SchedulerSettings()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()
    yield app
    await fastapi_plugins.scheduler_plugin.terminate()


async def test_basic(schedulerapp):
    count = 3
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
    assert res == dict([(str(i), str(i)) for i in range(count)])


async def test_health(schedulerapp):
    count = 3
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
    assert res == dict([(str(i), str(i)) for i in range(count)])
    assert await fastapi_plugins.scheduler_plugin.health() == dict(
        jobs=0,
        active=0,
        pending=0,
        limit=100,
        closed=False
    )


async def test_endpoints(client):
    endpoint = '/demo'
    response = client.get(endpoint)
    assert 200 == response.status_code
    #
    job_timeout = 1
    print()
    print('> submit a job with timeout=%s' % job_timeout)
    endpoint = '/jobs/schedule?timeout=%s' % job_timeout
    response = client.post(endpoint)
    assert 200 == response.status_code
    job_id = response.json()
    assert len(job_id) > 0
    #
    print('> check the job %s' % job_id)
    endpoint = '/jobs/status?job_id=%s' % job_id
    response = client.get(endpoint)
    assert 200 == response.status_code
    assert response.json() == {'job_id': job_id, 'status': 'processing'}
    #
    tries = 10000
    attempt = 0
    endpoint = '/jobs/status?job_id=%s' % job_id
    while attempt < tries:
        response = client.get(endpoint)
        assert 200 == response.status_code
        if response.json() == {'job_id': job_id, 'status': 'success'}:
            break
        attempt += 1
    else:
        pytest.fail(f'job {job_id} with timeout {job_timeout} not finished')
