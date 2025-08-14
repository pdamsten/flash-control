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

import subprocess
import lib.util as util
import json
import tempfile
from lib.logger import INFO, ERROR, EXCEPTION, DEBUG

def write(fname, data):
    if isinstance(data, dict):
        tmp = tempfile.NamedTemporaryFile(mode = 'w', delete = False)
        DEBUG(f"Temp file path: {tmp.name}")
        tmp.write(json.dumps(data))
        tmp.close()
        data = tmp.name

    cmd = [
        "exiftool",
        "-config", util.path('lib/exiftool-custom-ns.config'),
        "-d", "%Y:%m:%d %H:%M:%S",
        "-G0:1",
        "-n",
        "-overwrite_original_in_place",
        f"-json={data}",
        fname
    ]
    result = subprocess.run(cmd, capture_output = True, text = True)
    if result.returncode != 0:
        return f"Exiftool failed: {result.stderr.strip()}"
    return None

def read(fname):
    cmd = [
        "exiftool",
        "-config", util.path('lib/exiftool-custom-ns.config'),
        "-d", "%Y:%m:%d %H:%M:%S",
        "-G0:1",
        "-n",
        "-struct",
        "-json",
        fname
    ]
    result = subprocess.run(cmd, capture_output = True, text = True)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout.strip())[0]
        return data
    except Exception as e:
        EXCEPTION("Error parsing JSON.")
        return None

