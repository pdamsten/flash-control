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

import sys
import os
import inspect
import time
import json
from threading import Semaphore

import webview

import lib.util as util

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
        self.close()

    def close(self):
        print('Window closed')
        self.window.events.closing -= self.on_closing
        HTMLMainWindow.instances.remove(self)
        self.window.destroy()
        if not HTMLMainWindow.instances:
            print('All windows closed, exiting')
            self.writeConfig()
            sys.exit(0)

    def messageBox(self, msg):
        def _message(msg):
            self.window.gui.BrowserView.display_confirmation_dialog('Close', None, msg)
            semaphore.release()
            
        if sys.platform.startswith('darwin'):
            semaphore = Semaphore(0)
            AppHelper.callAfter(_message, msg)
            semaphore.acquire()
        else:
            self.window.gui.BrowserView.display_confirmation_dialog('Close', None, msg)

    def writeConfig(self):
        util.writeJson(CONFIG, self.config)

    def on_resized(self, width, height):
        self.savePosAndSize()

    def on_moved(self, x, y):
        self.savePosAndSize()

    def savePosAndSize(self):
        pos = self.window.gui.get_position(self.window.uid)
        size = self.window.gui.get_size(self.window.uid)
        self.config['width'] = size[0]
        self.config['height'] = size[1]
        self.config['x'] = pos[0]
        self.config['y'] = pos[1]

    def setPulsing(self, elem, pulsing):
        self.setClass(elem, 'pulse', pulsing)

    def setVisible(self, elem, visible):
        self.setClass(elem, 'hidden', not visible)

    def setEnabled(self, elem, enabled):
        self.setClass(elem, 'disabled', not enabled)

    def setActive(self, elem, active):
        self.setClass(elem, 'active', active)

    def setNotification(self, elem, notification):
        self.setClass(elem, 'notification', notification)

    def setClass(self, elem, cname, value):
        if isinstance(elem, str):
            elem = self.elem(elem)
        if elem:
            elem.classes.append(cname) if value else elem.classes.remove(cname)

    def innerHTML(self, elemid, htmlstring):
        print(f'innerHTML({elemid}, {htmlstring})')
        htmlstring = htmlstring.replace('\n', '\\n').replace('"', '\\"')
        js = f'document.getElementById("{elemid}").innerHTML = "{htmlstring}";'
        self.window.evaluate_js(js)

    def scrollToBottom(self, elemid):
        self.window.evaluate_js(f"""
                var e = document.getElementById('{elemid}');
                e.scrollTo({{top: e.scrollHeight, behavior: "smooth"}});
        """)

    def elementFromPoint(self, x, y):
        return self.window.evaluate_js(f"""
            e = document.elementFromPoint({x}, {y});
            e;
        """)

    def elem(self, search):
        if isinstance(search, dict):
            if 'id' in search['target']['attributes']:
                key = '#' + search['target']['attributes']['id']
            elif 'id' in search['currentTarget']:
                key = '#' + search['currentTarget']['id']
            elif 'data-pywebview-id' in search['target']['attributes']:
                key = f'[data-pywebview-id={search['target']['attributes']['data-pywebview-id']}]'
            else:
                return None
        else:
             key = search
        #print(f'elem({key})')
        if not key in self.elements:
            if e := self.window.dom.get_elements(key):
                self.elements[key] = e[0]
            else:
                return None
        return self.elements[key]

    def value(self, d, key, default = None):
        #print('*1', key, default)
        keys = key.split('/')
        for i, k in enumerate(keys[:-1]):
            #print('*2', k, d, default)
            if k.isdigit():
                k = int(k)
                if len(d) <= k:
                    d.extend([{}] * (k + 1 - len(d)))
            else:
                if not k in d:
                    if keys[i+1].isdigit():
                        d[k] = []
                    else:
                        d[k] = {}
            d = d[k]
        if keys[-1] not in d:
            d[keys[-1]] = default
        #print('*3', d[keys[-1]], keys[-1])
        return d[keys[-1]]

    def cv(self, key, default = None):
        return self.value(self.config, key, default)
   
    def __init__(self, title, html, css = None, api = None, size = (1000, 800)):
        HTMLMainWindow.instances.append(self)

        self.api = api
        self.css = css
        self.config = util.json(CONFIG)
        self.elements = {}
        print (f'Config: {json.dumps(self.config, sort_keys = True, indent = 4)}')
        hpath = html if util.isPath(html) else None
        html = html if not util.isPath(html) else None
        time.sleep(0.1)
        self.window = webview.create_window(title, hpath, html = html, 
                frameless = sys.platform.startswith('darwin'), js_api = api, 
                width = int(self.cv('width', size[0])), height = int(self.cv('height', size[1])),
                x = int(self.cv('x', 0)), y = int(self.cv('y', 0)))
        self.window.events.closing += self.on_closing
        self.window.events.resized += self.on_resized
        self.window.events.moved += self.on_moved
        webview.start(self.init, self.window)

    def setMacOsTitle(self, info):
        if sys.platform.startswith('darwin'):
            try:
                from Foundation import NSBundle

                app = AppKit.NSApplication.sharedApplication()
                icon_image = AppKit.NSImage.alloc().initWithContentsOfFile_(info['icon'])
                if icon_image:
                    app.setApplicationIconImage_(icon_image)

                bundle = NSBundle.mainBundle()
                if bundle:
                    app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                    if app_info:
                        app_info['CFBundleName'] = info['name']
                        app_info['CFBundleVersion'] = info['bundle_version']
                        app_info['CFBundleShortVersionString'] = info['version']
                        app_info['NSHumanReadableCopyright'] = info['copyright']

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

