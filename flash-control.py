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
        <select class="flash-name" data-key="Name"></select>
        <select class="flash-role" data-key="Role"></select>
      </div>
      <div class="flash-info-b">
        <select class="flash-modifier" data-key="Modifier"></select>
        <select class="flash-accessory" data-key="Accessory"></select>
        <select class="flash-gel" data-key="Gel"></select>
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
        self.power = ''
        super().__init__(title, html, css, api)

    def fill_select(self, e, items, value = None):
        e = self.elem(e)
        for i, item in enumerate(items):
            selected = ' selected' if item == value else ''
            e.append(f'<option value="{i}"{selected}>{item}</option>')

    def onShutterClicked(self, e):
        e = self.elem(e)
        print(e.id)

    def onSelectChange(self, e):
        elem = self.elem(e)
        pid = elem.parent.parent.id
        n = e['target']['selectedIndex'] 
        value = None if n == 0 else e['target']['childNodes'][n]['text']
        if pid.startswith('flash-'):
            self.config[pid][elem.attributes['data-key']] = value
        else:
            self.config[elem.id] = value

    def saveDebugHtml(self):
        js = "document.documentElement.outerHTML"
        html = self.window.evaluate_js(js)
        with open(self.path('html/debug.html'), 'w') as f:
            f.write(html)
    def setPower(self, group_id, power):
        print(f'setPower({group_id}, {power})')
        pass

    def onKeyPress(self, e):
        print(e['which'])
        if e['which'] >= 48 and e['which'] <= 57:
            n = e['which'] - 48
            if len(self.power) == 1 and (self.power != '1' and n != 0):
                self.power += '.'
            self.power += str(n)
            self.elem('#flash-A .flash-power').text = self.power
            if self.power == '10' or len(self.power) == 3:
                self.setPower('A', self.power)
                self.power = ''
        elif e['which'] in [44, 46, 32, 45]:
            self.power += '.'
            self.elem('#flash-A .flash-power').text = self.power

    def init(self, window):
        super().init(window)

        window.dom.document.events.keypress += self.onKeyPress
        
        self.fill_select('#stands', self.slist('user/stands.txt'), self.cv('stands'))
        self.fill_select('#remotes', self.slist('user/remotes.txt'), self.cv('remotes'))
        self.fill_select('#triggers', self.slist('user/triggers.txt'), self.cv('triggers'))
        self.fill_select('#tethering', self.slist('user/tethering.txt'), self.cv('tethering'))
        self.fill_select('#filters', self.slist('user/filters.txt'), self.cv('filters'))
        self.fill_select('#extension_tubes', self.slist('user/extension_tubes.txt'), 
                         self.cv('extension_tubes'))

        for i in range(self.cv('flash-groups', 6)):
            gid = chr(ord('A') + i)
            c = self.elem('#scroll-container')
            c.append(flash_group.format(group_id = gid))
            fid = f'flash-{gid}/'
            self.fill_select(f'#flash-{gid} .flash-name', self.slist('user/flash_names.txt'),
                             self.cv(fid + 'Name'))
            self.fill_select(f'#flash-{gid} .flash-role', self.slist('user/flash_roles.txt'),
                             self.cv(fid + 'Role'))
            self.fill_select(f'#flash-{gid} .flash-modifier', 
                             self.slist('user/flash_modifiers.txt'), self.cv(fid + 'Modifier'))
            self.fill_select(f'#flash-{gid} .flash-accessory', 
                             self.slist('user/flash_accessories.txt'), self.cv(fid + 'Accessory'))
            self.fill_select(f'#flash-{gid} .flash-gel', self.slist('user/flash_gels.txt'), 
                             self.cv(fid + 'Gel'))
        
        self.elem('#shutter-button').events.click += self.onShutterClicked

        for e in window.dom.get_elements('select'):
            e.events.change += self.onSelectChange
        #self.saveDebugHtml()

def main():
    FlashControlWindow('Flash Control', HTMLMainWindow.path('html/gui.html'), api = Api())
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()    
    main()
