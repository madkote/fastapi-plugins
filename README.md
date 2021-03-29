<p align="center">
    <em>Plugins for FastAPI framework, high performance, easy to learn, fast to code, ready for production</em>
</p>
<p align="center">
<a href="https://travis-ci.org/madkote/fastapi-plugins" target="_blank">
    <img src="https://travis-ci.org/madkote/fastapi_plugins.svg?branch=master" alt="Build Status">
</a>
<a href="https://codecov.io/gh/madkote/fastapi-plugins" target="_blank">
    <img src="https://codecov.io/gh/madkote/fastapi_plugins/branch/master/graph/badge.svg" alt="Coverage">
</a>
<a href="https://pypi.org/project/fastapi-plugins" target="_blank">
    <img src="https://img.shields.io/pypi/v/fastapi_plugins.svg" alt="Package version">
</a>
<a href="https://gitter.im/tiangolo/fastapi?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge" target="_blank">
    <img src="https://badges.gitter.im/tiangolo/fastapi.svg" alt="Join the chat at https://gitter.im/tiangolo/fastapi">
</a>
</p>

# fastapi-plugins
FastAPI framework plugins

* [Cache](./docs/cache.md)
  * [Memcached](./docs/cache.md#memcached)
  * [Redis](./docs/cache.md#redis)
* [Scheduler](./docs/scheduler.md)
* [Control](./docs/control.md)
  * [Version](./docs/control.md#version)
  * [Environment](./docs/control.md#environment)
  * [Health](./docs/control.md#health)
  * [Heartbeat](./docs/control.md#heartbeat)
* Celery
* MQ
* and much more is already in progress...

## Changes
See [release notes](CHANGES.md)

## Installation
* by default contains
  * [Redis](./docs/cache.md#redis)
  * [Scheduler](./docs/scheduler.md)
  * [Control](./docs/control.md)
* `memcached` adds [Memcached](#memcached)
* `all` add everything above

```sh
pip install fastapi-plugins
pip install fastapi-plugins[memcached]
pip install fastapi-plugins[all]
```

## Quick start
```python
import fastapi
import fastapi_plugins

from fastapi_plugins.memcached import MemcachedSettings
from fastapi_plugins.memcached import MemcachedClient
from fastapi_plugins.memcached import depends_memcached
from fastapi_plugins.memcached import memcached_plugin

import asyncio
import aiojobs
import aioredis

class AppSettings(
        fastapi_plugins.ControlSettings,
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings,
        MemcachedSettings,
):
    api_name: str = str(__name__)

app = fastapi.FastAPI()
config = AppSettings()

@app.get("/")
async def root_get(
        cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
) -> typing.Dict:
    return dict(ping=await cache.ping())


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
```

# Development
Issues and suggestions are welcome through [issues](https://github.com/madkote/fastapi-plugins/issues)

# License
This project is licensed under the terms of the MIT license.
