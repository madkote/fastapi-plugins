#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.__init__
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2019, madkote

fastapi_plugins
---------------
FastAPI plugins

# TODO: xxx tests with docker
'''

from __future__ import absolute_import

from .plugin import *  # noqa F401 F403
from .version import VERSION

# TODO: xxx
# try:
#     import aioredis  # noqa F401
# except ImportError:
#     import warnings
#     warnings.warn(
#         'The `aioredis` library has not been installed. '
#         'Functionality from the `redis` package will not be available.'
#     )
# else:
#     from ._redis import *  # noqa F401 F403

# TODO: xxx
# try:
#     import aiojobs  # noqa F401
# except ImportError:
#     import warnings
#     warnings.warn(
#         'The `aiojobs` library has not been installed. '
#         'Functionality from the `scheduler` package will not be available.'
#     )
# else:
#     from .scheduler import *  # noqa F401 F403

from ._redis import *  # noqa F401 F403
from .scheduler import *  # noqa F401 F403

__all__ = []
__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2019, madkote'


# TODO: health
# TODO: databases
# TODO: mq - activemq, rabbitmq, kafka
# TODO: celery
# TODO: logging - simple? or more complex example? -> will decide later
# ... more?
