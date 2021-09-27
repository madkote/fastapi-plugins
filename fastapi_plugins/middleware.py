#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.middleware
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2021, madkote RES

fastapi_plugins.middleware
--------------------------
Middleware utilities and collections
'''

from __future__ import absolute_import

import typing

import fastapi
import starlette.middleware.cors

from .version import VERSION

__all__ = ['register_middleware']
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2021, madkote RES'


def register_middleware(
        app: fastapi.FastAPI,
        middleware: typing.List[typing.Tuple[type, typing.Any]]=None
) -> fastapi.FastAPI:
    if not middleware:
        middleware = [
            (
                starlette.middleware.cors.CORSMiddleware,
                dict(
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"]
                )
            )
        ]
    for mw_klass, options in middleware:
        app.add_middleware(mw_klass, **options)
    return app
