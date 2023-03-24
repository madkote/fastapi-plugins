#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.control
#
# Health is inspired by
# "https://dzone.com/articles/an-overview-of-health-check-patterns"
#

from __future__ import absolute_import

import abc
import asyncio
import pprint
import typing

import fastapi
import pydantic
import starlette.requests

from .plugin import PluginError
from .plugin import PluginSettings
from .plugin import Plugin
from .utils import Annotated

__all__ = [
    'ControlEnviron', 'ControlHealthCheck', 'ControlHealth',
    'ControlHealthError', 'ControlHeartBeat', 'ControlVersion',
    #
    'ControlError', 'ControlHealthMixin', 'ControlSettings', 'Controller',
    'ControlPlugin', 'control_plugin', 'depends_control', 'TControlPlugin'
]


DEFAULT_CONTROL_ROUTER_PREFIX = 'control'
DEFAULT_CONTROL_VERSION = '0.0.1'


class ControlError(PluginError):
    pass


class ControlBaseModel(pydantic.BaseModel):
    class Config:
        use_enum_values = True
        validate_all = True


class ControlEnviron(ControlBaseModel):
    environ: typing.Dict = pydantic.Field(
        ...,
        title='Environment',
        example=dict(var1='variable1', var2='variable2')
    )


class ControlHealthStatus(ControlBaseModel):
    status: bool = pydantic.Field(
        ...,
        title='Health status',
        example=True
    )


class ControlHealthCheck(ControlHealthStatus):
    name: str = pydantic.Field(
        ...,
        title='Health check name',
        min_length=1,
        example='Redis'
    )
    details: typing.Dict = pydantic.Field(
        ...,
        title='Health check details',
        example=dict(detail1='detail1', detail2='detail2')
    )


class ControlHealth(ControlHealthStatus):
    checks: typing.List[ControlHealthCheck] = pydantic.Field(
        ...,
        title='Health checks',
        example=[
            ControlHealthCheck(
                name='Redis',
                status=True,
                details=dict(
                    redis_type='redis',
                    redis_host='localhost',
                )
            ).dict()
        ]
    )


class ControlHealthError(ControlBaseModel):
    detail: ControlHealth = pydantic.Field(
        ...,
        title='Health error',
        example=ControlHealth(
            status=False,
            checks=[
                ControlHealthCheck(
                    name='Redis',
                    status=False,
                    details=dict(error='Some error')
                )
            ]
        )
    )


class ControlHeartBeat(ControlBaseModel):
    is_alive: bool = pydantic.Field(
        ...,
        title='Alive flag',
        example=True
    )


# class ControlInfo(ControlBaseModel):
#     status: str = pydantic.Field(
#         'API is up and running',
#         title='status',
#         min_length=1,
#         exampe='API is up and running'
#     )


class ControlVersion(ControlBaseModel):
    version: str = pydantic.Field(
        ...,
        title='Version',
        min_length=1,
        example='1.2.3'
    )


class ControlHealthMixin(object):
    @abc.abstractmethod
    async def health(self) -> typing.Dict:
        pass


class Controller(object):
    def __init__(
            self,
            router_prefix: str=DEFAULT_CONTROL_ROUTER_PREFIX,
            router_tag: str=DEFAULT_CONTROL_ROUTER_PREFIX,
            version: str=DEFAULT_CONTROL_VERSION,
            environ: typing.Dict=None,
            failfast: bool=True
    ):
        self.router_prefix = router_prefix
        self.router_tag = router_tag
        self.version = version
        self.environ = environ
        self.plugins: typing.List[ControlHealthMixin] = []
        self.failfast = failfast

    def patch_app(
            self,
            app: fastapi.FastAPI,
            enable_environ: bool=True,
            enable_health: bool=True,
            enable_heartbeat: bool=True,
            enable_version: bool=True
    ) -> None:
        #
        # register plugins
        for name, state in app.state._state.items():
            if isinstance(state, ControlHealthMixin):
                self.plugins.append((name, state))
        #
        # register endpoints
        if not (enable_environ or enable_health or enable_heartbeat or enable_version): # noqa E501
            return

        router_control = fastapi.APIRouter()

        if enable_version:
            @router_control.get(
                '/version',
                summary='Version',
                description='Get the version',
                response_model=ControlVersion
            )
            async def version_get() -> ControlVersion:
                return ControlVersion(version=await self.get_version())

        if enable_environ:
            @router_control.get(
                '/environ',
                summary='Environment',
                description='Get the environment',
                response_model=ControlEnviron
            )
            async def environ_get() -> ControlEnviron:
                return ControlEnviron(
                    environ=dict(**(await self.get_environ()))
                )

        if enable_heartbeat:
            @router_control.get(
                '/heartbeat',
                summary='Heart beat',
                description='Get the alive signal',
                response_model=ControlHeartBeat
            )
            async def heartbeat_get() -> ControlHeartBeat:
                return ControlHeartBeat(is_alive=await self.get_heart_beat())

        if enable_health:
            @router_control.get(
                '/health',
                summary='Health',
                description='Get the health',
                response_model=ControlHealth,
                responses={
                    starlette.status.HTTP_200_OK: dict(
                        description='UP and healthy',
                        model=ControlHealth
                    ),
                    starlette.status.HTTP_417_EXPECTATION_FAILED: dict(
                        description='NOT healthy',
                        model=ControlHealthError
                    )
                }
            )
            async def health_get() -> ControlHealth:
                health = await self.get_health()
                if health.status:
                    return health
                else:
                    raise fastapi.HTTPException(
                        status_code=starlette.status.HTTP_417_EXPECTATION_FAILED,   # noqa E501
                        detail=health.dict()
                    )

        #
        # register router
        app.include_router(
            router_control,
            prefix='' if not self.router_prefix else '/' + self.router_prefix,
            tags=[self.router_tag],
        )

    async def register_plugin(self, plugin: ControlHealthMixin):
        raise NotImplementedError

    async def get_environ(self) -> typing.Dict:
        return self.environ if self.environ is not None else {}

    async def get_health(self) -> ControlHealth:
        shared_obj = type('', (), {})()
        shared_obj.status = True

        # TODO: implement failfast -> wait()
        async def wrappit(name, hfunc) -> ControlHealthCheck:
            try:
                details = await hfunc or {}
                status = True
            except Exception as e:
                details = dict(error=str(e))
                status = False
                shared_obj.status = False
            finally:
                return ControlHealthCheck(
                    name=name,
                    status=status,
                    details=details
                )

        # TODO: perform all checks with this function asyncio.wait(fs)
        # TODO: perform without shared object
        results = await asyncio.gather(
            *[wrappit(name, plugin.health()) for name, plugin in self.plugins]
        )
        return ControlHealth(
            status=shared_obj.status,
            checks=results
        )

    async def get_heart_beat(self) -> bool:
        return True

    async def get_version(self) -> str:
        return self.version


class ControlSettings(PluginSettings):
    control_router_prefix: str = DEFAULT_CONTROL_ROUTER_PREFIX
    control_router_tag: str = DEFAULT_CONTROL_ROUTER_PREFIX
    control_enable_environ: bool = True
    control_enable_health: bool = True
    control_enable_heartbeat: bool = True
    control_enable_version: bool = True


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
        app.state.PLUGIN_CONTROL = self
        #
        # initialize here while `app` is available
        self.controller = Controller(
            router_prefix=self.config.control_router_prefix,
            router_tag=self.config.control_router_tag,
            version=version,
            environ=environ
        )
        self.controller.patch_app(
            app,
            enable_environ=self.config.control_enable_environ,
            enable_health=self.config.control_enable_health,
            enable_heartbeat=self.config.control_enable_heartbeat,
            enable_version=self.config.control_enable_version
        )

    async def init(self):
        if self.controller is None:
            raise ControlError('Control cannot be initialized')
        if self.config.control_enable_health:
            health = await self.controller.get_health()
            if not health.status:
                print()
                print('-' * 79)
                pprint.pprint(health.dict())
                print('-' * 79)
                print()
                raise ControlError('failed health control')

    async def terminate(self):
        self.config = None
        self.controller = None


control_plugin = ControlPlugin()


async def depends_control(
    conn: starlette.requests.HTTPConnection
) -> Controller:
    return await conn.app.state.PLUGIN_CONTROL()


TControlPlugin = Annotated[Controller, fastapi.Depends(depends_control)]
