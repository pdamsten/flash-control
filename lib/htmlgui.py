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
        print('Window closed')
        self.window.events.closing -= self.on_closing
        HTMLMainWindow.instances.remove(self)
        self.window.destroy()
        if not HTMLMainWindow.instances:
            print('All windows closed, exiting')
            self.writeConfig()
            sys.exit(0)

    def writeConfig(self):
        util.writeJson(CONFIG, self.config)

    def on_resized(self, width, height):
        self.config['width'] = width
        self.config['height'] = height

    def on_moved(self, x, y):
        self.config['x'] = x
        self.config['y'] = y

    def setPulsing(self, elem, pulsing):
        self.setClass(elem, 'pulse', pulsing)

    def setVisible(self, elem, visible):
        self.setClass(elem, 'hidden', not visible)

    def setEnabled(self, elem, enabled):
        self.setClass(elem, 'disabled', not enabled)

    def setActive(self, elem, active):
        self.setClass(elem, 'active', not active)

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
    
    def cv(self, key, default = None):
        keys = key.split('/')
        d = self.config
        for k in keys[:-1]:
            if not k in d:
                d[k] = {}
            d = d[k]
        if keys[-1] not in d:
            d[keys[-1]] = default
        return d[keys[-1]]
   
    def __init__(self, title, html, css = None, api = None, size = (1000, 800)):
        HTMLMainWindow.instances.append(self)

        self.api = api
        self.css = css
        self.config = util.json(CONFIG)
        self.elements = {}
        print (f'Config: {self.config}')
        hpath = html if util.isPath(html) else None
        html = html if not util.isPath(html) else None
        time.sleep(0.1)
        self.window = webview.create_window(title, hpath, html = html, 
                frameless = sys.platform.startswith('darwin'), js_api = api, 
                width = self.cv('width', size[0]), height = self.cv('height', size[1]),
                x = self.cv('x'), y = self.cv('y'))
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

