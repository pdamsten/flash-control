#!/usr/bin/env python
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

import argparse
import sys, os
from lib.htmlgui import HTMLMainWindow
import pprint

#iconbutton = '<div class="iconbutton" onclick=\'pywebview.api.buttonPressed("{id}")\'>\n<img src="{svg}">\n<span>{title}</span></div>\n'

flash_group = '''
    <div id="flash-{group_id}" class="flash-container">
      <button class="flash-group">{group_id}</button>
      <span class="flash-power">8.0</span>
      <button class="flash-sound"><img src="svg/sound.svg"></button>
      <button class="flash-mode">M</button>
      <button class="flash-light"><img src="svg/light.svg"></button>
      <div class="flash-info-a">
        <select class="flash-name"></select>
        <select class="flash-role"></select>
      </div>
      <div class="flash-info-b">
        <select class="flash-modifier"></select>
        <select class="flash-accessory"></select>
        <select class="flash-gel"></select>
      </div>
    </div>
'''

class Api():
    def buttonPressed(self, value):
        print(value)
        HTMLMainWindow.destroy()
        sys.exit(0)

class FlashControlWindow(HTMLMainWindow):
    def __init__(self, title, html, css = None, api = None):
        super().__init__(title, html, css, api)

    def fill_select(self, element, items):
        for i, item in enumerate(items):
            element.append(f'<option value="{i}">{item}</option>')

    def onShutterClicked(self, e):
        print(e['currentTarget']['id'])

    def onChange(self, e):
        #pprint.pp(e['target'])
        print(e['target']['selectedIndex'])
        print(e['target']['childNodes'][e['target']['selectedIndex']]['text'])

    def saveDebugHtml(self):
        js = "document.documentElement.outerHTML"
        html = self.window.evaluate_js(js)
        with open(self.path('html/debug.html'), 'w') as f:
            f.write(html)

    def init(self, window):
        super().init(window)
        self.stands = window.dom.get_elements('#stands')[0]
        self.remotes = window.dom.get_elements('#remotes')[0]
        self.triggers = window.dom.get_elements('#triggers')[0]
        self.tethering = window.dom.get_elements('#tethering')[0]
        self.filters = window.dom.get_elements('#filters')[0]
        self.extension_tubes = window.dom.get_elements('#extension_tubes')[0]
        self.scroll_container = window.dom.get_elements('#scroll-container')[0]

        self.fill_select(self.stands, self.slist('user/stands.txt'))
        self.stands.events.change += self.onChange

        self.fill_select(self.remotes, self.slist('user/remotes.txt'))
        self.fill_select(self.triggers, self.slist('user/triggers.txt'))
        self.fill_select(self.tethering, self.slist('user/tethering.txt'))
        self.fill_select(self.filters, self.slist('user/filters.txt'))
        self.fill_select(self.extension_tubes, self.slist('user/extension_tubes.txt'))

        for i in range(self.cv('flash-groups', 6)):
            gid = chr(ord('A') + i)
            self.scroll_container.append(flash_group.format(group_id = gid))
            self.fill_select(window.dom.get_elements(f'#flash-{gid} .flash-name')[0], 
                             self.slist('user/flash_names.txt'))
            self.fill_select(window.dom.get_elements(f'#flash-{gid} .flash-role')[0], 
                             self.slist('user/flash_roles.txt'))
            self.fill_select(window.dom.get_elements(f'#flash-{gid} .flash-modifier')[0], 
                             self.slist('user/flash_modifiers.txt'))
            self.fill_select(window.dom.get_elements(f'#flash-{gid} .flash-accessory')[0], 
                             self.slist('user/flash_accessories.txt'))
            self.fill_select(window.dom.get_elements(f'#flash-{gid} .flash-gel')[0],
                              self.slist('user/flash_gels.txt'))
        
        window.dom.get_elements('#shutter-button')[0].events.click += self.onShutterClicked
        #self.saveDebugHtml()

def main():
    FlashControlWindow('Flash Control', HTMLMainWindow.path('html/gui.html'), api = Api())
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()    
    main()
