#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_settings
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote RES

tests.test_settings
-------------------
Settings tests
'''

from __future__ import absolute_import

import asyncio
import os
import unittest

import fastapi
# import pydantic
import pytest

import fastapi_plugins

from fastapi_plugins.settings import ConfigManager

from . import VERSION
from . import d2json

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'


@pytest.mark.settings
class TestSettings(unittest.TestCase):
    def setUp(self):
        fastapi_plugins.reset_config()
        fastapi_plugins.get_config.cache_clear()

    def tearDown(self):
        fastapi_plugins.reset_config()
        fastapi_plugins.get_config.cache_clear()

    def test_manager_register(self):
        class MyConfig(fastapi_plugins.PluginSettings):
            api_name: str = 'API name'

        name = 'myconfig'

        m = ConfigManager()
        m.register(name, MyConfig)

        exp = {name: MyConfig}
        res = m._settings_map
        self.assertTrue(res == exp, 'register failed')

    def test_manager_reset(self):
        class MyConfig(fastapi_plugins.PluginSettings):
            api_name: str = 'API name'

        name = 'myconfig'

        m = ConfigManager()
        m.register(name, MyConfig)

        exp = {name: MyConfig}
        res = m._settings_map
        self.assertTrue(res == exp, 'register failed')

        m.reset()
        exp = {}
        res = m._settings_map
        self.assertTrue(res == exp, 'reset failed')

    def test_manager_get_config(self):
        class MyConfig(fastapi_plugins.PluginSettings):
            api_name: str = 'API name'

        name = 'myconfig'

        m = ConfigManager()
        m.register(name, MyConfig)

        exp = {name: MyConfig}
        res = m._settings_map
        self.assertTrue(res == exp, 'register failed')

        exp = d2json(MyConfig().dict())
        res = d2json(m.get_config(name).dict())
        self.assertTrue(res == exp, 'get configuration failed')

    def test_manager_get_config_default(self):
        class MyConfig(fastapi_plugins.PluginSettings):
            api_name: str = 'API name'

        name = fastapi_plugins.CONFIG_NAME_DEFAULT

        m = ConfigManager()
        m.register(name, MyConfig)

        exp = {name: MyConfig}
        res = m._settings_map
        self.assertTrue(res == exp, 'register failed')

        exp = d2json(MyConfig().dict())
        res = d2json(m.get_config().dict())
        self.assertTrue(res == exp, 'get configuration failed')

    def test_manager_get_config_not_existing(self):
        class MyConfig(fastapi_plugins.PluginSettings):
            api_name: str = 'API name'

        name = 'myconfig'

        m = ConfigManager()
        m.register(name, MyConfig)

        exp = {name: MyConfig}
        res = m._settings_map
        self.assertTrue(res == exp, 'register failed')

        try:
            m.get_config()
        except fastapi_plugins.ConfigError:
            pass
        else:
            self.fail('configuration should not exist')

    def test_wrap_register_config(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            fastapi_plugins.register_config(MyConfig)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config().dict())
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_register_config_docker(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            # docker is default
            fastapi_plugins.register_config_docker(MyConfig)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config().dict())
            self.assertTrue(res == exp, 'get configuration failed')
            #
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_DOCKER).dict()) # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_register_config_local(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            #
            fastapi_plugins.register_config_local(MyConfig)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_LOCAL).dict())  # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
            #
            os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_LOCAL  # noqa E501
            try:
                exp = d2json(MyConfig().dict())
                res = d2json(fastapi_plugins.get_config().dict())
                self.assertTrue(res == exp, 'get configuration failed')
            finally:
                os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_register_config_test(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            #
            fastapi_plugins.register_config_test(MyConfig)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_TEST).dict())  # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
            #
            os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_TEST  # noqa E501
            try:
                exp = d2json(MyConfig().dict())
                res = d2json(fastapi_plugins.get_config().dict())
                self.assertTrue(res == exp, 'get configuration failed')
            finally:
                os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_register_config_by_name(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            name = 'myconfig'
            fastapi_plugins.register_config(MyConfig, name=name)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(name).dict())
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_get_config(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            fastapi_plugins.register_config(MyConfig)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config().dict())
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_get_config_by_name(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            name = 'myconfig'
            fastapi_plugins.register_config(MyConfig, name=name)
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(name).dict())
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_wrap_reset_config(self):
        try:
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            from fastapi_plugins.settings import _manager

            exp = {}
            res = _manager._settings_map
            self.assertTrue(res == exp, 'reset init failed')

            fastapi_plugins.register_config(MyConfig)

            exp = {fastapi_plugins.CONFIG_NAME_DOCKER: MyConfig}
            res = _manager._settings_map
            self.assertTrue(res == exp, 'reset register failed')

            fastapi_plugins.reset_config()

            exp = {}
            res = _manager._settings_map
            self.assertTrue(res == exp, 'reset failed')
        finally:
            fastapi_plugins.reset_config()

    def test_decorator_register_config(self):
        try:
            @fastapi_plugins.registered_configuration
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config().dict())
            self.assertTrue(res == exp, 'get configuration failed: %s != %s' % (exp, res))  # noqa E501
        finally:
            fastapi_plugins.reset_config()

    def test_decorator_register_config_docker(self):
        try:
            @fastapi_plugins.registered_configuration_docker
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            # docker is default
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config().dict())
            self.assertTrue(res == exp, 'get configuration failed')
            #
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_DOCKER).dict()) # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_decorator_register_config_local(self):
        try:
            @fastapi_plugins.registered_configuration_local
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            #
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_LOCAL).dict()) # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
            #
            os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_LOCAL   # noqa E501
            try:
                exp = d2json(MyConfig().dict())
                res = d2json(fastapi_plugins.get_config().dict())
                self.assertTrue(res == exp, 'get configuration failed')
            finally:
                os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
        finally:
            fastapi_plugins.reset_config()

    def test_decorator_register_config_test(self):
        try:
            @fastapi_plugins.registered_configuration_test
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            #
            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_TEST).dict())   # noqa E501
            self.assertTrue(res == exp, 'get configuration failed')
            #
            os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_TEST    # noqa E501
            try:
                exp = d2json(MyConfig().dict())
                res = d2json(fastapi_plugins.get_config().dict())
                self.assertTrue(res == exp, 'get configuration failed')
            finally:
                os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
        finally:
            fastapi_plugins.reset_config()

    def test_decorator_register_config_by_name(self):
        try:
            name = 'myconfig'

            @fastapi_plugins.registered_configuration(name=name)
            class MyConfig(fastapi_plugins.PluginSettings):
                api_name: str = 'API name'

            exp = d2json(MyConfig().dict())
            res = d2json(fastapi_plugins.get_config(name).dict())
            self.assertTrue(res == exp, 'get configuration failed')
        finally:
            fastapi_plugins.reset_config()

    def test_app_config(self):
        async def _test():
            @fastapi_plugins.registered_configuration
            class MyConfigDocker(fastapi_plugins.PluginSettings):
                api_name: str = 'docker'

            @fastapi_plugins.registered_configuration_local
            class MyConfigLocal(fastapi_plugins.PluginSettings):
                api_name: str = 'local'

            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.get_config()

            await fastapi_plugins.config_plugin.init_app(app=app, config=config)    # noqa E501
            await fastapi_plugins.config_plugin.init()

            try:
                c = await fastapi_plugins.config_plugin()
                exp = d2json(MyConfigDocker().dict())
                res = d2json(c.dict())
                self.assertTrue(res == exp, 'get configuration failed')
            finally:
                await fastapi_plugins.config_plugin.terminate()
                fastapi_plugins.reset_config()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_app_config_environ(self):
        async def _test():
            os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_LOCAL   # noqa E501
            try:
                @fastapi_plugins.registered_configuration
                class MyConfigDocker(fastapi_plugins.PluginSettings):
                    api_name: str = 'docker'

                @fastapi_plugins.registered_configuration_local
                class MyConfigLocal(fastapi_plugins.PluginSettings):
                    api_name: str = 'local'

                app = fastapi_plugins.register_middleware(fastapi.FastAPI())
                config = fastapi_plugins.get_config()

                await fastapi_plugins.config_plugin.init_app(app=app, config=config)    # noqa E501
                await fastapi_plugins.config_plugin.init()

                try:
                    c = await fastapi_plugins.config_plugin()
                    exp = d2json(MyConfigLocal().dict())
                    res = d2json(c.dict())
                    self.assertTrue(res == exp, 'get configuration failed: %s != %s' % (exp, res))  # noqa E501
                finally:
                    await fastapi_plugins.config_plugin.terminate()
            finally:
                os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
                fastapi_plugins.reset_config()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
