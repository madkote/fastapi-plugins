# Cache
## Memcached
Valid variable are
* `MEMCACHED_HOST` - Memcached server host.
* `MEMCACHED_PORT` - Memcached server port. Default is `11211`.
* `MEMCACHED_POOL_MINSIZE` - Minimum number of free connection to create in pool. Default is `1`.
* `MEMCACHED_POOL_SIZE` -  Maximum number of connection to keep in pool. Default is `10`. Must be greater than `0`. `None` is disallowed.
* `MEMCACHED_PRESTART_TRIES` - The number tries to connect to the a Memcached instance.
* `MEMCACHED_PRESTART_WAIT` - The interval in seconds to wait between connection failures on application start.

### Example
```python
    # run with `uvicorn demo_app:app`
    import contextlib
    import typing
    import fastapi
    import pydantic
    
    from fastapi_plugins.memcached import MemcachedSettings
    from fastapi_plugins.memcached import MemcachedClient
    from fastapi_plugins.memcached import memcached_plugin
    from fastapi_plugins.memcached import depends_memcached
    
    class AppSettings(OtherSettings, MemcachedSettings):
        api_name: str = str(__name__)
    
    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI):
        config = AppSettings()
        await memcached_plugin.init_app(app, config=config)
        await memcached_plugin.init()
        yield
        await memcached_plugin.terminate()
    
    app = fastapi_plugins.register_middleware(fastapi.FastAPI(lifespan=lifespan))
    
    @app.get("/")
    async def root_get(
            cache: MemcachedClient=fastapi.Depends(depends_memcached),
    ) -> typing.Dict:
        await cache.set(b'Hello', b'World')
        await cache.get(b'Hello')
        return dict(ping=await cache.ping())
```

## Redis
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
* `REDIS_TTL` - Default `Time-To-Live` value. Default is `3600`.
* `REDIS_SENTINELS` - List or a tuple of Redis sentinel addresses.
* `REDIS_SENTINEL_MASTER` - The name of the master server in a sentinel configuration. Default is `mymaster`.
* `REDIS_PRESTART_TRIES` - The number tries to connect to the a Redis instance.
* `REDIS_PRESTART_WAIT` - The interval in seconds to wait between connection failures on application start.

### Example
```python
    # run with `uvicorn demo_app:app`
    import contextlib
    import typing
    import aioredis
    import fastapi
    import pydantic
    import fastapi_plugins
    
    class AppSettings(OtherSettings, fastapi_plugins.RedisSettings):
        api_name: str = str(__name__)
    
    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI):
        config = AppSettings()
        await fastapi_plugins.redis_plugin.init_app(app, config=config)
        await fastapi_plugins.redis_plugin.init()
        yield
        await fastapi_plugins.redis_plugin.terminate()
    
    app = fastapi_plugins.register_middleware(fastapi.FastAPI(lifespan=lifespan))
    
    
    @app.get("/")
    async def root_get(
            cache: aioredis.Redis=fastapi.Depends(fastapi_plugins.depends_redis),
    ) -> typing.Dict:
        return dict(ping=await cache.ping())
```

### Example with Docker Compose - Redis
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

### Example with Docker Compose - Redis Sentinel
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