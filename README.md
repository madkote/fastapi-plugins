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

* Cache
  * [Memcached](#memcached)
  * [Redis](#redis)
* [Scheduler](#scheduler)
* Celery
* MQ
* Logging
* Health
* Common

## Changes
See [release notes](CHANGES.md)

## Installation
* by default contains only [Redis](#redis) and [Scheduler](#scheduler)
* `memcached` adds [Memcached](#memcached)
* `all` add everything above

```sh
pip install fastapi-plugins
pip install fastapi-plugins[memcached]
pip install fastapi-plugins[all]
```

## Plugins
### Cache
#### Memcached
Valid variable are
* `MEMCACHED_HOST` - Memcached server host.
* `MEMCACHED_PORT` - Memcached server port. Default is `11211`.
* `MEMCACHED_POOL_MINSIZE` - Minimum number of free connection to create in pool. Default is `1`.
* `MEMCACHED_POOL_SIZE` -  Maximum number of connection to keep in pool. Default is `10`. Must be greater than `0`. `None` is disallowed.
* `MEMCACHED_PRESTART_TRIES` - The number tries to connect to the a Memcached instance.
* `MEMCACHED_PRESTART_WAIT` - The interval in seconds to wait between connection failures on application start.

##### Example
```python
    # run with `uvicorn demo_app:app`
    import typing
    import fastapi
    import pydantic
    
    from fastapi_plugins.memcached import MemcachedSettings
    from fastapi_plugins.memcached import MemcachedClient
    from fastapi_plugins.memcached import memcached_plugin
    from fastapi_plugins.memcached import depends_memcached
    
    class AppSettings(OtherSettings, MemcachedSettings):
        api_name: str = str(__name__)
    
    app = fastapi.FastAPI()
    config = AppSettings()
    
    @app.get("/")
    async def root_get(
            cache: MemcachedClient=fastapi.Depends(depends_memcached),
    ) -> typing.Dict:
        await cache.set(b'Hello', b'World')
        await cache.get(b'Hello')
        return dict(ping=await cache.ping())
    
    @app.on_event('startup')
    async def on_startup() -> None:
        await memcached_plugin.init_app(app, config=config)
        await memcached_plugin.init()
    
    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        await memcached_plugin.terminate()
```

#### Redis
Supports
* single instance
* sentinel

Valid variable are
* `REDIS_TYPE`
  * `redis` - single Redis instance
  * `sentinel` - Redis cluster
* `REDIS_URL` - URL to connect to Redis server. Example
  `redis://user:password@localhost:6379/2`. Supports protocols `redis://`,
  `rediss://` (redis over TLS) and `unix://`.
* `REDIS_HOST` - Redis server host.
* `REDIS_PORT` - Redis server port. Default is `6379`.
* `REDIS_PASSWORD` - Redis password for server.
* `REDIS_DB` - Redis db (zero-based number index). Default is `0`.
* `REDIS_CONNECTION_TIMEOUT` - Redis connection timeout. Default is `2`.
* `REDIS_POOL_MINSIZE` - Minimum number of free connection to create in pool. Default is `1`.
* `REDIS_POOL_MAXSIZE` -  Maximum number of connection to keep in pool. Default is `10`. Must be greater than `0`. `None` is disallowed.
* `REDIS_SENTINELS` - List or a tuple of Redis sentinel addresses.
* `REDIS_SENTINEL_MASTER` - The name of the master server in a sentinel configuration. Default is `mymaster`.
* `REDIS_PRESTART_TRIES` - The number tries to connect to the a Redis instance.
* `REDIS_PRESTART_WAIT` - The interval in seconds to wait between connection failures on application start.

##### Example
```python
    # run with `uvicorn demo_app:app`
    import typing
    import aioredis
    import fastapi
    import pydantic
    import fastapi_plugins
    
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
```

##### Example with Docker Compose - Redis
```YAML
version: '3.7'
services:
  redis:
    image: redis
    ports:
      - "6379:6379"
  demo_fastapi_plugin:
    image:    demo_fastapi_plugin
    environment:
      - REDIS_TYPE=redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    ports:
      - "8000:8000"
```

##### Example with Docker Compose - Redis Sentinel
```YAML
version: '3.7'
services:
  ...
  redis-sentinel:
    ports:
      - "26379:26379"
    environment:
      - ...
    links:
      - redis-master
      - redis-slave
  demo_fastapi_plugin:
    image:    demo_fastapi_plugin
    environment:
      - REDIS_TYPE=sentinel
      - REDIS_SENTINELS=redis-sentinel:26379
    ports:
      - "8000:8000"
```

### Scheduler
Simple schedule an _awaitable_ job as a task. 
* _long_ running `async` functions (e.g. monitor a file a system or events)
* gracefully cancel spawned tasks

Valid variable are:
* `AIOJOBS_CLOSE_TIMEOUT` - The timeout in seconds before canceling a task.
* `AIOJOBS_LIMIT` - The number of concurrent tasks to be executed.
* `AIOJOBS_PENDING_LIMIT` - The number of pending jobs (waiting fr execution).


```python
# run with `uvicorn demo_app:app`
import ...
import fastapi_plugins

class AppSettings(OtherSettings, fastapi_plugins.RedisSettings, fastapi_plugins.SchedulerSettings):
    api_name: str = str(__name__)

app = fastapi.FastAPI()
config = AppSettings()

@app.post("/jobs/schedule/<timeout>")
async def job_post(
    timeout: int=fastapi.Query(..., title='the job sleep time'),
    cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
    scheduler: aiojobs.Scheduler=fastapi.Depends(fastapi_plugins.depends_scheduler),  # @IgnorePep8
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

@app.on_event('startup')
async def on_startup() -> None:
    await fastapi_plugins.redis_plugin.init_app(app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.scheduler_plugin.init_app(app=app, config=config)
    await fastapi_plugins.scheduler_plugin.init()

@app.on_event('shutdown')
async def on_shutdown() -> None:
    await fastapi_plugins.scheduler_plugin.terminate()
    await fastapi_plugins.redis_plugin.terminate()
```

### ... more already in progress ...

# Development
Issues and suggestions are welcome through *issues*

# License
This project is licensed under the terms of the MIT license.
