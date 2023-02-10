#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.test_logger

from __future__ import absolute_import

import json
import logging

import fastapi
import pytest

import fastapi_plugins


pytestmark = [pytest.mark.anyio, pytest.mark.logger]


@pytest.fixture(params=None)
async def logapp(request):
    app = fastapi_plugins.register_middleware(fastapi.FastAPI())
    await fastapi_plugins.log_plugin.init_app(
        app=app,
        config=request.param or fastapi_plugins.LoggingSettings(),
        name=request.node.name
    )
    await fastapi_plugins.log_plugin.init()
    yield app
    await fastapi_plugins.log_plugin.terminate()


@pytest.fixture
async def logapp_name(request):
    return request.node.name


@pytest.mark.parametrize(
    'logapp, level',
    [
        pytest.param(None, logging.WARNING),
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.CRITICAL
            ),
            logging.CRITICAL
        ),
    ],
    indirect=['logapp']
)
async def test_basic(logapp, level, logapp_name):
    logger = await fastapi_plugins.log_plugin()
    assert logapp_name == logger.name
    assert level == logger.level


@pytest.mark.parametrize(
    'logapp, level, result',
    [
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logtxt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            ['Hello', 'World', 'Echo']
        ),
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logjson,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            [
                {"message": "Hello", "level": "DEBUG"},
                {"message": "World", "planet": "earth", "level": "INFO"},
                {"message": "Echo", "planet": "earth", "satellite": ["moon"], "level": "WARNING"}   # noqa E501
            ]
        ),
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logfmt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            [
                'at=DEBUG msg="Hello" process=MainProcess',
                'at=INFO msg="World" process=MainProcess planet="earth"',
                'at=WARNING msg="Echo" process=MainProcess planet="earth" satellite="[\'moon\']"'   # noqa E501
            ]
        ),
    ],
    indirect=['logapp']
)
async def test_format(logapp, level, result, logapp_name):
    def _preproc(_results):
        def _inner(__results):
            for r in __results:
                try:
                    rr = json.loads(r)
                    rr.pop('timestamp')
                    rr.pop('name')
                    yield rr
                except json.decoder.JSONDecodeError:
                    yield r
        return list(_inner(_results))

    logger = await fastapi_plugins.log_plugin()
    assert logapp_name == logger.name
    assert level == logger.level
    #
    logger.debug('Hello')
    logger.info('World', extra=dict(planet='earth'))
    logger.warning('Echo', extra=dict(planet='earth', satellite=['moon']))
    h = logger.handlers[0]
    assert result == _preproc([r for r in h.mqueue.queue][1:])


@pytest.mark.parametrize(
    'logapp, level, result',
    [
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logtxt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            ['Hello', 'World', 'Echo']
        ),
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logjson,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            [
                {"message": "Hello", "level": "DEBUG"},
                {"message": "World", "planet": "earth", "level": "INFO"},
                {"message": "Echo", "planet": "earth", "satellite": ["moon"], "level": "WARNING"}   # noqa E501
            ]
        ),
        pytest.param(
            fastapi_plugins.LoggingSettings(
                logging_level=logging.DEBUG,
                logging_style=fastapi_plugins.LoggingStyle.logfmt,
                logging_handler=fastapi_plugins.LoggingHandlerType.loglist
            ),
            logging.DEBUG,
            [
                'at=DEBUG msg="Hello" process=MainProcess',
                'at=INFO msg="World" process=MainProcess planet="earth"',
                'at=WARNING msg="Echo" process=MainProcess planet="earth" satellite="[\'moon\']"'   # noqa E501
            ]
        ),
    ],
    indirect=['logapp']
)
async def test_format_adapter(logapp, level, result, logapp_name):
    def _preproc(_results):
        def _inner(__results):
            for r in __results:
                try:
                    rr = json.loads(r)
                    rr.pop('timestamp')
                    rr.pop('name')
                    yield rr
                except json.decoder.JSONDecodeError:
                    yield r
        return list(_inner(_results))

    logger = await fastapi_plugins.log_plugin()
    assert logapp_name == logger.name
    assert level == logger.level
    #
    logger.debug('Hello')
    logger = await fastapi_plugins.log_adapter(logger, extra=dict(planet='earth'))      # noqa E501
    logger.info('World')
    logger = await fastapi_plugins.log_adapter(logger, extra=dict(satellite=['moon']))  # noqa E501
    logger.warning('Echo')
    h = logger.logger.handlers[0]
    assert result == _preproc([r for r in h.mqueue.queue][1:])
