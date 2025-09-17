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
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import lib.exiftool as exiftool
import lib.util as util
from threading import Lock

PREFIX =         "XMP:XMP-pdplus:"
STAND =          PREFIX + "Stand"
TETHERING =      PREFIX + "Tethering"
TRIGGER =        PREFIX + "Trigger"
FILTER =         PREFIX + "Filter"
EXTENSION_TUBE = PREFIX + "ExtensionTube"
REMOTE =         PREFIX + "Remote"
EXPOSURES =      PREFIX + "Exposures"
FLASHES =        PREFIX + "Flashes"
ID =             "Id"
ROLE =           "Role"
NAME =           "Name"
MODIFIER =       "Modifier"
ACCESSORY =      "Accessory"
POWER =          "Power"
GEL =            "Gel"
MODE =           "Mode"

class RAWEventHandler(PatternMatchingEventHandler):
    def __init__(self, watcher, pattern):
        super(RAWEventHandler, self).__init__(    
            patterns = pattern.split(';'),
            ignore_patterns = [],
            ignore_directories = True
        )
        self.watcher = watcher
        
    def on_created(self, event):
        flash_info = os.path.splitext(event.src_path)[0] + '.json'
        xmp = os.path.splitext(event.src_path)[0] + '.xmp'
        util.writeJson(flash_info, self.watcher.json)
        msg = exiftool.write(xmp, flash_info)
        if not msg:
            msg = (f'Metadata added: {os.path.basename(event.src_path)}', 0)
        else:
            msg = (f'Metadata FAILED: {os.path.basename(event.src_path)}', 1)
        self.watcher.msg(msg)

class RAWWatcher:
    def __init__(self):
        self.observer = None
        self.lock = Lock()
        self.callbacks = {}

    def callback(self, name, callback):
        self.callbacks[name] = callback

    def msg(self, s):
        if 'msg' in self.callbacks:
            self.callbacks['msg'](s)

    def start(self, folder, pattern):
        self.observer = Observer()
        event_handler = RAWEventHandler(self, pattern)
        self.observer.schedule(event_handler, folder, recursive = True)
        self.observer.start()
    
    def stop(self):
        self.observer.stop()
        self.observer.join()

    def json(self):
        with self.lock:
            j = self.json
        return j

    def setJson(self, json):
        with self.lock:
            self.json = json
