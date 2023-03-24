#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fastapi_plugins.__init__
'''
:author:    madkote
:contact:   madkote(at)bluewin.ch
:copyright: Copyright 2023, madkote

fastapi_plugins
---------------
FastAPI plugins
'''

from __future__ import absolute_import

from .plugin import *           # noqa F401 F403
from .control import *          # noqa F401 F403
from .logger import *           # noqa F401 F403
from .middleware import *       # noqa F401 F403
from ._redis import *           # noqa F401 F403
from .scheduler import *        # noqa F401 F403
from .settings import *         # noqa F401 F403
from .version import VERSION

# try:
#     import aioredis  # noqa F401
# except ImportError:
#     pass
# else:
#     from ._redis import *  # noqa F401 F403
#
# try:
#     import aiojobs  # noqa F401
# except ImportError:
#     pass
# else:
#     from .scheduler import *  # noqa F401 F403

__author__ = 'madkote <madkote(at)bluewin.ch>'
__version__ = '.'.join(str(x) for x in VERSION)
__copyright__ = 'Copyright 2023, madkote'

# TODO: provide a generic cache type (redis, memcached, in-memory)
#       and share some settings. Module/Sub-Pack cache

# TODO: databases

# TODO: mq - activemq, rabbitmq, kafka
#   -> publish(topic, message, headers)
#   -> consume(topic, callback)

# TODO: celery

# TODO: look at fastapi-cache (memcache?) look at mqtt?

# ... more?
