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

import os 
import inspect
from pathlib import Path
import json as lib_json

MAIN_PATH  = os.path.dirname(os.path.abspath(inspect.stack()[-1].filename))

def isPath(path):
    path = os.path.dirname(path)
    p = Path(path)
    return p.exists()

def path(filename = ''):
    if os.path.isabs(filename):
        return filename
    return MAIN_PATH + '/' + filename

# needs that path func initialized
from lib.logger import INFO, ERROR, EXCEPTION, DEBUG

def writeJson(fname, json_data):
    with open(path(fname), 'w') as f:
        lib_json.dump(json_data, f, indent = 4)

def json(filename):
    data = {}
    try:
        with open(path(filename), 'r') as f:
            data = lib_json.load(f)
    except:
        pass
    return data

def stringList(filename):
    data = []
    try:
        with open(path(filename), 'r') as f:
            data = f.read().strip().splitlines()
    except Exception as e:
        print(f"Error reading file {filename}")
    return data
