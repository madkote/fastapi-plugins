# Settings
The easy way to configure the `FastAPI` application:
* define (various) configuration(s)
* register configuration
* use configuration depending on the environment
* use configuration in router handler if required

## Define configuration
It is a good practice to defined various configuration for your application.
```python
	import fastapi_plugins
	
	class DefaultSettings(fastapi_plugins.RedisSettings):
		api_name: str = str(__name__)
	
	class DockerSettings(DefaultSettings):
	    redis_type = fastapi_plugins.RedisType.sentinel
	    redis_sentinels = 'localhost:26379'
	
	class LocalSettings(DefaultSettings):
	    pass
	
	class TestSettings(DefaultSettings):
	    testing: bool = True

	class MyConfigSettings(DefaultSettings):
	    custom: bool = True

	...
```

## Register configuration
Registration with a decorator
```python
	import fastapi_plugins
	
	class DefaultSettings(fastapi_plugins.RedisSettings):
		api_name: str = str(__name__)
	
	# @fastapi_plugins.registered_configuration_docker
	@fastapi_plugins.registered_configuration
	class DockerSettings(DefaultSettings):
	    redis_type = fastapi_plugins.RedisType.sentinel
	    redis_sentinels = 'localhost:26379'
	
	@fastapi_plugins.registered_configuration_local
	class LocalSettings(DefaultSettings):
	    pass
	
	@fastapi_plugins.registered_configuration_test
	class TestSettings(DefaultSettings):
	    testing: bool = True
	
	@fastapi_plugins.registered_configuration(name='my_config')
	class MyConfigSettings(DefaultSettings):
	    custom: bool = True
	...
```

or by a function call
```python
	import fastapi_plugins
	
	class DefaultSettings(fastapi_plugins.RedisSettings):
		api_name: str = str(__name__)
	
	class DockerSettings(DefaultSettings):
	    redis_type = fastapi_plugins.RedisType.sentinel
	    redis_sentinels = 'localhost:26379'
	
	class LocalSettings(DefaultSettings):
	    pass
	
	class TestSettings(DefaultSettings):
	    testing: bool = True
	
	class MyConfigSettings(DefaultSettings):
	    custom: bool = True
	
	fastapi_plugins.register_config(DockerSettings)
	# fastapi_plugins.register_config_docker(DockerSettings)
	fastapi_plugins.register_config_local(LocalSettings)
	fastapi_plugins.register_config_test(TestSettings)
	fastapi_plugins.register_config(MyConfigSettings, 'my_config')
	...
```


## Application configuration
Next, create application and it's configuration, and register the plugin if needed. The last is optinally,
and is only relevant for use cases, where the configuration values are required for endpoint handlers (see `api_name` below).
```python
import fastapi
import fastapi_plugins
...

@contextlib.asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    config = fastapi_plugins.get_config()
    await fastapi_plugins.config_plugin.init_app(app, config)
    await fastapi_plugins.config_plugin.init()
    await fastapi_plugins.redis_plugin.init_app(app, config=config)
    await fastapi_plugins.redis_plugin.init()
    await fastapi_plugins.control_plugin.init_app(app, config=config, version=__version__, environ=config.dict())
    await fastapi_plugins.control_plugin.init()
    yield
    await fastapi_plugins.control_plugin.terminate()
    await fastapi_plugins.redis_plugin.terminate()
    await fastapi_plugins.config_plugin.terminate()

app = fastapi_plugins.register_middleware(fastapi.FastAPI(lifespan=lifespan))

@app.get("/")
async def root_get(
        cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
        conf: pydantic.BaseSettings=fastapi.Depends(fastapi_plugins.depends_config) # noqa E501
) -> typing.Dict:
    return dict(ping=await cache.ping(), api_name=conf.api_name)
```

## Use configuration
Now, the application will use by default a configuration for `docker` or by user's command any other configuration.
```bash
	uvicorn scripts.demo_app:app
	curl -X 'GET' 'http://localhost:8000/control/environ' -H 'accept: application/json'	
	{
	  "environ": {
	    "config_name":"docker",
	    "redis_type":"sentinel",
	    ...
	  }
	}
	
	...
	CONFIG_NAME=local uvicorn scripts.demo_app:app
	curl -X 'GET' 'http://localhost:8000/control/environ' -H 'accept: application/json'	
	{
	  "environ": {
	    "config_name":"local",
	    "redis_type":"redis",
	    ...
	  }
	}
```

It is also usefull with `docker-compose`:
```yaml
services:
  demo_fastapi_plugin:
    image: demo_fastapi_plugin
    environment:
      - CONFIG_NAME=docker
  
  ...
  
  demo_fastapi_plugin:
    image: demo_fastapi_plugin
    environment:
      - CONFIG_NAME=docker_sentinel
```
