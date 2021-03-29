# Control
Control you application out of the box with:
* `/control/environ` - return the application's environment
* `/control/health` - return the application's and it's plugins health
* `/control/heartbeat` - return the application's heart beat
* `/control/version` - return the application's version

Valid variables are:
* `CONTROL_ROUTER_PREFIX` - The router prefix for `control` plugin. Default is `control`.
* `CONTROL_ROUTER_TAG` - The router tag for `control` plugin. Default is `control`.
* `CONTROL_ENABLE_ENVIRON` - The flag to enable or disable `environ` endpoint. Default is `True` - enabled.
* `CONTROL_ENABLE_HEALTH` - The flag to enable or disable `health` endpoint. Default is `True` - enabled.
* `CONTROL_ENABLE_HEARTBEAT` - The flag to enable or disable `heartbeat` endpoint. Default is `True` - enabled.
* `CONTROL_ENABLE_VERSION` - The flag to enable or disable `version` endpoint. Default is `True` - enabled.

## Environment
The endpoint `/control/environ` returns the environment variables and their
values used in the application. It is the responsibility of developer to hide
or mask some values such as passwords or any other critical information.

## Version
The endpoint `/control/version` returns the version of the application. The
version must be passed explicitly.

## Health
The endpoint `/control/health` returns health status of the application, where
all observed plugins should return some details on health check or raise an
exception.

```python
	class MyPluginWithHealth(
	        fastapi_plugins.Plugin,
	        fastapi_plugins.ControlHealthMixin
	):
	    async def init_app(
	            self,
	            app: fastapi.FastAPI,
	            config: pydantic.BaseSettings=None,     # @UnusedVariable
	            *args,                                  # @UnusedVariable
	            **kwargs                                # @UnusedVariable
	    ) -> None:
	        self.counter = 0
	        app.state.MY_PLUGIN_WITH_HELP = self
	
	    async def health(self) -> typing.Dict:
	        if self.counter > 3:
	            raise Exception('Health check failed')
	        else:
	            self.counter += 1
	            return dict(myinfo='OK', mytype='counter health')
	
	myplugin = MyPluginWithHealth()
	app = fastapi.FastAPI()
	config = AppSettings()
	
	@app.get("/")
	async def root_get(
	        myextension: MyPluginWithHealth=fastapi.Depends(depends_myplugin),
	) -> typing.Dict:
	    return dict(ping='pong')
	
	@app.on_event('startup')
	async def on_startup() -> None:
	    await fastapi_plugins.myplugin.init_app(app, config=config)
	    await fastapi_plugins.myplugin.init()
	    await fastapi_plugins.control_plugin.init_app(
	        app,
	        config=config,
	        version='1.2.3',
	        environ=config.dict(),
	    )
	    await fastapi_plugins.control_plugin.init()
	
	@app.on_event('shutdown')
	async def on_shutdown() -> None:
	    await fastapi_plugins.control_plugin.terminate()
	    await fastapi_plugins.myplugin.terminate()
```

## Heartbeat
The endpoint `/control/heartbeat` returns heart beat of the application - simple health without any plugins.

## Example
```python
    # run with `uvicorn demo_app:app`
    import aioredis
    import fastapi
    import fastapi_plugins
    
    class AppSettings(
        fastapi_plugins.ControlSettings,
        fastapi_plugins.RedisSettings
    ):
        api_name: str = str(__name__)
        #
        # control_enable_environ: bool = True
        # control_enable_health: bool = True
        # control_enable_heartbeat: bool = True
        # control_enable_version: bool = True
    
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
        await fastapi_plugins.control_plugin.init_app(
            app,
            config=config,
            version='1.2.3',
            environ=config.dict(),
        )
        await fastapi_plugins.control_plugin.init()
    
    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        await fastapi_plugins.control_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
```

Control plugin should be initialized as last in order to find all observable
plugins - to report their health.
Parameters `version` and `environ` will return these values on endpoint calls.

#### Environ
```bash
	curl -X 'GET' 'http://localhost:8000/control/environ' -H 'accept: application/json'
	
	{
	  "environ": {
	    "memcached_host":"localhost",
	    "memcached_port":11211,
	    "memcached_pool_size":10,
	    "memcached_pool_minsize":1,
	    "memcached_prestart_tries":300,
	    "memcached_prestart_wait":1,
	    "aiojobs_close_timeout":0.1,
	    "aiojobs_limit":100,
	    "aiojobs_pending_limit":10000,
	    "redis_type":"redis",
	    "redis_url":null,
	    "redis_host":"localhost",
	    ...
	  }
	}
```

#### Version
```bash
	curl -X 'GET' 'http://localhost:8000/control/version' -H 'accept: application/json'
	
	{
	  "version": "0.1.2"
	}
```

#### Health
```bash
	curl -X 'GET' 'http://localhost:8000/control/health' -H 'accept: application/json'
	
	{
	  "status": true,
	  "checks": [
	    {
	      "status": true,
	      "name": "MEMCACHED",
	      "details": {
	        "host": "localhost",
	        "port": 11211,
	        "version": "1.6.9"
	      }
	    },
	    {
	      "status": true,
	      "name": "REDIS",
	      "details": {
	        "redis_type": "redis",
	        "redis_address": "redis://localhost:6379/0",
	        "redis_pong": "PONG"
	      }
	    },
	    {
	      "status": true,
	      "name": "AIOJOBS_SCHEDULER",
	      "details": {
	        "jobs": 0,
	        "active": 0,
	        "pending": 0,
	        "limit": 100,
	        "closed": false
	      }
	    }
	  ]
	}
```

#### Heartbeat
```bash
	curl -X 'GET' 'http://localhost:8000/control/heartbeat' -H 'accept: application/json'
	
	{
	  "is_alive": true
	}
```
