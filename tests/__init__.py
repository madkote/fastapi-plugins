#!/usr/bin/env python
# -*- coding: utf-8 -*-
# tests.__init__

import json


def d2json(d):
    return json.dumps(d, sort_keys=True)
