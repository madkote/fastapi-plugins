#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_settings

from __future__ import absolute_import

import os

import fastapi
import pytest

import fastapi_plugins

from fastapi_plugins.settings import ConfigManager


pytestmark = [pytest.mark.anyio, pytest.mark.settings]


@pytest.fixture
def myconfig():
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    return MyConfig


@pytest.fixture
def myconfig_name():
    return 'myconfig'


@pytest.fixture
def myconfig_name_default():
    return fastapi_plugins.CONFIG_NAME_DEFAULT


@pytest.fixture
def plugin():
    fastapi_plugins.reset_config()
    fastapi_plugins.get_config.cache_clear()
    yield fastapi_plugins
    fastapi_plugins.reset_config()
    fastapi_plugins.get_config.cache_clear()


def test_manager_register(plugin, myconfig, myconfig_name):
    m = ConfigManager()
    m.register(myconfig_name, myconfig)
    assert m._settings_map == {myconfig_name: myconfig}


def test_manager_reset(plugin, myconfig, myconfig_name):
    m = ConfigManager()
    m.register(myconfig_name, myconfig)
    assert m._settings_map == {myconfig_name: myconfig}
    m.reset()
    assert m._settings_map == {}


@pytest.mark.parametrize(
    'name',
    [
        pytest.param('myconfig_name'),
        pytest.param('myconfig_name_default'),
    ]
)
def test_manager_get_config(name, plugin, myconfig, request):
    name = request.getfixturevalue(name)
    m = ConfigManager()
    m.register(name, myconfig)
    assert m._settings_map == {name: myconfig}
    assert myconfig().model_dump() == m.get_config(name).model_dump()


def test_manager_get_config_not_existing(plugin, myconfig, myconfig_name):
    m = ConfigManager()
    m.register(myconfig_name, myconfig)
    assert m._settings_map == {myconfig_name: myconfig}
    with pytest.raises(fastapi_plugins.ConfigError):
        m.get_config()


def test_wrap_register_config(plugin, myconfig):
    fastapi_plugins.register_config(myconfig)
    assert myconfig().model_dump() == fastapi_plugins.get_config().model_dump()


def test_wrap_register_config_docker(plugin, myconfig):
    # docker is default
    fastapi_plugins.register_config_docker(myconfig)
    assert myconfig().model_dump() == fastapi_plugins.get_config().model_dump()
    assert myconfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_DOCKER).model_dump()   # noqa E501


def test_wrap_register_config_local(plugin, myconfig):
    fastapi_plugins.register_config_local(myconfig)
    assert myconfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_LOCAL).model_dump()    # noqa E501
    os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_LOCAL                           # noqa E501
    try:
        assert myconfig().model_dump() == fastapi_plugins.get_config().model_dump()                                 # noqa E501
    finally:
        os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)


def test_wrap_register_config_test(plugin, myconfig):
    fastapi_plugins.register_config_test(myconfig)
    assert myconfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_TEST).model_dump()     # noqa E501
    os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_TEST                            # noqa E501
    try:
        assert myconfig().model_dump() == fastapi_plugins.get_config().model_dump()                                 # noqa E501
    finally:
        os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)


def test_wrap_register_config_by_name(plugin, myconfig, myconfig_name):
    fastapi_plugins.register_config(myconfig, name=myconfig_name)
    assert myconfig().model_dump() == fastapi_plugins.get_config(myconfig_name).model_dump()    # noqa E501


def test_wrap_get_config(plugin, myconfig):
    fastapi_plugins.register_config(myconfig)
    assert myconfig().model_dump() == fastapi_plugins.get_config().model_dump()


def test_wrap_get_config_by_name(plugin, myconfig, myconfig_name):
    fastapi_plugins.register_config(myconfig, name=myconfig_name)
    assert myconfig().model_dump() == fastapi_plugins.get_config(myconfig_name).model_dump()    # noqa E501


def test_wrap_reset_config(plugin, myconfig):
    from fastapi_plugins.settings import _manager
    assert _manager._settings_map == {}
    fastapi_plugins.register_config(myconfig)
    assert _manager._settings_map == {fastapi_plugins.CONFIG_NAME_DOCKER: myconfig} # noqa E501
    fastapi_plugins.reset_config()
    assert _manager._settings_map == {}


def test_decorator_register_config(plugin):
    @fastapi_plugins.registered_configuration
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    assert MyConfig().model_dump() == fastapi_plugins.get_config().model_dump()


def test_decorator_register_config_docker(plugin):
    @fastapi_plugins.registered_configuration_docker
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    # docker is default
    assert MyConfig().model_dump() == fastapi_plugins.get_config().model_dump()
    assert MyConfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_DOCKER).model_dump()   # noqa E501


def test_decorator_register_config_local(plugin):
    @fastapi_plugins.registered_configuration_local
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    assert MyConfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_LOCAL).model_dump()    # noqa E501
    os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_LOCAL                           # noqa E501
    try:
        assert MyConfig().model_dump() == fastapi_plugins.get_config().model_dump()                                 # noqa E501
    finally:
        os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)


def test_decorator_register_config_test(plugin):
    @fastapi_plugins.registered_configuration_test
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    assert MyConfig().model_dump() == fastapi_plugins.get_config(fastapi_plugins.CONFIG_NAME_TEST).model_dump() # noqa E501
    os.environ[fastapi_plugins.DEFAULT_CONFIG_ENVVAR] = fastapi_plugins.CONFIG_NAME_TEST                        # noqa E501
    try:
        assert MyConfig().model_dump() == fastapi_plugins.get_config().model_dump()                             # noqa E501
    finally:
        os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)


def test_decorator_register_config_by_name(plugin, myconfig_name):
    @fastapi_plugins.registered_configuration(name=myconfig_name)
    class MyConfig(fastapi_plugins.PluginSettings):
        api_name: str = 'API name'

    assert MyConfig().model_dump() == fastapi_plugins.get_config(myconfig_name).model_dump()    # noqa E501


async def test_app_config(plugin):
    @fastapi_plugins.registered_configuration
    class MyConfigDocker(fastapi_plugins.PluginSettings):
        api_name: str = 'docker'

    @fastapi_plugins.registered_configuration_local
    class MyConfigLocal(fastapi_plugins.PluginSettings):
        api_name: str = 'local'

    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    config = fastapi_plugins.get_config()
    await fastapi_plugins.config_plugin.init_app(app=app, config=config)
    await fastapi_plugins.config_plugin.init()
    try:
        assert MyConfigDocker().model_dump() == (await fastapi_plugins.config_plugin()).model_dump()    # noqa E501
    finally:
        await fastapi_plugins.config_plugin.terminate()
        fastapi_plugins.reset_config()


async def test_app_config_environ(plugin):
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
        await fastapi_plugins.config_plugin.init_app(app=app, config=config)
        await fastapi_plugins.config_plugin.init()
        try:
            assert MyConfigLocal().model_dump() == (await fastapi_plugins.config_plugin()).model_dump() # noqa E501
        finally:
            await fastapi_plugins.config_plugin.terminate()
    finally:
        os.environ.pop(fastapi_plugins.DEFAULT_CONFIG_ENVVAR)
