#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.utils

from __future__ import absolute_import

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated                                    # noqa
else:
    from typing_extensions import Annotated                         # noqa
