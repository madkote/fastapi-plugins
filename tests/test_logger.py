#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_logger
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote

tests.test_logger
-----------------
Logger tests
'''

from __future__ import absolute_import

import asyncio
import copy
import json
import inspect
import logging
import unittest

import fastapi
import pytest

import fastapi_plugins

from . import VERSION

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote'


@pytest.mark.logger
class LoggerTest(unittest.TestCase):
    def test_basic(self):
        async def _test():
            level = logging.WARNING
            name = 'fastapi_plugins'
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings()
            await fastapi_plugins.log_plugin.init_app(app=app, config=config)
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_name_and_level(self):
        name = 'fastapi_plugins_%s' % inspect.stack()[0][3]

        async def _test():
            level = logging.CRITICAL
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings(logging_level=level)
            await fastapi_plugins.log_plugin.init_app(
                app=app,
                config=config,
                name=name
            )
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_format_default(self):
        name = 'fastapi_plugins_%s' % inspect.stack()[0][3]

        async def _test():
            level = logging.DEBUG
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings(
                logging_level=level,
                logging_style=fastapi_plugins.LoggingStyle.logtxt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            )
            await fastapi_plugins.log_plugin.init_app(
                app=app,
                config=config,
                name=name
            )
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                #
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
                #
                logger.debug('Hello')
                logger.info('World', extra=dict(planet='earth'))
                logger.warning('Echo', extra=dict(planet='earth', satellite=['moon']))  # noqa E501
                #
                h = logger.handlers[0]
                res = [r for r in h.mqueue.queue][1:]
                exp = ['Hello', 'World', 'Echo']
                try:
                    self.assertTrue(exp == res, 'different logs')
                except Exception as e:
                    print()
                    print('---- expected ------')
                    print(exp)
                    print('--------------------')
                    print()
                    print('---- records ------')
                    print(res)
                    print('--------------------')
                    print()
                    raise e
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_format_json(self):
        name = 'fastapi_plugins_%s' % inspect.stack()[0][3]

        async def _test():
            def _preproc_exp(_r):
                _res = []
                for x in _r:
                    x1 = copy.deepcopy(x)
                    x1.pop('timestamp')
                    _res.append(x1)
                return _res

            def _preproc_res(_r):
                _res = []
                for x in _r:
                    x1 = json.loads(x)
                    x1.pop('timestamp')
                    _res.append(x1)
                return _res

            level = logging.DEBUG
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings(
                logging_level=level,
                logging_style=fastapi_plugins.LoggingStyle.logjson,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            )
            await fastapi_plugins.log_plugin.init_app(
                app=app,
                config=config,
                name=name
            )
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                #
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
                #
                logger.debug('Hello')
                logger.info('World', extra=dict(planet='earth'))
                logger.warning('Echo', extra=dict(planet='earth', satellite=['moon']))  # noqa E501
                #
                h = logger.handlers[0]
                res = [r for r in h.mqueue.queue][1:]
                res = _preproc_res(res)
                exp = [
                    {"message": "Hello", "timestamp": "2021-09-23T13:44:01.066467Z", "level": "DEBUG", "name": name},                                           # noqa E501
                    {"message": "World", "planet": "earth", "timestamp": "2021-09-23T13:44:01.066581Z", "level": "INFO", "name": name},                         # noqa E501
                    {"message": "Echo", "planet": "earth", "satellite": ["moon"], "timestamp": "2021-09-23T13:44:01.066690Z", "level": "WARNING", "name": name} # noqa E501
                ]
                exp = _preproc_exp(exp)
                try:
                    self.assertTrue(exp == res, 'different logs')
                except Exception as e:
                    print()
                    print('---- expected ------')
                    print(exp)
                    print('--------------------')
                    print()
                    print('---- records ------')
                    print(res)
                    print('--------------------')
                    print()
                    raise e
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_format_logfmt(self):
        name = 'fastapi_plugins_%s' % inspect.stack()[0][3]

        async def _test():
            level = logging.DEBUG
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings(
                logging_level=level,
                logging_style=fastapi_plugins.LoggingStyle.logfmt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            )
            await fastapi_plugins.log_plugin.init_app(
                app=app,
                config=config,
                name=name
            )
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                #
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
                #
                logger.debug('Hello')
                logger.info('World', extra=dict(planet='earth'))
                logger.warning('Echo', extra=dict(planet='earth', satellite=['moon']))  # noqa E501
                #
                h = logger.handlers[0]
                res = [r for r in h.mqueue.queue][1:]
                exp = [
                    'at=DEBUG msg="Hello" process=MainProcess',
                    'at=INFO msg="World" process=MainProcess planet="earth"',
                    'at=WARNING msg="Echo" process=MainProcess planet="earth" satellite="[\'moon\']"'   # noqa E501
                ]
                try:
                    self.assertTrue(exp == res, 'different logs')
                except Exception as e:
                    print()
                    print('---- expected ------')
                    print(exp)
                    print('--------------------')
                    print()
                    print('---- records ------')
                    print(res)
                    print('--------------------')
                    print()
                    raise e
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()

    def test_adapter(self):
        name = 'fastapi_plugins_%s' % inspect.stack()[0][3]

        async def _test():
            def _preproc_exp(_r):
                _res = []
                for x in _r:
                    x1 = copy.deepcopy(x)
                    x1.pop('timestamp')
                    _res.append(x1)
                return _res

            def _preproc_res(_r):
                _res = []
                for x in _r:
                    x1 = json.loads(x)
                    x1.pop('timestamp')
                    _res.append(x1)
                return _res

            level = logging.DEBUG
            #
            app = fastapi_plugins.register_middleware(fastapi.FastAPI())
            config = fastapi_plugins.LoggingSettings(
                logging_level=level,
                logging_style=fastapi_plugins.LoggingStyle.logjson,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            )
            await fastapi_plugins.log_plugin.init_app(
                app=app,
                config=config,
                name=name
            )
            await fastapi_plugins.log_plugin.init()
            try:
                logger = await fastapi_plugins.log_plugin()
                #
                exp = name
                res = logger.name
                self.assertTrue(
                    exp == res,
                    'logging name mismatch %s != %s' % (exp, res)
                )
                exp = level
                res = logger.level
                self.assertTrue(
                    exp == res,
                    'logging level mismatch %s != %s' % (exp, res)
                )
                #
                logger.debug('Hello')
                logger = await fastapi_plugins.log_adapter(logger, extra=dict(planet='earth'))      # noqa E501
                logger.info('World')
                logger = await fastapi_plugins.log_adapter(logger, extra=dict(satellite=['moon']))  # noqa E501
                logger.warning('Echo')
                #
                h = logger.logger.handlers[0]
                res = [r for r in h.mqueue.queue][1:]
                res = _preproc_res(res)
                exp = [
                    {"message": "Hello", "timestamp": "2021-09-23T13:44:01.066467Z", "level": "DEBUG", "name": name},                                           # noqa E501
                    {"message": "World", "planet": "earth", "timestamp": "2021-09-23T13:44:01.066581Z", "level": "INFO", "name": name},                         # noqa E501
                    {"message": "Echo", "planet": "earth", "satellite": ["moon"], "timestamp": "2021-09-23T13:44:01.066690Z", "level": "WARNING", "name": name} # noqa E501
                ]
                exp = _preproc_exp(exp)
                try:
                    self.assertTrue(exp == res, 'different logs')
                except Exception as e:
                    print()
                    print('---- expected ------')
                    print(exp)
                    print('--------------------')
                    print()
                    print('---- records ------')
                    print(res)
                    print('--------------------')
                    print()
                    raise e
            finally:
                await fastapi_plugins.log_plugin.terminate()

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(_test())
        event_loop.close()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
