# Logging
## Supported formats
* Default
* JSON
* Logfmt

Shipped plugin will dump all logs to `sys.stdout`. In order to change/add more handlers or
formats, override the plugin and implement missing functionality (you also can provide PR).
For details see below.

## Valid variables and values
* `LOGGING_LEVEL` - verbosity level
  * any valid level provided by standard `logging` library (e.g. `10`, `20`, `30`, ...) 
* `LOGGING_STYLE` - style/format of log records
  * `txt` - default `logging` format
  * `json` - JSON format
  * `logfmt` - `Logfmt` format (key, value)
* `LOGGING_HANDLER` - Handler type for log entries.
  * `stdout` - Output log entries to `sys.stdout`.
  * `list` - Collect log entries in a queue, **for testing purposes only**.
* `LOGGING_FMT` - logging format for default formatter, e.g. `"%(asctime)s %(levelname) %(message)s"`.
  **Note**: this parameter is only valid in conjuction with `LOGGING_STYLE=txt`.

## Example
### Application
```python
    # run with `uvicorn demo_app:app`
    import logging
    import typing
    import aioredis
    import fastapi
    import pydantic
    import fastapi_plugins
    
    class AppSettings(OtherSettings, fastapi_plugins.LoggingSettings, fastapi_plugins.RedisSettings):
        api_name: str = str(__name__)
        logging_level: int = logging.DEBUG
        logging_style: fastapi_plugins.LoggingStyle = fastapi_plugins.LoggingStyle.logjson
    
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings()
    
    @app.get("/")
    async def root_get(
            cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
            logger: logging.Logger=fastapi.Depends(fastapi_plugins.depends_logging),
    ) -> typing.Dict:
        ping = await cache.ping()
        logger.debug('root_get', extra=dict(ping=ping))
        return dict(ping=ping)
    
    @app.on_event('startup')
    async def on_startup() -> None:
        await fastapi_plugins.log_plugin.init_app(app, config=config, name=__name__)
        await fastapi_plugins.log_plugin.init()
        await fastapi_plugins.redis_plugin.init_app(app, config=config)
        await fastapi_plugins.redis_plugin.init()
    
    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
```

### Application with Logging Adapter
```python
	... as above ...

	@app.post("/jobs/schedule/<timeout>")
	async def job_post(
	    cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
	    logger: logging.Logger=fastapi.Depends(fastapi_plugins.depends_logging)
	) -> str:
	    async def coro(job_id, cache):
		    logger.info('Done job %s' % job_id)
	
		# create a job ID
	    job_id = str(uuid.uuid4()).replace('-', '')

		# create logging adapter which will contain job ID in every log record
	    logger = await fastapi_plugins.log_adapter(
	        logger,
	        extra=dict(job_id=job_id, other='some static information')
	    )

		# job_id and other will be now part of log record
	    logger.info('New job %s' % job_id)
	    await cache.set(job_id, 'pending')
	    logger.debug('Pending job %s' % job_id)
	    # await scheduler.spawn(coro(job_id, cache))
	    return job_id
```

### Custom formats and handlers
```python
    # run with `uvicorn demo_app:app`
    import logging
    import typing
    import aioredis
    import fastapi
    import pydantic
    import fastapi_plugins
    
    class CustomLoggingSettings(fastapi_plugins.LoggingSettings):
    	some_settings: ... = ...
    
    class CustomLoggingPlugin(fastapi_plugins.LoggingPlugin):
        def _create_logger(
            self, 
            name:str, 
            config:pydantic.BaseSettings=None
        ) -> logging.Logger:
            import sys
            handler = logging.StreamHandler(stream=sys.stderr)
            formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(name)-15s %(message)s')
            logger = logging.getLogger(name)
            #
            logger.setLevel(config.logging_level)
            handler.setLevel(config.logging_level)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger
    
    class AppSettings(OtherSettings, CustomLoggingSettings, fastapi_plugins.RedisSettings):
        api_name: str = str(__name__)
        logging_level: int = logging.DEBUG
    
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = AppSettings()
    fastapi_plugins.log_plugin = CustomLoggingPlugin()
    
    @app.get("/")
    async def root_get(
            cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
            logger: logging.Logger=fastapi.Depends(fastapi_plugins.depends_logging),
    ) -> typing.Dict:
        ping = await cache.ping()
        logger.debug('root_get', extra=dict(ping=ping))
        return dict(ping=ping)
    
    @app.on_event('startup')
    async def on_startup() -> None:
        await fastapi_plugins.log_plugin.init_app(app, config, name=__name__)
    	await fastapi_plugins.log_plugin.init()
        await fastapi_plugins.redis_plugin.init_app(app, config=config)
        await fastapi_plugins.redis_plugin.init()
    
    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.log_plugin.terminate()
```

### Docker Compose
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
      - LOGGING_LEVEL=10    # 0, 10, 20, 30, 40, 50
      - LOGGING_STYLE=json  # txt, json, logfmt
      - ...
    ports:
      - "8000:8000"
```
