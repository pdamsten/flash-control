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

def writeJson(fname, json_data):
    with open(path(fname), 'w') as f:
        lib_json.dump(json_data, f, indent = 4, sort_keys = True)

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
        print(f"Error reading file {filename}: {str(e)}")
    return data

def convertDict(org, table, disable_key = None):
    def none(s):
        return s if s else ""
    
    def getv(d, key):
        keys = key.split('/')
        for k in keys[:-1]:
            if not k in d:
                return None
            d = d[k]
        if keys[-1] not in d:
            return None
        if disable_key and disable_key in d and d[disable_key]:
            return None
        return none(d[keys[-1]])

    def setv(key, v):
        keys = key.split('/')
        d = dest
        for i, k in enumerate(keys[:-1]):
            k = k if isinstance(d, dict) else int(k)
            if not k in d if isinstance(d, dict) else k >= len(d):
                if not (isinstance(v, str) and v.startswith('#')):
                    if isinstance(d, list):
                        k = int(k)
                        if k >= len(d):
                            d.extend([None] * (k - len(d) + 1))
                    if keys[i + 1].isdigit():
                        d[k] = []
                    else:
                        d[k] = {}
                else:
                    return
            d = d[k]
        k = keys[-1] if isinstance(d, dict) else int(keys[-1])
        d[k] = v[1:] if isinstance(v, str) and v.startswith('#') else v

    dest = [] if table[0][0].startswith('{index}/') else {}
    data = {}
    for i, group in enumerate([chr(ch + ord('A')) for ch in range(12)]):
        data['group'] = group
        data['index'] = i
        for dest_key, org_key in table:
            org_key = org_key.format(**data)
            dest_key = dest_key.format(**data)
            invert = False
            if org_key.startswith('!'):
                org_key = org_key[1:]
                invert = True
            v = org_key if org_key.startswith('#') else getv(org, org_key)
            v = v if v is None or not invert else not v
            if v is not None:
                setv(dest_key, v)
    print(dest)
    return dest