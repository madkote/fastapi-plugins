#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_control

from __future__ import absolute_import

import contextlib
import typing

import fastapi
import pydantic
import pytest
import starlette.testclient

import fastapi_plugins

from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
from fastapi_plugins.memcached import memcached_plugin
from fastapi_plugins.memcached import MemcachedSettings


pytestmark = [pytest.mark.anyio, pytest.mark.control]


class DummyPluginHealthOK(
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
        app.state.DUMMY_PLUGIN_HEALTH_OK = self

    async def health(self) -> typing.Dict:
        return dict(dummy='OK')


class DummyPluginHealthOKOnce(
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
        app.state.DUMMY_PLUGIN_HEALTH_OK_ONCE = self

    async def health(self) -> typing.Dict:
        if self.counter > 0:
            raise Exception('Health check failed')
        else:
            self.counter += 1
            return dict(dummy='OK')


class DummyPluginHealthFail(
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
        app.state.DUMMY_PLUGIN_HEALTH_FAIL = self

    async def health(self) -> typing.Dict:
        raise Exception('Health check failed')


class DummyPluginHealthNotDefined(
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
        app.state.DUMMY_PLUGIN_NOT_DEFINED = self


class MyControlConfig(
        fastapi_plugins.RedisSettings,
        fastapi_plugins.SchedulerSettings,
        fastapi_plugins.ControlSettings,
        MemcachedSettings
):
    pass


def make_app(config=None, version=None, environ=None, plugins=None):
    if plugins is None:
        plugins = []
    if config is None:
        config = fastapi_plugins.ControlSettings()

    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI):
        for p in plugins:
            await p.init_app(app, config)
            await p.init()
        kwargs = {}
        if version:
            kwargs.update(**dict(version=version))
        if environ:
            kwargs.update(**dict(environ=environ))
        await fastapi_plugins.control_plugin.init_app(app, config, **kwargs)
        await fastapi_plugins.control_plugin.init()
        yield
        await fastapi_plugins.control_plugin.terminate()
        for p in plugins:
            await p.terminate()

    return fastapi_plugins.register_middleware(
        fastapi.FastAPI(lifespan=lifespan)
    )


@pytest.fixture(params=[{}])
def client(request):
    with starlette.testclient.TestClient(make_app(**request.param)) as c:
        yield c


@pytest.mark.parametrize(
    'kwargs, result',
    [
        pytest.param({}, {}),
        pytest.param(dict(environ=dict(ping='pong')), dict(ping='pong')),
    ]
)
async def test_controller_environ(kwargs, result):
    assert result == await fastapi_plugins.Controller(**kwargs).get_environ()


async def test_controller_health():
    assert dict(status=True, checks=[]) == (await fastapi_plugins.Controller().get_health()).dict() # noqa E501


@pytest.mark.parametrize(
    'klass, name, status, details',
    [
        pytest.param(
            DummyPluginHealthOK,
            'DUMMY_PLUGIN_OK',
            True,
            dict(dummy='OK')
        ),
        pytest.param(
            DummyPluginHealthNotDefined,
            'DUMMY_PLUGIN_NOT_DEFINED',
            True,
            {}
        ),
        pytest.param(
            DummyPluginHealthFail,
            'DUMMY_PLUGIN_HEALTH_FAIL',
            False,
            dict(error='Health check failed')
        ),
    ]
)
async def test_controller_health_plugin(
    klass, name, status, details
):
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = fastapi_plugins.ControlSettings()
    dummy = klass()
    await dummy.init_app(app, config)
    await dummy.init()
    try:
        c = fastapi_plugins.Controller()
        c.plugins.append((name, dummy))
        assert (await c.get_health()).dict() == dict(
            status=status,
            checks=[
                dict(
                    name=name,
                    status=status,
                    details=details
                )
            ]
        )
    finally:
        await dummy.terminate()


async def test_controller_heartbeat():
    assert await fastapi_plugins.Controller().get_heart_beat() is True


@pytest.mark.parametrize(
    'kwargs, version',
    [
        pytest.param({}, DEFAULT_CONTROL_VERSION),
        pytest.param(dict(version='1.2.3'), '1.2.3'),
    ]
)
async def test_controller_version(kwargs, version):
    assert version == await fastapi_plugins.Controller(**kwargs).get_version()


@pytest.mark.parametrize(
    'client, result, status, endpoint',
    [
        pytest.param(
            {},
            dict(environ={}),
            200,
            '/control/environ'
        ),
        pytest.param(
            dict(environ=dict(ping='pong')),
            dict(environ=dict(ping='pong')),
            200,
            '/control/environ'
        ),
        pytest.param(
            {},
            {'version': DEFAULT_CONTROL_VERSION},
            200,
            '/control/version'
        ),
        pytest.param(
            dict(version='1.2.3'),
            {'version': '1.2.3'},
            200,
            '/control/version'
        ),
        pytest.param(
            {},
            dict(is_alive=True),
            200,
            '/control/heartbeat'
        ),
        pytest.param(
            {},
            dict(status=True, checks=[]),
            200,
            '/control/health'
        ),
        pytest.param(
            dict(
                plugins=[
                    DummyPluginHealthNotDefined(),
                    DummyPluginHealthOK()
                ]
            ),
            dict(
                status=True,
                checks=[
                    dict(
                        name='DUMMY_PLUGIN_NOT_DEFINED',
                        status=True,
                        details={}
                    ),
                    dict(
                        name='DUMMY_PLUGIN_HEALTH_OK',
                        status=True,
                        details=dict(dummy='OK')
                    )
                ]
            ),
            200,
            '/control/health'
        ),
        pytest.param(
            dict(
                config=MyControlConfig(),
                plugins=[
                    fastapi_plugins.redis_plugin,
                    fastapi_plugins.scheduler_plugin,
                    memcached_plugin
                ]
            ),
            dict(
                status=True,
                checks=[
                    {
                        'name': 'REDIS',
                        'status': True,
                        'details': {
                            'redis_type': 'redis',
                            'redis_address': 'redis://localhost:6379',
                            'redis_pong': True
                        }
                    },
                    {
                        'name': 'AIOJOBS_SCHEDULER',
                        'status': True,
                        'details': {
                            'jobs': 0,
                            'active': 0,
                            'pending': 0,
                            'limit': 100,
                            'closed': False
                        }
                    },
                    {
                        'name': 'MEMCACHED',
                        'status': True,
                        'details': {
                            'host': 'localhost',
                            'port': 11211,
                            'version': '1.6.18'
                        }
                    }
                ]
            ),
            200,
            '/control/health',
        ),
        pytest.param(
            dict(
                plugins=[
                    DummyPluginHealthNotDefined(),
                    DummyPluginHealthOK(),
                    DummyPluginHealthOKOnce()
                ]
            ),
            {
                'detail': {
                    'status': False,
                    'checks': [
                        {
                            'name': 'DUMMY_PLUGIN_NOT_DEFINED',
                            'status': True,
                            'details': {}
                        },
                        {
                            'name': 'DUMMY_PLUGIN_HEALTH_OK',
                            'status': True,
                            'details': {'dummy': 'OK'}
                        },
                        {
                            'name': 'DUMMY_PLUGIN_HEALTH_OK_ONCE',
                            'status': False,
                            'details': {'error': 'Health check failed'}
                        }
                    ]
                }
            },
            417,
            '/control/health'
        ),
    ],
    indirect=['client']
)
async def test_router(client, result, status, endpoint):
    response = client.get(endpoint)
    assert status == response.status_code
    assert result == response.json()


async def test_router_health_with_plugins_broken_init():
    with pytest.raises(fastapi_plugins.ControlError):
        with starlette.testclient.TestClient(
            make_app(
                plugins=[
                    DummyPluginHealthFail(),
                    DummyPluginHealthOK()
                ]
            )
        ) as c:
            c.get('/control/version')


@pytest.mark.parametrize(
    'client, result, status, endpoint',
    [
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_router_prefix='outofcontrol'
                )
            ),
            dict(status=True, checks=[]),
            200,
            '/outofcontrol/health'
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_router_prefix='outofcontrol'
                )
            ),
            {'version': DEFAULT_CONTROL_VERSION},
            200,
            '/outofcontrol/version'
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_router_prefix='outofcontrol'
                ),
                version='1.2.3'
            ),
            {'version': '1.2.3'},
            200,
            '/outofcontrol/version'
        ),
    ],
    indirect=['client']
)
async def test_router_prefix_custom(client, result, status, endpoint):
    response = client.get(endpoint)
    assert status == response.status_code
    assert result == response.json()


@pytest.mark.parametrize(
    'client, endpoints',
    [
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_enable_environ=False,
                    control_enable_health=False,
                    control_enable_heartbeat=False,
                    control_enable_version=False
                )
            ),
            [
                (404, '/control/environ'),
                (404, '/control/version'),
                (404, '/control/heartbeat'),
                (404, '/control/health')
            ]
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_enable_environ=False,
                    control_enable_health=True,
                    control_enable_heartbeat=True,
                    control_enable_version=True
                )
            ),
            [
                (404, '/control/environ'),
                (200, '/control/version'),
                (200, '/control/heartbeat'),
                (200, '/control/health')
            ]
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_enable_environ=True,
                    control_enable_health=True,
                    control_enable_heartbeat=True,
                    control_enable_version=False
                )
            ),
            [
                (200, '/control/environ'),
                (404, '/control/version'),
                (200, '/control/heartbeat'),
                (200, '/control/health')
            ]
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_enable_environ=True,
                    control_enable_health=False,
                    control_enable_heartbeat=True,
                    control_enable_version=True
                )
            ),
            [
                (200, '/control/environ'),
                (200, '/control/version'),
                (200, '/control/heartbeat'),
                (404, '/control/health')
            ]
        ),
        pytest.param(
            dict(
                config=fastapi_plugins.ControlSettings(
                    control_enable_environ=True,
                    control_enable_health=True,
                    control_enable_heartbeat=False,
                    control_enable_version=True
                )
            ),
            [
                (200, '/control/environ'),
                (200, '/control/version'),
                (404, '/control/heartbeat'),
                (200, '/control/health')
            ]
        ),
    ],
    indirect=['client']
)
async def test_router_disable(client, endpoints):
    for status, endpoint in endpoints:
        response = client.get(endpoint)
        assert status == response.status_code
