#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.scheduler
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2020, madkote

fastapi_plugins.scheduler
-------------------------
Scheduler plugin (based on `aiojobs`)
'''

from __future__ import absolute_import

import aiojobs
import fastapi
import pydantic
import starlette.requests

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin

from .version import VERSION

__all__ = [
    'SchedulerError', 'SchedulerSettings', 'SchedulerPlugin',
    'scheduler_plugin', 'depends_scheduler'
    # 'MadnessScheduler'
]
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2020, madkote'


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


class SchedulerPlugin(Plugin):
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
        factory = aiojobs.create_scheduler
        #
        # TODO: monkey patching is not preferred way, but waiting for aoilibs
        #
        # TODO: provide a pull request (custom, job, better scheduler)
        #
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#         if self.config.aiojobs_enable_cancel:
#             class _PatchJob(aiojobs._scheduler.Job):
#                 def __init__(self, *args, **kwargs):
#                     super(_PatchJob, self).__init__(*args, **kwargs)
#                     self._id = str(uuid.uuid4())
#
#                 @property
#                 def id(self):
#                     return self._id
#             aiojobs._scheduler.Job = _PatchJob
#             factory = create_madness_scheduler
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        self.scheduler = await factory(
            close_timeout=self.config.aiojobs_close_timeout,
            limit=self.config.aiojobs_limit,
            pending_limit=self.config.aiojobs_pending_limit
        )

    async def terminate(self):
        self.config = None
        if self.scheduler is not None:
            await self.scheduler.close()
            self.scheduler = None


scheduler_plugin = SchedulerPlugin()


async def depends_scheduler(
    request: starlette.requests.Request
) -> aiojobs.Scheduler:
    return await request.app.state.AIOJOBS_SCHEDULER()
