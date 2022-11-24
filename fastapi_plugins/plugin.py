#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.plugin

from __future__ import absolute_import

import abc
import typing

import fastapi
import pydantic


class PluginError(Exception):
    pass


class PluginSettings(pydantic.BaseSettings):
    class Config:
        env_prefix = ''
        use_enum_values = True


class Plugin:
    DEFAULT_CONFIG_CLASS: pydantic.BaseSettings = None

    def __init__(
            self,
            app: fastapi.FastAPI=None,
            config: pydantic.BaseSettings=None
    ):
        self._on_init()
        if app and config:
            self.init_app(app, config)

    def __call__(self) -> typing.Any:
        return self._on_call()

    def _on_init(self) -> None:
        pass

#     def is_initialized(self) -> bool:
#         raise NotImplementedError('implement is_initialied()')

    @abc.abstractmethod
    async def _on_call(self) -> typing.Any:
        raise NotImplementedError('implement _on_call()')

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic.BaseSettings=None,
            *args,
            **kwargs
    ) -> None:
        pass

    async def init(self):
        pass

    async def terminate(self):
        pass
