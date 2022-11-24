#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.middleware

from __future__ import absolute_import

import typing

import fastapi
import starlette.middleware.cors


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
