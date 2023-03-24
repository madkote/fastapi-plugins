#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.scheduler

from __future__ import absolute_import

import typing

import aiojobs
import fastapi
import pydantic
import starlette.requests

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin

from .control import ControlHealthMixin
from .utils import Annotated
from .version import VERSION

__all__ = [
    'SchedulerError', 'SchedulerSettings', 'SchedulerPlugin',
    'scheduler_plugin', 'depends_scheduler', 'TSchedulerPlugin'
    # 'MadnessScheduler'
]
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote'


class SchedulerError(PluginError):
    pass


# class MadnessScheduler(aiojobs.Scheduler):
#     def __init__(self, *args, **kwargs):
#         super(MadnessScheduler, self).__init__(*args, **kwargs)
#         self._job_map = {}
#
#     async def spawn(self, coro):
#         job = await aiojobs.Scheduler.spawn(self, coro)
#         self._job_map[job.id] = job
#         return job
#
#     def _done(self, job) -> None:
#         if job.id in self._job_map:
#             self._job_map.pop(job.id)
#         return aiojobs.Scheduler._done(self, job)
#
#     async def cancel_job(self, job_id: str) -> None:
#         if job_id in self._job_map:
#             await self._job_map[job_id].close()
#
#
# async def create_madness_scheduler(
#     *args,
#     close_timeout=0.1,
#     limit=100,
#     pending_limit=10000,
#     exception_handler=None
# ) -> MadnessScheduler:
#     if exception_handler is not None and not callable(exception_handler):
#         raise TypeError(
#             'A callable object or None is expected, got {!r}'.format(
#                 exception_handler
#             )
#         )
#     loop = asyncio.get_event_loop()
#     return MadnessScheduler(
#         loop=loop,
#         close_timeout=close_timeout,
#         limit=limit,
#         pending_limit=pending_limit,
#         exception_handler=exception_handler
#     )


# TODO: test settings (values)
# TODO: write unit tests
class SchedulerSettings(PluginSettings):
    aiojobs_close_timeout: float = 0.1
    aiojobs_limit: int = 100
    aiojobs_pending_limit: int = 10000
    # aiojobs_enable_cancel: bool = False


class SchedulerPlugin(Plugin, ControlHealthMixin):
    DEFAULT_CONFIG_CLASS = SchedulerSettings

    def _on_init(self) -> None:
        self.scheduler: aiojobs.Scheduler = None

    async def _on_call(self) -> aiojobs.Scheduler:
        if self.scheduler is None:
            raise SchedulerError('Scheduler is not initialized')
        return self.scheduler

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise SchedulerError('Scheduler configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise SchedulerError('Scheduler configuration is not valid')
        app.state.AIOJOBS_SCHEDULER = self

    async def init(self):
        if self.scheduler is not None:
            raise SchedulerError('Scheduler is already initialized')
        self.scheduler = aiojobs.Scheduler(
            close_timeout=self.config.aiojobs_close_timeout,
            limit=self.config.aiojobs_limit,
            pending_limit=self.config.aiojobs_pending_limit
        )

    async def terminate(self):
        self.config = None
        if self.scheduler is not None:
            await self.scheduler.close()
            self.scheduler = None

    async def health(self) -> typing.Dict:
        return dict(
            jobs=len(self.scheduler),
            active=self.scheduler.active_count,
            pending=self.scheduler.pending_count,
            limit=self.scheduler.limit,
            closed=self.scheduler.closed
        )


scheduler_plugin = SchedulerPlugin()


async def depends_scheduler(
    conn: starlette.requests.HTTPConnection
) -> aiojobs.Scheduler:
    return await conn.app.state.AIOJOBS_SCHEDULER()


TSchedulerPlugin = Annotated[aiojobs.Scheduler, fastapi.Depends(depends_scheduler)] # noqa E501
