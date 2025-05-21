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
from lib.htmlgui import HTMLMainWindow
from lib.godox import Godox
from lib.nano import NanoKontrol2
from webview.dom import DOMEventHandler
import subprocess
import lib.util as util
from lib.metadata import RAWWatcher
import platform 
import os
import threading
import sys
if sys.platform.startswith('darwin'):
    from lib.numberoverlay import NumberOverlay

json_conv_table = [
    ("XMP:XMP-pdplus:Stand", 'stands'),
    ("XMP:XMP-pdplus:Tethering", 'tethering'),
    ("XMP:XMP-pdplus:Trigger", 'triggers'),
    ("XMP:XMP-pdplus:Filter", 'filters'),
    ("XMP:XMP-pdplus:ExtensionTube", 'extension_tubes'),
    ("XMP:XMP-pdplus:Remote", 'remotes'),
    ("XMP:XMP-pdplus:Exposures", "#1"),
    ("XMP:XMP-pdplus:Flashes/{index}/Role", 'flash-{group}/Role'),
    ("XMP:XMP-pdplus:Flashes/{index}/Name", 'flash-{group}/Name'),
    ("XMP:XMP-pdplus:Flashes/{index}/Modifier", 'flash-{group}/Modifier'),
    ("XMP:XMP-pdplus:Flashes/{index}/Accessory", 'flash-{group}/Accessory'),
    ("XMP:XMP-pdplus:Flashes/{index}/Power", 'flash-{group}/CurrentPower'),
    ("XMP:XMP-pdplus:Flashes/{index}/Gel", 'flash-{group}/Gel'),
    ("XMP:XMP-pdplus:Flashes/{index}/ID", '#{group}'),
]

godox_conv_table = [
    ('{index}/power', 'flash-{group}/CurrentPower'),
    ('{index}/mode', 'flash-{group}/Mode'),
    ('{index}/disabled', 'flash-{group}/Disabled'),
    ('{index}/group', '#{group}'),
]

nano_conv_table = [
    ('{group}/SOLO', '!flash-{group}/Disabled'),
    ('{group}/MUTE', '!flash-{group}/Disabled'),
    ('{group}/RECORD', '!flash-{group}/Disabled'),
]

flash_group = '''
    <div id="flash-{group_id}" class="flash-container">
      <button id="flash-group-{group_id}" class="flash-group">{group_id}</button>
      <div id="flash-power-{group_id}" class="flash-power">
            <span id="flash-power-prefix{group_id}" class="flash-prefix">-</span><span id="flash-power-number{group_id}" class="flash-power-nbr">3.0</span>
      </div>
      <button id="flash-mode-{group_id}" class="flash-mode">M</button>
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

ENTER = 13
BACKSPACE = 8
ESCAPE = 27

class FlashControlWindow(HTMLMainWindow):
    def __init__(self, title, html, css = None, api = None):
        self.power = ''
        self.activeGroup = 'A'
        self.godox = None
        self.metadata = None
        self.nano = None
        self.lastSlider = 0
        info = {
            'name': 'Flash Control',
            'bundle_version': 'X',
            'version': '0.1',
            'icon': util.path('app-icon.icns'),
            'copyright': 'Copyright © 2025 Petri Damstén\nhttps://petridamsten.com'
        }
        self.setMacOsTitle(info)
        if sys.platform.startswith('darwin'):
            self.overlay = NumberOverlay.alloc().init()
        else:
            self.overlay = None

        super().__init__(title, html, css, api)

    def on_closing(self):
        print('Flash Window closed')
        self.window.events.closing -= self.on_closing
        print('Stopping godox')
        self.godox.stop()
        print('Stopping nano')
        self.nano.stop()
        print('Stopping metadata')
        if self.metadata:
            self.metadata.stop()
        print('Stopping super')
        super().on_closing()

    def on_resized(self, width, height):
        if self.overlay:
            self.overlay.center_((self.config['x'], self.config['y'], width, height))
        super().on_moved(width, height)

    def on_moved(self, x, y):
        if self.overlay:
            self.overlay.center_((x, y, self.config['width'], self.config['height']))
        super().on_moved(x, y)

    def fill_select(self, e, items, value = None):
        e = self.elem(e)
        for i, item in enumerate(items):
            selected = ' selected' if item == value else ''
            e.append(f'<option value="{i}"{selected}>{item}</option>')

    def onShutterClicked(self, e):
        self.godox.test()

    def onSoundClicked(self, e):
        e = self.elem(e)
        self.setSound(not self.cv('Sound'))

    def onLightClicked(self, e):
        e = self.elem(e)
        self.setLight(not self.cv('ModellingLight'))

    def setSound(self, v):
        self.config['Sound'] = v
        if v:
            self.elem(f'#flash-sound-all').classes.remove('disabled')
        else:
            self.elem(f'#flash-sound-all').classes.append('disabled')
        self.setSoundAndLight()

    def setLight(self, v):
        self.config['ModellingLight'] = v
        if v:
            self.elem(f'#flash-light-all').classes.remove('disabled')
        else:
            self.elem(f'#flash-light-all').classes.append('disabled')
        self.setSoundAndLight()

    def setSoundAndLight(self):
        if self.godox:
            self.godox.setBeepAndLight(self.cv('Sound'), self.cv('ModellingLight'))
    
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
        if self.metadata:
            self.metadata.setJson(util.convertDict(self.config, json_conv_table, 'Disabled'))

    def onGroupClicked(self, e):
        e = self.elem(e)
        self.activateGroup(e.id[-1:])

    def onGroupButtonClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.setGroupDisabled(gid, not self.cv(f'flash-{gid}/Disabled'))

    def setGroupDisabled(self, group_id, disabled):
        a = ['flash-group-', 'flash-power-', 'flash-mode-', 
             'flash-name-', 'flash-role-', 'flash-modifier-', 'flash-accessory', 'flash-gel-']
        
        self.config[f'flash-{group_id}']['Disabled'] = disabled
        for s in a:
            e = self.elem(f'#{s}{group_id}')
            if disabled:
                e.classes.append('disabled')
            else:
                tmp = True
                if e.id.startswith('flash-mode-'):
                    tmp = False
                if tmp:
                    e.classes.remove('disabled')
        if not disabled:
            self.activateGroup(group_id)
        self.setFlashValues()

    def onModeClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.activateGroup(gid)
        self.setMode(gid, 'M' if self.cv(f'flash-{gid}/Mode') == 'TTL' else 'TTL')
        self.powerHtml(gid)

    def setMode(self, group_id, v):
        self.config[f'flash-{group_id}']['Mode'] = v
        self.elem(f'#flash-mode-{group_id}').text = self.config[f'flash-{group_id}']['Mode']
        self.setFlashValues()

    def activateGroup(self, group_id):
        self.onKeyPress(ENTER)
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
        print('setPower', group_id, power)
        if self.overlay:
            self.overlay.hide()
        mode = self.cv(f'flash-{group_id}/Mode', 'M')
        self.config[f'flash-{group_id}']['Power' + mode] = power
        self.config[f'flash-{group_id}']['CurrentPower'] = power
        self.powerHtml(self.activeGroup)
        self.power = ''
        self.setFlashValues()

    def setFlashValues(self):
        if self.godox:
            self.godox.setValues(util.convertDict(self.config, godox_conv_table))
        if self.metadata:
            self.metadata.setJson(util.convertDict(self.config, json_conv_table, 'Disabled'))
        if self.nano:
            self.nano.setValues(util.convertDict(self.config, nano_conv_table))

    def powerHtml(self, gid, power = None):
        e = self.elem(f'#flash-power-{gid}')
        s = str(power) if power else str(self.pwr(gid))
        if s == '10.0':
            s = '10'
        if s[0] in ['+', '-']:
            e.children[0].text = s[0]
            s = s[1:]
        else:
            e.children[0].text = ''
        e.children[1].text = s

    def onKeyPress(self, e):
        # This eats spaces and returns which prevents opening select from keyboard
        # on macos tab is not selecting buttons. Custom tab key control?
        key = e['which'] if isinstance(e, dict) else e
        print('Key pressed', key, chr(key))
        manual = (self.cv(f'flash-{self.activeGroup}/Mode') == 'M')
        if key >= ord('0') and key <= ord('9'):
            n = key - 48
            if manual:
                if len(self.power) == 1 and (self.power != '1' or n != 0):
                    self.power += '.'
                self.power += str(n)
                if self.power == '10' or len(self.power) == 3:
                    self.setPower(self.activeGroup, self.power)
            else:
                if len(self.power) == 0:
                    self.power = '+'
                if len(self.power) == 2:
                    self.power += '.'
                if len(self.power) == 3:
                    self.power += '0' if n == 0 else '3' if n < 5 else '7'
                else:
                    self.power += str(n)
                if len(self.power) == 4:
                    self.setPower(self.activeGroup, self.power)
            self.powerHtml(self.activeGroup, self.power)
        elif chr(key) == '-':
            if not manual and len(self.power) == 0:
                self.power = '-'
                self.powerHtml(self.activeGroup, self.power)
        elif chr(key) in ['.', ',']:
            if manual:
                 if len(self.power) == 1:
                    self.power += '.'
            else:
                 if len(self.power) == 2:
                    self.power += '.'
            self.powerHtml(self.activeGroup, self.power)
        elif key >= ord('a') and key <= ord('l'):
            self.activateGroup(chr(key).upper())
        elif key == ord(' '):
            self.setGroupDisabled(self.activeGroup, 
                                  not self.cv(f'flash-{self.activeGroup}/Disabled'))
        elif key == ENTER:
            if len(self.power) > 0:
                if manual:
                    if len(self.power) == 1:
                        self.power += '.0'
                    elif len(self.power) == 2:
                        self.power += '0'
                    self.setPower(self.activeGroup, self.power)
                else:
                    if len(self.power) == 1:
                        self.power = '+0.0'
                    elif len(self.power) == 2:
                        self.power += '.0'
                    elif len(self.power) == 3:
                        self.power += '0'
                    self.setPower(self.activeGroup, self.power)
        elif key == ESCAPE or key == BACKSPACE:
            if len(self.power) > 0:
                self.power = ''
                self.elem(f'#flash-power-{self.activeGroup}').text = \
                        self.cv(f'flash-{self.activeGroup}/Power')

    def onTryAgain(self, e):
        self.elem('#flash-button').classes.append('pulse')
        self.elem('#try-trigger-button').classes.append('hidden')
        self.elem('#flash-popup .message').text = 'Connecting...'
        self.godox.connect(self.cv('godox', {}))

    def onGodoxFailed(self, data):
        if data:
            msg = f'Unable to connect to Godox device: {data} and scan failed.'
        else:
            msg = 'Godox device scan failed.'
        self.elem('#flash-button').classes.remove('pulse')
        self.elem('#flash-button').classes.append('disabled')
        self.elem('#flash-popup .message').text = msg
        self.elem('#try-trigger-button').classes.remove('hidden')

    def onGodoxConnected(self, data):
        self.elem('#flash-button').classes.remove('pulse')
        self.elem('#flash-popup .message').text = f'Connected to: {data}'
        self.setSoundAndLight()
        self.godox.setValues(util.convertDict(self.config, godox_conv_table))

    def onGodoxConfig(self, data):
        self.config['godox'] = data

    def onNanoFailed(self, data):
        self.elem('#nano-button').classes.remove('pulse')
        self.elem('#nano-button').classes.append('disabled')
        self.elem('#nano-popup .message').text = f'Unable to connect to nanoKontrol2 device.'
        self.elem('#try-nano-button').classes.remove('hidden')

    def onNanoConnected(self, data):
        self.elem('#nano-button').classes.remove('pulse')
        self.elem('#nano-popup .message').text = 'Connected to nanoKontrol2'
        self.nano.setValues(util.convertDict(self.config, nano_conv_table))

    def nano2Power(self, gid, v):
        if self.cv(f'flash-{gid}/Mode', 'M') == 'M':
            v = str(round(8.0 * (v / 127.0) + 2.0, 1))
            if v == '10.0':
                v = '10'
        else:
            v = str(round(6.0 * (v / 127.0) - 3.0, 1))
        return v

    def onNanoSlider(self, d):
        if self.overlay:
            v = self.nano2Power(d[0], d[1])
            self.overlay.setValue_(v)

    def onNanoEvent(self, data):
        gid = None
        if isinstance(data[0], tuple):
            gid = data[0][0]
            cmd = data[0][1]
        else:
            cmd = data[0]
        v = data[1]

        if cmd == 'SLIDER' or cmd == 'KNOB':
            if self.activeGroup != gid:
                self.activateGroup(gid)
            self.setPower(gid, self.nano2Power(gid, v))
        elif cmd == 'RECORD' and v == 0:
            self.onShutterClicked(None)

    def pwr(self, gid):
        fid = f'flash-{gid}'
        mode = self.cv(fid + '/Mode', 'M')
        default = '10' if mode == 'M' else '+0.0'
        self.config[fid]['CurrentPower'] = self.cv(fid + '/Power' + mode, default)
        return self.config[fid]['CurrentPower']

    def onShowConfig(self, e):
        cfg = self.path('user/config.json')
        print(cfg)
        print(subprocess.Popen(['open', cfg]))

    def onMetadataMsg(self, msg):
        self.elem('#metadata-popup .message').text = msg

    def bring_window_to_front(self):
        if platform.system() == 'Darwin':
            print(subprocess.run([
                'osascript', '-e',
                f'tell application "System Events" to set frontmost of the first process whose unix id is {os.getpid()} to true'
            ]))

    def init(self, window):
        super().init(window)

        window.dom.document.events.keypress += DOMEventHandler(self.onKeyPress,
                                                               prevent_default = True)
        
        self.fill_select('#stands', util.stringList('user/stands.txt'), self.cv('stands'))
        self.fill_select('#remotes', util.stringList('user/remotes.txt'), self.cv('remotes'))
        self.fill_select('#triggers', util.stringList('user/triggers.txt'), self.cv('triggers'))
        self.fill_select('#tethering', util.stringList('user/tethering.txt'), self.cv('tethering'))
        self.fill_select('#filters', util.stringList('user/filters.txt'), self.cv('filters'))
        self.fill_select('#extension_tubes', util.stringList('user/extension_tubes.txt'), 
                         self.cv('extension_tubes'))

        for i in range(self.cv('flash-groups', 6)):
            gid = chr(ord('A') + i)
            c = self.elem('#scroll-container')
            e = c.append(flash_group.format(group_id = gid))
            e.events.click += self.onGroupClicked
            fid = f'flash-{gid}/'
            self.fill_select(f'#flash-{gid} .flash-name', util.stringList('user/flash_names.txt'),
                             self.cv(fid + 'Name'))
            self.fill_select(f'#flash-{gid} .flash-role', util.stringList('user/flash_roles.txt'),
                             self.cv(fid + 'Role'))
            self.fill_select(f'#flash-{gid} .flash-modifier', 
                             util.stringList('user/flash_modifiers.txt'), self.cv(fid + 'Modifier'))
            self.fill_select(f'#flash-{gid} .flash-accessory', 
                             util.stringList('user/flash_accessories.txt'), 
                             self.cv(fid + 'Accessory'))
            self.fill_select(f'#flash-{gid} .flash-gel', util.stringList('user/flash_gels.txt'), 
                             self.cv(fid + 'Gel'))

            self.elem(f'#flash-mode-{gid}').events.click += self.onModeClicked
            self.setMode(gid, self.cv(fid + 'Mode', 'M'))

            e = self.elem(f'#flash-power-{gid}')
            e.events.click += self.onGroupClicked
            self.powerHtml(gid)

            self.elem(f'#flash-{gid} .flash-group').events.click += self.onGroupButtonClicked
            self.setGroupDisabled(gid, self.cv(fid + 'Disabled', False))
    
        self.elem('#shutter-button').events.click += self.onShutterClicked
        self.elem(f'#flash-sound-all').events.click += self.onSoundClicked
        self.setSound(self.cv('Sound', False))
        self.elem(f'#flash-light-all').events.click += self.onLightClicked
        self.setLight(self.cv('ModellingLight', False))

        self.elem('#try-trigger-button').events.click += self.onTryAgain
        self.elem('#skull-button').events.click += self.onShowConfig

        for e in window.dom.get_elements('select'):
            e.events.change += self.onSelectChange

        self.activateGroup('A')

        self.godox = Godox()
        self.godox.callback('failed', self.onGodoxFailed)
        self.godox.callback('connected', self.onGodoxConnected)
        self.godox.callback('config', self.onGodoxConfig)
        self.godox.connect(self.cv('godox', {}))

        self.nano = NanoKontrol2()
        self.nano.callback('failed', self.onNanoFailed)
        self.nano.callback('connected', self.onNanoConnected)
        self.nano.callback('event', self.onNanoEvent)
        self.nano.connect(self.onNanoSlider)

        tethering_path = self.cv('TetheringPath', '')
        tethering_pat = self.cv('TetheringPattern', '')
        self.metadata = None

        if tethering_path:
            self.metadata = RAWWatcher()
            self.metadata.start(tethering_path, tethering_pat)
            self.metadata.setJson(util.convertDict(self.config, json_conv_table, 'Disabled'))
            self.metadata.callback('msg', self.onMetadataMsg)
            self.elem('#metadata-popup').classes.remove('disabled')

        self.window.events.closing += self.on_closing

        # self.bring_window_to_front()
        if self.overlay:
            self.overlay.center_((self.config['x'], self.config['y'], 
                                  self.config['width'], self.config['height']))

        if (args.debug):
            self.saveDebugHtml()

def main():
    FlashControlWindow('Flash Control', util.path('html/gui.html'))
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action = 'store_true')
    args = parser.parse_args()    
    main()
