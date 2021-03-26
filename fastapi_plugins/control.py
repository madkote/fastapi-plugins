#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.control
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote RES

fastapi_plugins.control
-----------------------
Controller plugin

-----------------------
/control
/control/health
/control/health/...
/control/version
-----------------------
TODO: control version must be object   -> ControlEnviron
TODO: control environ must be object   -> ControlVersion
TODO: health should be Health response -> ControlHealth

TODO: test base model with various pydantic version

TODO: add more routes to health
TODO: add health observer
'''

from __future__ import absolute_import

import typing

import fastapi
import pydantic
import starlette.requests

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin
from .version import VERSION

__all__ = [
    'ControlError', 'ControlSettings', 'Controller',
    'ControlPlugin', 'control_plugin', 'depends_control'
]
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'


DEFAULT_CONTROL_ROUTER_PREFIX = 'control'
DEFAULT_CONTROL_VERSION = '0.0.1'


class ControlError(PluginError):
    pass


class Controller(object):
    def __init__(
            self,
            router_prefix: str=DEFAULT_CONTROL_ROUTER_PREFIX,
            router_tag: str=DEFAULT_CONTROL_ROUTER_PREFIX,
            version: str=DEFAULT_CONTROL_VERSION,
            environ: typing.Dict=None
    ):
        self.router_prefix = router_prefix
        self.router_tag = router_tag
        self.version = version
        self.environ = environ

    def patch_app(self, app: fastapi.FastAPI) -> None:
        router_control = fastapi.APIRouter()

        @router_control.get(
            '/version',
            summary='Version',
            description='Get the version',
        )
        async def version_get() -> typing.Dict:
            return dict(version=await self.get_version())

        @router_control.get(
            '/environ',
            summary='Environment',
            description='Get the environment'
        )
        async def environ_get() -> typing.Dict:
            return dict(**(await self.get_environ()))

        @router_control.get(
            '/health',
            summary='Health',
            description='Get the health',
            responses={
                starlette.status.HTTP_200_OK: {
                    'description': 'UP and healthy',
                },
                starlette.status.HTTP_417_EXPECTATION_FAILED: {
                    'description': 'NOT healthy',
                }
            }
        )
        async def health_get() -> typing.Dict:
            if await self.get_health():
                return dict(status='UP')
            else:
                raise fastapi.HTTPException(
                    status_code=starlette.status.HTTP_417_EXPECTATION_FAILED,
                    detail='NOT healthy'
                )

        app.include_router(
            router_control,
            prefix='/' + self.router_prefix,
            tags=[self.router_tag],
        )

    async def get_environ(self) -> typing.Dict:
        return self.environ if self.environ is not None else {}

    async def get_health(self) -> bool:
        return True

    async def get_version(self) -> str:
        return self.version


class ControlSettings(PluginSettings):
    control_router_prefix: str = DEFAULT_CONTROL_ROUTER_PREFIX
    control_router_tag: str = DEFAULT_CONTROL_ROUTER_PREFIX


class ControlPlugin(Plugin):
    DEFAULT_CONFIG_CLASS = ControlSettings

    def _on_init(self) -> None:
        self.controller: Controller = None

    async def _on_call(self) -> Controller:
        if self.controller is None:
            raise ControlError('Control is not initialized')
        return self.controller

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None,
            *,
            version: str=DEFAULT_CONTROL_VERSION,
            environ: typing.Dict=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise ControlError('Control configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise ControlError('Control configuration is not valid')
        app.state.CONTROL = self
        #
        # initialize here while `app` is available
        self.controller = Controller(
            router_prefix=self.config.control_router_prefix,
            router_tag=self.config.control_router_tag,
            version=version,
            environ=environ
        )
        self.controller.patch_app(app)

    async def init(self):
        if self.controller is None:
            raise ControlError('Control cannot be initialized')

    async def terminate(self):
        self.config = None
        self.controller = None


control_plugin = ControlPlugin()


async def depends_control(
    request: starlette.requests.Request
) -> Controller:
    return await request.app.state.CONTROL()
