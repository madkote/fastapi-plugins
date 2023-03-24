#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.settings

from __future__ import absolute_import

import functools
import typing

import fastapi
import pydantic
import starlette.config

from .plugin import PluginError
from .plugin import Plugin
from .utils import Annotated
from .version import VERSION

__all__ = [
    'ConfigError', 'ConfigPlugin', 'depends_config', 'config_plugin',
    'TConfigPlugin',
    #
    'register_config',
    'register_config_docker', 'register_config_local', 'register_config_test',
    # 'register_config_by_name',
    'reset_config', 'get_config',
    #
    'registered_configuration', 'registered_configuration_docker',
    'registered_configuration_local', 'registered_configuration_test',
    # 'registered_configuration_by_name',
    #
    'DEFAULT_CONFIG_ENVVAR', 'DEFAULT_CONFIG_NAME',
    'CONFIG_NAME_DEFAULT', 'CONFIG_NAME_DOCKER', 'CONFIG_NAME_LOCAL',
    'CONFIG_NAME_TEST',
]
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'

DEFAULT_CONFIG_ENVVAR: str = 'CONFIG_NAME'
DEFAULT_CONFIG_NAME: str = 'docker'

CONFIG_NAME_DEFAULT = DEFAULT_CONFIG_NAME
CONFIG_NAME_DOCKER = DEFAULT_CONFIG_NAME
CONFIG_NAME_LOCAL = 'local'
CONFIG_NAME_TEST = 'test'


class ConfigError(PluginError):
    pass


class ConfigManager(object):
    def __init__(self):
        self._settings_map = {}

    def register(self, name: str, config: pydantic.BaseSettings) -> None:
        self._settings_map[name] = config

    def reset(self) -> None:
        self._settings_map.clear()

    def get_config(
            self,
            config_or_name: typing.Union[str, pydantic.BaseSettings]=None,
            config_name_default: str=DEFAULT_CONFIG_NAME,
            config_name_envvar: str=DEFAULT_CONFIG_ENVVAR
    ) -> pydantic.BaseSettings:
        if isinstance(config_or_name, pydantic.BaseSettings):
            return config_or_name
        if not config_or_name:
            config_or_name = config_name_default
        base_cfg = starlette.config.Config()
        config_or_name = base_cfg(
            config_name_envvar,
            cast=str,
            default=config_or_name
        )
        if config_or_name not in self._settings_map:
            raise ConfigError('Unknown configuration "%s"' % config_or_name)
        return self._settings_map[config_or_name]()


_manager = ConfigManager()


def register_config(config: pydantic.BaseSettings, name: str=None) -> None:
    if not name:
        name = CONFIG_NAME_DEFAULT
    _manager.register(name, config)


def register_config_docker(config: pydantic.BaseSettings) -> None:
    _manager.register(CONFIG_NAME_DOCKER, config)


def register_config_local(config: pydantic.BaseSettings) -> None:
    _manager.register(CONFIG_NAME_LOCAL, config)


def register_config_test(config: pydantic.BaseSettings) -> None:
    _manager.register(CONFIG_NAME_TEST, config)


# def registered_configuration(cls=None, /, *, name: str=None):
def registered_configuration(cls=None, *, name: str=None):
    if not name:
        name = CONFIG_NAME_DEFAULT

    def wrap(kls):
        _manager.register(name, kls)
        return kls

    if cls is None:
        return wrap
    return wrap(cls)


def registered_configuration_docker(cls=None):
    def wrap(kls):
        _manager.register(CONFIG_NAME_DOCKER, kls)
        return kls
    if cls is None:
        return wrap
    return wrap(cls)


def registered_configuration_local(cls=None):
    def wrap(kls):
        _manager.register(CONFIG_NAME_LOCAL, kls)
        return kls
    if cls is None:
        return wrap
    return wrap(cls)


def registered_configuration_test(cls=None):
    def wrap(kls):
        _manager.register(CONFIG_NAME_TEST, kls)
        return kls
    if cls is None:
        return wrap
    return wrap(cls)


def reset_config() -> None:
    _manager.reset()


@functools.lru_cache()
def get_config(
        config_or_name: typing.Union[str, pydantic.BaseSettings]=None,
        config_name_default: str=DEFAULT_CONFIG_NAME,
        config_name_envvar: str=DEFAULT_CONFIG_ENVVAR
) -> pydantic.BaseSettings:
    return _manager.get_config(
        config_or_name=config_or_name,
        config_name_default=config_name_default,
        config_name_envvar=config_name_envvar
    )


class ConfigPlugin(Plugin):
    DEFAULT_CONFIG_CLASS = pydantic.BaseSettings

    async def _on_call(self) -> pydantic.BaseSettings:
        return self.config

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None,
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        app.state.PLUGIN_CONFIG = self


config_plugin = ConfigPlugin()


async def depends_config(
    conn: starlette.requests.HTTPConnection
) -> pydantic.BaseSettings:
    return await conn.app.state.PLUGIN_CONFIG()


TConfigPlugin = Annotated[pydantic.BaseSettings, fastapi.Depends(depends_config)]   # noqa E501
