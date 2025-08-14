#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#**************************************************************************
#
#   Copyright (c) 2025 by Petri Damstén <petri.damsten@gmail.com> 
#                         https://petridamsten.com
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#**************************************************************************

import logging
import json
import sys

import lib.util as util

LOGFILE = util.path('user/flash-control.log')
FORMAT = '%(asctime)s.%(msecs)03d %(levelname)s %(module)s::%(funcName)s - %(message)s'
DATETIME = '%Y-%m-%d %H:%M:%S'
_level = logging.DEBUG
_file_output = False
    
def setHandler():
    logger.handlers.clear()
    if _file_output:
        handler = logging.FileHandler(LOGFILE, mode = 'a')
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_level)
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def setParams(fileOutput = False, level = logging.DEBUG):
    global _file_output, _level

    _file_output = fileOutput
    _level = level
    setHandler()

def format_msg(msg):
    if isinstance(msg, dict):
        return json.dumps(msg, sort_keys = True, indent = 4)
    return msg

def INFO(msg, *args, **kwargs):
    kwargs.setdefault("stacklevel", 2)
    logger.info(format_msg(msg), *args, **kwargs)

def DEBUG(msg, *args, **kwargs):
    kwargs.setdefault("stacklevel", 2)
    logger.debug(format_msg(msg), *args, **kwargs)

def EXCEPTION(msg, *args, **kwargs):
    kwargs.setdefault("stacklevel", 2)
    logger.exception(format_msg(msg), *args, **kwargs)

def ERROR(msg, *args, **kwargs):
    kwargs.setdefault("stacklevel", 2)
    logger.error(format_msg(msg), *args, **kwargs)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
setHandler()