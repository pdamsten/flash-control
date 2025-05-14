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
from webview.dom import DOMEventHandler

#iconbutton = '<div class="iconbutton" onclick=\'pywebview.api.buttonPressed("{id}")\'>\n<img src="{svg}">\n<span>{title}</span></div>\n'

flash_group = '''
    <div id="flash-{group_id}" class="flash-container">
      <button id="flash-group-{group_id}" class="flash-group">{group_id}</button>
      <span id="flash-power-{group_id}" class="flash-power">8.0</span>
      <button id="flash-sound-{group_id}" class="flash-sound"><img src="svg/sound.svg"></button>
      <button id="flash-mode-{group_id}" class="flash-mode disabled">M</button>
      <button id="flash-light-{group_id}" class="flash-light"><img src="svg/light.svg"></button>
      <div class="flash-info-a">
        <select id="flash-name-{group_id}" class="flash-name" data-key="Name"></select>
        <select id="flash-role-{group_id}" class="flash-role" data-key="Role"></select>
      </div>
      <div class="flash-info-b">
        <select id="flash-modifier-{group_id}" class="flash-modifier" data-key="Modifier"></select>
        <select id="flash-accessory{group_id}" class="flash-accessory" data-key="Accessory"></select>
        <select id="flash-gel-{group_id}" class="flash-gel" data-key="Gel"></select>
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
        self.activeGroup = 'A'
        info = {
            'name': 'Flash Control',
            'bundle_version': 'X',
            'version': '0.1',
            'icon': self.path('app-icon.icns'),
            'copyright': 'Copyright © 2025 Petri Damstén'
        }
        print(self.path('app_icon.icns'))
        self.setMacOsTitle(info)

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
            self.activateGroup(pid[-1:])
        else:
            self.config[elem.id] = value

    def onGroupClicked(self, e):
        e = self.elem(e)
        self.activateGroup(e.id[-1:])

    def onGroupButtonClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.setGroupDisabled(gid, not self.cv(f'flash-{gid}/Disabled'))

    def setGroupDisabled(self, group_id, disabled):
        a = ['flash-group-', 'flash-power-', 'flash-sound-', 'flash-mode-', 'flash-light-', 
             'flash-name-', 'flash-role-', 'flash-modifier-', 'flash-accessory', 'flash-gel-']
        
        self.config[f'flash-{group_id}']['Disabled'] = disabled
        for s in a:
            print(f'#{s}{group_id}')
            e = self.elem(f'#{s}{group_id}')
            if disabled:
                e.classes.append('disabled')
            else:
                tmp = True
                if e.id.startswith('flash-sound-'):
                    tmp = self.cv(f'flash-{group_id}/Sound')
                elif e.id.startswith('flash-mode-'):
                    tmp = False
                elif e.id.startswith('flash-light-'):
                    tmp = self.cv(f'flash-{group_id}/Light')
                if tmp:
                    e.classes.remove('disabled')
        if not disabled:
            self.activateGroup(group_id)

    def onSoundClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.activateGroup(gid)
        self.setSound(gid, not self.cv(f'flash-{gid}/Sound'))

    def onModeClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.activateGroup(gid)
        self.setMode(gid, 'M' if self.cv(f'flash-{gid}/Mode') == 'TTL' else 'TTL')

    def onLightClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.activateGroup(gid)
        self.setLight(gid, not self.cv(f'flash-{gid}/Light'))

    def setSound(self, group_id, v):
        self.config[f'flash-{group_id}']['Sound'] = v
        if v:
            self.elem(f'#flash-sound-{group_id}').classes.remove('disabled')
        else:
            self.elem(f'#flash-sound-{group_id}').classes.append('disabled')

    def setMode(self, group_id, v):
        self.config[f'flash-{group_id}']['Mode'] = v
        self.elem(f'#flash-mode-{group_id}').text = self.config[f'flash-{group_id}']['Mode']

    def setLight(self, group_id, v):
        self.config[f'flash-{group_id}']['Light'] = v
        if v:
            self.elem(f'#flash-light-{group_id}').classes.remove('disabled')
        else:
            self.elem(f'#flash-light-{group_id}').classes.append('disabled')

    def activateGroup(self, group_id):
        if len(self.power) > 0:
            if len(self.power) == 1:
                self.power += '.0'
            elif len(self.power) == 2:
                self.power += '0'
            self.setPower(self.activeGroup, self.power)
        e = self.elem(f'#flash-{group_id}')
        if e:
            self.activeGroup = group_id
            for ch in range(ord('A'), ord('L') + 1):
                et = self.elem(f'#flash-{chr(ch)}')
                if et:
                    et.classes.remove('active')
            e.classes.append('active')

    def saveDebugHtml(self):
        js = "document.documentElement.outerHTML"
        html = self.window.evaluate_js(js)
        with open(self.path('html/debug.html'), 'w') as f:
            f.write(html)

    def setPower(self, group_id, power):
        self.config[f'flash-{group_id}']['Power'] = power
        self.elem(f'#flash-power-{self.activeGroup}').text = power
        self.power = ''

    def onKeyPress(self, e):
        # This eats spaces and returns which prevents opening select from keyboard
        # on macos tab is not selecting buttons. Custom tab key control?
        print('Key pressed', chr(e['which']))
        if e['which'] >= ord('0') and e['which'] <= ord('9'):
            n = e['which'] - 48
            if len(self.power) == 1 and (self.power != '1' or n != 0):
                self.power += '.'
            self.power += str(n)
            self.elem(f'#flash-{self.activeGroup} .flash-power').text = self.power
            if self.power == '10' or len(self.power) == 3:
                self.setPower(self.activeGroup, self.power)
        elif chr(e['which']) in ['.', ',', '-'] and len(self.power) == 1:
            self.power += '.'
            self.elem(f'#flash-{self.activeGroup} .flash-power').text = self.power
        elif e['which'] >= ord('a') and e['which'] <= ord('l'):
            self.activateGroup(chr(e['which']).upper())
        elif e['which'] == ord(' '):
            print('Space pressed')
            self.setGroupDisabled(self.activeGroup, 
                                  not self.cv(f'flash-{self.activeGroup}/Disabled'))
    
    def init(self, window):
        super().init(window)

        window.dom.document.events.keypress += DOMEventHandler(self.onKeyPress,
                                                               prevent_default = True)
        
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
            e = c.append(flash_group.format(group_id = gid))
            e.events.click += self.onGroupClicked
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
            self.elem(f'#flash-{gid} .flash-group').events.click += self.onGroupButtonClicked
            self.setGroupDisabled(gid, self.cv(fid + 'Disabled', False))

            e = self.elem(f'#flash-power-{gid}')
            e.events.click += self.onGroupClicked
            e.text = self.cv(fid + 'Power', 10)

            self.elem(f'#flash-sound-{gid}').events.click += self.onSoundClicked
            self.setSound(gid, self.cv(fid + 'Sound', False))
            self.elem(f'#flash-mode-{gid}').events.click += self.onModeClicked
            self.setMode(gid, self.cv(fid + 'Mode', 'M'))
            self.elem(f'#flash-light-{gid}').events.click += self.onLightClicked
            self.setLight(gid, self.cv(fid + 'Light', False))
    
        self.elem('#shutter-button').events.click += self.onShutterClicked

        for e in window.dom.get_elements('select'):
            e.events.change += self.onSelectChange

        self.activateGroup('A')

        if (args.debug):
            self.saveDebugHtml()

def main():
    FlashControlWindow('Flash Control', HTMLMainWindow.path('html/gui.html'), api = Api())
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action = 'store_true')
    args = parser.parse_args()    
    main()
