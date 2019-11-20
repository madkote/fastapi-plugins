
<p align="center">
    <em>Plugins for FastAPI framework, high performance, easy to learn, fast to code, ready for production</em>
</p>
<p align="center">
<a href="https://travis-ci.org/madkote/fastapi_plugins" target="_blank">
    <img src="https://travis-ci.org/madkote/fastapi_plugins.svg?branch=master" alt="Build Status">
</a>
<a href="https://codecov.io/gh/madkote/fastapi_plugins" target="_blank">
    <img src="https://codecov.io/gh/madkote/fastapi_plugins/branch/master/graph/badge.svg" alt="Coverage">
</a>
<a href="https://pypi.org/project/fastapi_plugins" target="_blank">
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

# Changes
See [release notes](CHANGES.md)

# Plugins
## Redis
Supports
* single instance
* cluster **NOT SUPPORTED NOW**
* fake redis **NOT SUPPORTED NOW**
### Example
```
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
## ... more already in progress ...

# Development
Issues and suggestions are welcome through *issues*

# License
This project is licensed under the terms of the MIT license.
