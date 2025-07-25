#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.logger

from __future__ import absolute_import

import datetime
import enum
import logging
import logging.handlers
import numbers
import queue
import sys
import typing

import fastapi
import pydantic_settings
import starlette.requests
from pythonjsonlogger import jsonlogger, orjson

from .control import ControlHealthMixin
from .plugin import Plugin, PluginError, PluginSettings
from .utils import Annotated

__all__ = [
    'LoggingError', 'LoggingStyle', 'LoggingHandlerType', 'LoggingSettings',
    'LoggingPlugin', 'log_plugin', 'log_adapter', 'depends_logging',
    'TLoggerPlugin'
]


class QueueHandler(logging.Handler):
    def __init__(self, *args, mqueue=None, **kwargs):
        super(QueueHandler, self).__init__(*args, **kwargs)
        self.mqueue = mqueue if mqueue is not None else queue.Queue()

    def emit(self, record):
        self.mqueue.put(self.format(record))


class _Formatter:
    def _add_more_fields(self, log_record, record, message_dict) -> None:   # noqa
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now

        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        if not log_record.get('name'):
            log_record['name'] = record.name


class JsonFormatter(jsonlogger.JsonFormatter, _Formatter):
    def add_fields(self, log_record, record, message_dict) -> None:
        super().add_fields(log_record, record, message_dict)
        self._add_more_fields(log_record, record, message_dict)


class OrJsonFormatter(orjson.OrjsonFormatter, _Formatter):
    def add_fields(self, log_record, record, message_dict) -> None:
        super().add_fields(log_record, record, message_dict)
        self._add_more_fields(log_record, record, message_dict)


class LogfmtFormatter(logging.Formatter):
    # from https://github.com/jkakar/logfmt-python
    def format_line(self, extra: typing.Dict) -> str:
        outarr = []
        for k, v in extra.items():
            if v is None:
                outarr.append(f'{k}=')
                continue
            if isinstance(v, bool):
                v = 'true' if v else 'false'
            elif isinstance(v, numbers.Number):
                pass
            else:
                if isinstance(v, (dict, object)):
                    v = str(v)
                v = '"%s"' % v.replace('"', '\\"')
            outarr.append(f'{k}={v}')
        return ' '.join(outarr)

    def format(self, record):
        return ' '.join(
            [
                f'at={record.levelname}',
                'msg="%s"' % record.getMessage().replace('"', '\\"'),
                f'process={record.processName}',
                self.format_line(getattr(record, 'context', {})),
            ]
        ).strip()


class LoggerLogfmt(logging.Logger):
    def makeRecord(
            self,
            name,
            level,
            fn,
            lno,
            msg,
            args,
            exc_info,
            func=None,
            extra=None,
            sinfo=None
    ):
        factory = logging.getLogRecordFactory()
        rv = factory(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            rv.__dict__['context'] = dict(**extra)
        return rv


class LoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        _extra = kwargs.get('extra', {})
        kwargs["extra"] = dict(**self.extra)
        kwargs["extra"].update(**_extra)
        return msg, kwargs


class LoggingError(PluginError):
    pass


@enum.unique
class LoggingStyle(str, enum.Enum):
    logfmt = 'logfmt'
    logjson = 'json'
    logorjson = 'orjson'
    logtxt = 'txt'


@enum.unique
class LoggingHandlerType(str, enum.Enum):
    loglist = 'list'
    logstdout = 'stdout'


class LoggingSettings(PluginSettings):
    logging_level: int = logging.WARNING
    logging_style: LoggingStyle = LoggingStyle.logtxt
    logging_handler: LoggingHandlerType = LoggingHandlerType.logstdout
    logging_fmt: typing.Optional[str] = None
    logging_memory_capacity: int = 0    # 1024*100
    logging_memory_flush_level: int = logging.ERROR


class LoggingPlugin(Plugin, ControlHealthMixin):
    DEFAULT_CONFIG_CLASS: pydantic_settings.BaseSettings = LoggingSettings

    def _create_logger(
            self,
            name: str,
            config: pydantic_settings.BaseSettings=None
    ) -> logging.Logger:
        handler = QueueHandler()
        formatter = logging.Formatter(fmt=config.logging_fmt)
        klass = None

        #
        # style
        if config.logging_style == LoggingStyle.logtxt:
            pass
        elif config.logging_style == LoggingStyle.logfmt:
            formatter = LogfmtFormatter()
            klass = LoggerLogfmt
        elif config.logging_style == LoggingStyle.logjson:
            formatter = JsonFormatter()
        elif config.logging_style == LoggingStyle.logorjson:
            formatter = OrJsonFormatter()
        else:
            raise LoggingError(f'unknown logging format style {config.logging_style}')

        #
        # handler type
        if config.logging_handler == LoggingHandlerType.loglist:
            pass
        elif config.logging_handler == LoggingHandlerType.logstdout:
            handler = logging.StreamHandler(stream=sys.stdout)
        else:
            raise LoggingError(f'unknown logging handler {config.logging_handler}')

        #
        # setup handler
        handler.setLevel(config.logging_level)
        handler.setFormatter(formatter)

        #
        # memory
        if config.logging_memory_capacity > 0:
            handler = logging.handlers.MemoryHandler(
                capacity=config.logging_memory_capacity,
                flushLevel=config.logging_memory_flush_level,
                target=handler
            )

        #
        # default logging class
        if klass is not None:
            _original_logger_klass = logging.getLoggerClass()
            try:
                logging.setLoggerClass(klass)
                logger = logging.getLogger(name)
            finally:
                logging.setLoggerClass(_original_logger_klass)
        else:
            logger = logging.getLogger(name)

        #
        # setup logger
        logger.setLevel(config.logging_level)
        logger.addHandler(handler)

        return logger

    def _on_init(self) -> None:
        self.config = None
        self.logger = None

    async def _on_call(self) -> logging.Logger:
        if self.logger is None:
            raise LoggingError('Logging is not initialized')
        return self.logger

    async def init_app(
            self,
            app: fastapi.FastAPI,
            config: pydantic_settings.BaseSettings=None,
            *,
            name: str=None
    ) -> None:
        self.config = config or self.DEFAULT_CONFIG_CLASS()
        if self.config is None:
            raise LoggingError('Logging configuration is not initialized')
        elif not isinstance(self.config, self.DEFAULT_CONFIG_CLASS):
            raise LoggingError('Logging configuration is not valid')
        name = name if name else __name__.split('.')[0]
        self.logger = self._create_logger(name, self.config)
        app.state.PLUGIN_LOGGER = self

    async def init(self) -> None:
        self.logger.info('Logging plugin is ON')

    async def terminate(self) -> None:
        self.logger.info('Logging plugin is OFF')
        self.config = None
        self.logger = None

    async def health(self) -> typing.Dict:
        return dict(level=self.logger.level, style=self.config.logging_style)


log_plugin = LoggingPlugin()


async def log_adapter(
    logger: typing.Union[logging.Logger, LoggerAdapter],
    extra: typing.Dict=None
) -> LoggerAdapter:
    if extra is None:
        extra = {}
    if isinstance(logger, logging.Logger):
        return LoggerAdapter(logger, extra)
    else:
        _extra = dict(**logger.extra)
        _extra.update(**extra)
        return LoggerAdapter(logger.logger, _extra)


async def depends_logging(
    conn: starlette.requests.HTTPConnection
) -> logging.Logger:
    return await conn.app.state.PLUGIN_LOGGER()


TLoggerPlugin = Annotated[logging.Logger, fastapi.Depends(depends_logging)]
