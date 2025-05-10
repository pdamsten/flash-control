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

import webview
import sys
import os
from pathlib import Path
import inspect
import json

def isPath(path):
    p = Path(path)
    return p.exists()

TEST_ICON = os.path.expanduser('~/src/digikam-sc/project/macosx/Icons.icns')
CONFIG = 'user/config.json'

try:
    if sys.platform.startswith('darwin'):
        import AppKit
        from PyObjCTools import AppHelper
except ImportError:
    print('You must have PyObjC to run this on macos')
    sys.exit(1)

class HTMLMainWindow():
    instances = []
    program_path = os.path.dirname(os.path.abspath(inspect.stack()[-1].filename))

    def on_closing(self):
        print('Window closed')
        self.window.events.closing -= self.on_closing
        HTMLMainWindow.instances.remove(self)
        self.window.destroy()
        if not HTMLMainWindow.instances:
            print('All windows closed, exiting')
            with open(self.path(CONFIG), 'w') as f:
                json.dump(self.config, f)
            sys.exit(0)

    def on_resized(self, width, height):
        self.config['width'] = width
        self.config['height'] = height

    def on_moved(self, x, y):
        self.config['x'] = x
        self.config['y'] = y - 25
    
    def json(self, filename):
        data = {}
        try:
            with open(self.path(filename), 'r') as f:
                data = json.load(f)
        except:
            pass
        return data

    def slist(self, filename):
        data = []
        try:
            with open(self.path(filename), 'r') as f:
                data = f.read().strip().splitlines()
        except Exception as e:
            print(f"Error reading file {filename}: {str(e)}")
            pass
        return data

    def cv(self, key, default = None):
        if not key in self.config:
            self.config[key] = default
        return self.config[key]

    @staticmethod
    def path(filename):
        return HTMLMainWindow.program_path + '/' + filename
    
    def __init__(self, title, html, css = None, api = None):
        HTMLMainWindow.instances.append(self)

        self.setMacOsTitle(title)
        self.api = api
        self.css = css
        self.config = self.json(CONFIG)
        print (f'Config: {self.config}')
        hpath = html if isPath(html) else None
        html = html if not isPath(html) else None
        self.window = webview.create_window(title, hpath, html = html, 
                frameless = sys.platform.startswith('darwin'), js_api = api, 
                width = self.cv('width', 1000), height = self.cv('height', 800),
                x = self.cv('x'), y = self.cv('y'))
        self.window.events.closing += self.on_closing
        self.window.events.resized += self.on_resized
        self.window.events.moved += self.on_moved
        webview.start(self.init, self.window)

    def setMacOsTitle(self, name):
        if sys.platform.startswith('darwin'):
            try:
                from Foundation import NSBundle

                app = AppKit.NSApplication.sharedApplication()
                icon_image = AppKit.NSImage.alloc().initWithContentsOfFile_(TEST_ICON)
                if icon_image:
                    app.setApplicationIconImage_(icon_image)

                bundle = NSBundle.mainBundle()
                if bundle:
                    app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                    if app_info:
                        app_info['CFBundleName'] = name
                        # TODO
                        app_info['CFBundleVersion'] = '0.1'
                        app_info['CFBundleShortVersionString'] = '0.2'
                        app_info['NSHumanReadableCopyright'] = 'copyright'

            except ImportError:
                pass

    def showTrafficLights(self):
        def _showTL(window):
            w = window.gui.BrowserView.instances.get(window.uid).window
            w.standardWindowButton_(AppKit.NSWindowCloseButton).setHidden_(False)
            w.standardWindowButton_(AppKit.NSWindowMiniaturizeButton).setHidden_(False)
            w.standardWindowButton_(AppKit.NSWindowZoomButton).setHidden_(False)
        if sys.platform.startswith('darwin'):
            AppHelper.callAfter(_showTL, self.window)

    def init(self, window):
        if self.css:
            window.load_css(self.css)
        self.showTrafficLights()
       
if __name__ == '__main__':
    HTMLMainWindow('Python html GUI', '<html><body><h1>Test</h1></body></html>', 
                   css = 'h1 {color: red;}', api = None)

