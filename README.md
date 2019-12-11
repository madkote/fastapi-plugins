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

* [Redis](#redis)
* Celery
* MQ
* Logging
* Health
* Common

## Changes
See [release notes](CHANGES.md)

## Installation
```sh
	pip install fastapi-plugins
```

## Plugins
### Redis
Supports
* single instance
* sentinel
* fake redis **NOT SUPPORTED NOW**

Valid variable are
* `REDIS_TYPE`
  * `redis` - single Redis isntance
  * `sentinel` - Redis cluster
  * `fake` - by using fake Redis
* `REDIS_URL` - URL to connect to Redis server. Example
  `redis://user:password@localhost:6379/2`. Supports protocols `redis://`,
  `rediss://` (redis over TLS) and `unix://`.
* `REDIS_HOST` - Redis server host.
* `REDIS_PORT` - Redis server port. Default is `6379`.
* `REDIS_PASSWORD` - Redis password for server.
* `REDIS_DB` - Redis db (zero-based number index). Default is `0`.
* `REDIS_CONNECTION_TIMEOUT` - Redis connection timeout. Default is `2`.
* `REDIS_POOL_MINSIZE` - Minimum number of free connection to create in pool. Default is `0`.
* `REDIS_POOL_MAXSIZE` -  Maximum number of connection to keep in pool. Default is `10`. Must be greater than `0`. `None` is disallowed.
* `REDIS_SENTINELS` - List or a tuple of Redis sentinel addresses.
* `REDIS_SENTINEL_MASTER` - The name of the master server in a sentinel configuration. Default is `mymaster`.

#### Example
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

#### Example with Docker Compose - Redis
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

#### Example with Docker Compose - Redis Sentinel
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


### ... more already in progress ...

# Development
Issues and suggestions are welcome through *issues*

# License
This project is licensed under the terms of the MIT license.
