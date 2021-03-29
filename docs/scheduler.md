# Scheduler
Simple schedule an _awaitable_ job as a task. 
* _long_ running `async` functions (e.g. monitor a file a system or events)
* gracefully cancel spawned tasks

Valid variable are:
* `AIOJOBS_CLOSE_TIMEOUT` - The timeout in seconds before canceling a task.
* `AIOJOBS_LIMIT` - The number of concurrent tasks to be executed.
* `AIOJOBS_PENDING_LIMIT` - The number of pending jobs (waiting fr execution).


```python
'''run with `uvicorn demo_app:app` '''
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