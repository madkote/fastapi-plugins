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
import unittest

import fastapi
import pytest
import starlette.testclient

import fastapi_plugins

from . import VERSION
from . import d2json

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'


@pytest.mark.control
class ControlTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_app(self, config=None, version=None, environ=None):
        app = fastapi.FastAPI()
        if config is None:
            config = fastapi_plugins.ControlSettings()

        @app.on_event('startup')
        async def on_startup() -> None:
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
            r = await c.get_health()
            self.assertTrue(r, 'health failed')
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
                exp = {}
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
                exp = myenviron
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
                exp = {'status': 'UP'}
                res = response.json()
                self.assertTrue(d2json(exp) == d2json(res), '[%s] json : %s != %s' % (endpoint, exp, res))  # noqa E501
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
                exp = {'status': 'UP'}
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
                exp = {'status': 'UP'}
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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
