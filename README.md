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

# important
Aioredis is about to merge into [redis-py](https://github.com/redis/redis-py).
So waiting for release and first benchmarks. Version `1.3.1` remains the fastest.

# fastapi-plugins
FastAPI framework plugins - simple way to share `fastapi` code and utilities across applications.

The concept is `plugin` - plug a functional utility into your application without or with minimal effort.

* [Cache](./docs/cache.md)
  * [Memcached](./docs/cache.md#memcached)
  * [Redis](./docs/cache.md#redis)
* [Scheduler](./docs/scheduler.md)
* [Control](./docs/control.md)
  * [Version](./docs/control.md#version)
  * [Environment](./docs/control.md#environment)
  * [Health](./docs/control.md#health)
  * [Heartbeat](./docs/control.md#heartbeat)
* [Application settings/configuration](./docs/settings.md)
* [Logging](./docs/logger.md)
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
  * [Logging](./docs/logger.md)
* `memcached` adds [Memcached](#memcached)
* `all` add everything above

```sh
pip install fastapi-plugins
pip install fastapi-plugins[memcached]
pip install fastapi-plugins[all]
```

## Quick start
### Plugin
Add information about plugin system.
### Application settings
Add information about settings.
### Application configuration
Add information about configuration of an application
### Complete example
```python
import fastapi
import fastapi_plugins

from fastapi_plugins.memcached import MemcachedSettings
from fastapi_plugins.memcached import memcached_plugin, TMemcachedPlugin

import asyncio
import aiojobs
import aioredis
import contextlib
import logging

@fastapi_plugins.registered_configuration
class AppSettings(
        fastapi_plugins.ControlSettings,
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings,
        fastapi_plugins.LoggingSettings,
        MemcachedSettings,
):
    api_name: str = str(__name__)
    logging_level: int = logging.DEBUG
    logging_style: fastapi_plugins.LoggingStyle = fastapi_plugins.LoggingStyle.logjson


@fastapi_plugins.registered_configuration(name='sentinel')
class AppSettingsSentinel(AppSettings):
    redis_type = fastapi_plugins.RedisType.sentinel
    redis_sentinels = 'localhost:26379'


@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    config = fastapi_plugins.get_config()
    await fastapi_plugins.config_plugin.init_app(app, config)
    await fastapi_plugins.config_plugin.init()
    await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    await fastapi_plugins.log_plugin.init()
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
    yield
    await fastapi_plugins.control_plugin.terminate()
    await fastapi_plugins.scheduler_plugin.terminate()
    await fastapi_plugins.redis_plugin.terminate()
    await memcached_plugin.terminate()
    await fastapi_plugins.log_plugin.terminate()
    await fastapi_plugins.config_plugin.terminate()


app = fastapi_plugins.register_middleware(fastapi.FastAPI(lifespan=lifespan))


@app.get("/")
async def root_get(
        cache: fastapi_plugins.TRedisPlugin,
        conf: fastapi_plugins.TConfigPlugin,
        logger: fastapi_plugins.TLoggerPlugin
) -> typing.Dict:
    ping = await cache.ping()
    logger.debug('root_get', extra=dict(ping=ping, api_name=conf.api_name))
    return dict(ping=ping, api_name=conf.api_name)


@app.post("/jobs/schedule/<timeout>")
async def job_post(
    timeout: int=fastapi.Query(..., title='the job sleep time'),
    cache: fastapi_plugins.TRedisPlugin,
    scheduler: fastapi_plugins.TSchedulerPlugin,
    logger: fastapi_plugins.TLoggerPlugin
) -> str:
    async def coro(job_id, timeout, cache):
        await cache.set(job_id, 'processing')
        try:
            await asyncio.sleep(timeout)
            if timeout == 8:
                logger.critical('Ugly erred job %s' % job_id)
                raise Exception('ugly error')
        except asyncio.CancelledError:
            await cache.set(job_id, 'canceled')
            logger.warning('Cancel job %s' % job_id)
        except Exception:
            await cache.set(job_id, 'erred')
            logger.error('Erred job %s' % job_id)
        else:
            await cache.set(job_id, 'success')
            logger.info('Done job %s' % job_id)

    job_id = str(uuid.uuid4()).replace('-', '')
    logger = await fastapi_plugins.log_adapter(logger, extra=dict(job_id=job_id, timeout=timeout))    # noqa E501
    logger.info('New job %s' % job_id)
    await cache.set(job_id, 'pending')
    logger.debug('Pending job %s' % job_id)
    await scheduler.spawn(coro(job_id, timeout, cache))
    return job_id


@app.get("/jobs/status/<job_id>")
async def job_get(
    job_id: str=fastapi.Query(..., title='the job id'),
    cache: fastapi_plugins.TRedisPlugin,
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
    cache: fastapi_plugins.TMemcachedPlugin,
) -> typing.Dict:
    await cache.set(key.encode(), str(key + '_value').encode())
    value = await cache.get(key.encode())
    return dict(ping=(await cache.ping()).decode(), key=key, value=value)
```

# Development
Issues and suggestions are welcome through [issues](https://github.com/madkote/fastapi-plugins/issues)

# License
This project is licensed under the terms of the MIT license.
