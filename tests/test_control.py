#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_control
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote RES

tests.test_control
------------------
Module
'''

from __future__ import absolute_import

import asyncio
import typing
import unittest

import fastapi
import pydantic
import pytest
import starlette.testclient

import fastapi_plugins

from fastapi_plugins.memcached import memcached_plugin
from fastapi_plugins.memcached import MemcachedSettings

from . import VERSION
from . import d2json

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'


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


@pytest.mark.control
class ControlTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_app(self, config=None, version=None, environ=None, plugins=None):
        if plugins is None:
            plugins = []
        app = fastapi.FastAPI()
        if config is None:
            config = fastapi_plugins.ControlSettings()

        @app.on_event('startup')
        async def on_startup() -> None:
            for p in plugins:
                await p.init_app(app, config)
                await p.init()
            kwargs = {}
            if version:
                kwargs.update(**dict(version=version))
            if environ:
                kwargs.update(**dict(environ=environ))
            await fastapi_plugins.control_plugin.init_app(app, config, **kwargs)    # noqa E501
            await fastapi_plugins.control_plugin.init()

        @app.on_event('shutdown')
        async def on_shutdown() -> None:
            await fastapi_plugins.control_plugin.terminate()
            for p in plugins:
                await p.terminate()

        return app

    # =========================================================================
    # CONTROLLER
    # =========================================================================
    def test_controller_environ(self):
        async def _test():
            c = fastapi_plugins.Controller()
            res = await c.get_environ()
            exp = {}
            self.assertTrue(d2json(exp) == d2json(res), 'environ failed')
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_environ_custom(self):
        async def _test():
            exp = dict(ping='pong')
            c = fastapi_plugins.Controller(environ=exp)
            res = await c.get_environ()
            self.assertTrue(d2json(exp) == d2json(res), 'environ failed')
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_health(self):
        async def _test():
            c = fastapi_plugins.Controller()
            exp = dict(status=True, checks=[])
            res = (await c.get_health()).dict()
            self.assertTrue(
                d2json(exp) == d2json(res),
                'health failed: %s != %s' % (exp, res)
            )
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_health_plugin_ok(self):
        async def _test():
            app = fastapi.FastAPI()
            config = fastapi_plugins.ControlSettings()
            dummy = DummyPluginHealthOK()
            await dummy.init_app(app, config)
            await dummy.init()
            try:
                c = fastapi_plugins.Controller()
                c.plugins.append(('DUMMY_PLUGIN_OK', dummy))
                exp = dict(
                    status=True,
                    checks=[
                        dict(
                            name='DUMMY_PLUGIN_OK',
                            status=True,
                            details=dict(dummy='OK')
                        )
                    ]
                )
                res = (await c.get_health()).dict()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await dummy.terminate()
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_health_plugin_notdefined(self):
        async def _test():
            app = fastapi.FastAPI()
            config = fastapi_plugins.ControlSettings()
            dummy = DummyPluginHealthNotDefined()
            await dummy.init_app(app, config)
            await dummy.init()
            try:
                c = fastapi_plugins.Controller()
                c.plugins.append(('DUMMY_PLUGIN_NOT_DEFINED', dummy))
                exp = dict(
                    status=True,
                    checks=[
                        dict(
                            name='DUMMY_PLUGIN_NOT_DEFINED',
                            status=True,
                            details={}
                        )
                    ]
                )
                res = (await c.get_health()).dict()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await dummy.terminate()
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_health_plugin_failing(self):
        async def _test():
            app = fastapi.FastAPI()
            config = fastapi_plugins.ControlSettings()
            dummy = DummyPluginHealthFail()
            await dummy.init_app(app, config)
            await dummy.init()
            try:
                c = fastapi_plugins.Controller()
                c.plugins.append(('DUMMY_PLUGIN_HEALTH_FAIL', dummy))
                exp = dict(
                    status=False,
                    checks=[
                        dict(
                            name='DUMMY_PLUGIN_HEALTH_FAIL',
                            status=False,
                            details=dict(error='Health check failed')
                        )
                    ]
                )
                res = (await c.get_health()).dict()
                self.assertTrue(
                    d2json(exp) == d2json(res),
                    'health failed: %s != %s' % (exp, res)
                )
            finally:
                await dummy.terminate()
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_heartbeat(self):
        async def _test():
            c = fastapi_plugins.Controller()
            exp = True
            res = await c.get_heart_beat()
            self.assertTrue(
                exp == res,
                'heart beat failed: %s != %s' % (exp, res)
            )
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_version(self):
        async def _test():
            from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
            c = fastapi_plugins.Controller()
            r = await c.get_version()
            self.assertTrue(r == DEFAULT_CONTROL_VERSION, 'version failed')
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    def test_controller_version_custom(self):
        async def _test():
            v = '1.2.3'
            c = fastapi_plugins.Controller(version=v)
            r = await c.get_version()
            self.assertTrue(r == v, 'version failed')
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        coro = asyncio.coroutine(_test)
        event_loop.run_until_complete(coro())
        event_loop.close()

    # =========================================================================
    # ROUTER
    # =========================================================================
    def test_router_environ(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(self.make_app())
            with client as c:
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(environ={})
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_environ_custom(self):
        myenviron = dict(ping='pong')
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app(environ=myenviron)
            )
            with client as c:
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(environ=myenviron)
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_version(self):
        from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(self.make_app())
            with client as c:
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': DEFAULT_CONTROL_VERSION}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_version_custom(self):
        myversion = '1.2.3'
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app(version=myversion)
            )
            with client as c:
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': myversion}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_heartbeat(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app()
            )
            with client as c:
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(is_alive=True)
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_health(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app()
            )
            with client as c:
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_health_with_plugins(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app(
                    plugins=[
                        DummyPluginHealthNotDefined(),
                        DummyPluginHealthOK()
                    ]
                )
            )
            with client as c:
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(
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
                )
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_health_with_plugins_full(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            class MyConfig(
                    fastapi_plugins.RedisSettings,
                    fastapi_plugins.SchedulerSettings,
                    fastapi_plugins.ControlSettings,
                    MemcachedSettings
            ):
                pass

            client = starlette.testclient.TestClient(
                self.make_app(
                    config=MyConfig(),
                    plugins=[
                        fastapi_plugins.redis_plugin,
                        fastapi_plugins.scheduler_plugin,
                        memcached_plugin
                    ]
                )
            )
            with client as c:
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(
                    status=True,
                    checks=[
                        {
                            'name': 'REDIS',
                            'status': True,
                            'details': {
                                'redis_type': 'redis',
                                'redis_address': 'redis://localhost:6379/0',
                                'redis_pong': 'PONG'
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
                                'version': '1.6.9'
                            }
                        }
                    ]
                )
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_health_with_plugins_broken(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app(
                    plugins=[
                        DummyPluginHealthNotDefined(),
                        DummyPluginHealthOK(),
                        DummyPluginHealthOKOnce()
                    ]
                )
            )
            with client as c:
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 417
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {
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
                }
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_health_with_plugins_broken_init(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            client = starlette.testclient.TestClient(
                self.make_app(
                    plugins=[
                        DummyPluginHealthFail(),
                        DummyPluginHealthOK()
                    ]
                )
            )
            try:
                with client as c:
                    endpoint = '/control/version'
                    c.get(endpoint)
            except fastapi_plugins.ControlError:
                pass
            else:
                self.fail('health on app initialization should fail')
        finally:
            event_loop.close()

    def test_router_prefix_custom(self):
        from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            config = fastapi_plugins.ControlSettings(
                control_router_prefix='outofcontrol'
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config)
            )
            with client as c:
                #
                endpoint = '/%s/health' % config.control_router_prefix
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/%s/version' % config.control_router_prefix
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': DEFAULT_CONTROL_VERSION}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_prefix_version_custom(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            myversion = '3.2.1'
            config = fastapi_plugins.ControlSettings(
                control_router_prefix='outofcontrol'
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config, version=myversion)
            )
            with client as c:
                #
                endpoint = '/%s/health' % config.control_router_prefix
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/%s/version' % config.control_router_prefix
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': myversion}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_disable(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            config = fastapi_plugins.ControlSettings(
                control_enable_environ=False,
                control_enable_health=False,
                control_enable_heartbeat=False,
                control_enable_version=False
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config)
            )
            with client as c:
                #
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_disable_environ(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
            config = fastapi_plugins.ControlSettings(
                control_enable_environ=False,
                control_enable_health=True,
                control_enable_heartbeat=True,
                control_enable_version=True
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config)
            )
            with client as c:
                #
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': DEFAULT_CONTROL_VERSION}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'is_alive': True}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_disable_version(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            config = fastapi_plugins.ControlSettings(
                control_enable_environ=True,
                control_enable_heartbeat=True,
                control_enable_health=True,
                control_enable_version=False
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config)
            )
            with client as c:
                #
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(environ={})
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'is_alive': True}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_disable_health(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
            config = fastapi_plugins.ControlSettings(
                control_enable_environ=True,
                control_enable_health=False,
                control_enable_heartbeat=True,
                control_enable_version=True
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config, plugins=[DummyPluginHealthFail()])
            )
            with client as c:
                #
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(environ={})
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': DEFAULT_CONTROL_VERSION}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'is_alive': True}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()

    def test_router_disable_heartbeat(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            from fastapi_plugins.control import DEFAULT_CONTROL_VERSION
            config = fastapi_plugins.ControlSettings(
                control_enable_environ=True,
                control_enable_health=True,
                control_enable_heartbeat=False,
                control_enable_version=True
            )
            client = starlette.testclient.TestClient(
                self.make_app(config=config)
            )
            with client as c:
                #
                endpoint = '/control/environ'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(environ={})
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/version'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = {'version': DEFAULT_CONTROL_VERSION}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/heartbeat'
                response = c.get(endpoint)
                exp = 404
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                #
                endpoint = '/control/health'
                response = c.get(endpoint)
                exp = 200
                res = response.status_code
                self.assertTrue(exp == res, '[%s] status code : %s != %s' % (endpoint, exp, res))  # noqa E501
                exp = dict(status=True, checks=[])
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
        finally:
            event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
