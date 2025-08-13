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
import platform 
import os
import sys
from threading import Timer
from webview.dom import DOMEventHandler
import subprocess

from lib.htmlgui import HTMLMainWindow
from lib.godox import Godox
from lib.nano import NanoKontrol2
import lib.util as util
from lib.metadata import RAWWatcher
import lib.metadata as meta
import lib.splash as splash
import lib.exiftool as exiftool

if sys.platform.startswith('darwin'):
    from lib.numberoverlay import NumberOverlay

flash_group = '''
    <div id="flash-{group_id}" class="flash-container">
      <button id="flash-group-{group_id}" tabindex="0" class="flash-group">{group_id}</button>
      <div id="flash-power-{group_id}" class="flash-power">
            <span id="flash-power-prefix{group_id}" class="flash-prefix">-</span><span id="flash-power-number{group_id}" class="flash-power-nbr">3.0</span>
      </div>
      <button id="flash-mode-{group_id}" tabindex="0" class="flash-mode">M</button>
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
SPACE = ord(' ')

class KeyHandler:
    def onKeyPress(self, key):
        self.window.onKeyPress(key)

    def start(self, window):
        self.window = window
        js_code = """
        document.addEventListener('keypress', function(event) {
            if (!event.target.isContentEditable) {
                const tag = event.target.tagName.toLowerCase();
                if (!['input', 'select', 'button'].includes(tag)) {
                    event.preventDefault();
                    window.pywebview.api.onKeyPress(event.keyCode);
                }
            }
        }, true);
        """
        window.window.evaluate_js(js_code)

class FlashControlWindow(HTMLMainWindow):
    def __init__(self, title, html, css = None):
        self.power = ''
        self.activeGroup = 'A'
        self.godox = None
        self.metadata = None
        self.nano = None
        self.lastSlider = 0
        self.delay = None
        self.overlay = None
        self.overlayPwr = None
        self.keyhandler = KeyHandler()
        self.FRACTIONS = [2 ** n for n in range(11)]
        self.FRACTIONS.reverse()


        if sys.platform.startswith('darwin'):
            self.overlay = NumberOverlay.alloc().init()

        info = {
            'name': 'Flash Control',
            'bundle_version': 'X',
            'version': '0.1',
            'icon': util.path('app-icon.icns'),
            'copyright': 'Copyright © 2025 Petri Damstén\nhttps://petridamsten.com'
        }
        self.setMacOsTitle(info)
        super().__init__(title, html, css, self.keyhandler)

    def on_closing(self):
        self.close()
        super().on_closing()

    def close(self):
        print('Flash Window closed')
        self.window.events.closing -= self.on_closing
        if self.godox:
            print('Stopping godox')
            self.godox.stop()
        if self.nano:
            print('Stopping nano')
            self.nano.stop()
        if self.metadata:
            print('Stopping metadata')
            self.metadata.stop()
        print('Stopping super')
        super().close()

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
        self.setEnabled(f'#flash-sound-all', v)
        self.setSoundAndLight()

    def setLight(self, v):
        self.config['ModellingLight'] = v
        self.setEnabled(f'#flash-light-all', v)
        self.setSoundAndLight()

    def setSoundAndLight(self):
        if self.godox:
            self.godox.setBeepAndLight(self.cv('Sound'), self.cv('ModellingLight'))
        if self.nano:
            self.nano.setBeepAndLight(self.cv('Sound'), self.cv('ModellingLight'))
    
    def forExiftool(data):
        data[meta.FLASHES] = [x for x in data[meta.FLASHES] if x[meta.MODE] != '-']
        return data
    
    def onSelectChange(self, e):
        elem = self.elem(e)
        key = getattr(meta, elem.attributes['data-key'].upper())
        pid = elem.parent.parent.id
        n = e['target']['selectedIndex'] 
        value = None if n == 0 else e['target']['childNodes'][n]['text']
        if pid.startswith('flash-'):
            index = pid[-1:]
            self.config['shooting-info'][meta.FLASHES][self.findex(index)][key] = value
            self.activateGroup(index)
        else:
            self.config['shooting-info'][key] = value
        if self.metadata:
            self.metadata.setJson(self.forExiftool(self.config['shooting-info']))

    def onGroupClicked(self, e):
        e = self.elem(e)
        self.activateGroup(e.id[-1:])

    def onGroupButtonClicked(self, e):
        e = self.elem(e)
        gid = e.id[-1:]
        self.setGroupDisabled(gid, not self.disabled(gid))

    def setGroupDisabled(self, group_id, disabled):
        a = ['flash-group-', 'flash-power-', 'flash-mode-', 
             'flash-name-', 'flash-role-', 'flash-modifier-', 'flash-accessory', 'flash-gel-']

        mode = '-' if disabled else self.cv(f'save/{group_id}/mode', 'M') 
        self.config['shooting-info'][meta.FLASHES][self.findex(group_id)][meta.MODE] = mode
        if not disabled:
            self.config['save'][group_id]['mode'] = mode
        for s in a:
            self.setEnabled(f'#{s}{group_id}', not disabled)
        if not disabled:
            self.activateGroup(group_id)
        self.setFlashValues()

    def disabled(self, group):
        if isinstance(group, str):
            group = self.findex(group)
        return (self.cv(f'shooting-info/{meta.FLASHES}/{group}/{meta.MODE}', '-') == '-')

    def onModeClicked(self, e):
        if e:
            e = self.elem(e)
            gid = e.id[-1:]
            self.activateGroup(gid)
        else:
            gid = self.activeGroup
        m = self.cv(f'save/{gid}/mode', 'M')
        self.setMode(gid, 'M' if m == 'TTL' else 'TTL')
        self.powerHtml(gid)

    def setMode(self, group_id, v):
        i = ord(group_id) - ord('A')
        self.config['shooting-info'][meta.FLASHES][i][meta.MODE] = v
        self.config['save'][group_id]['mode'] = v
        self.elem(f'#flash-mode-{group_id}').text = v
        self.setFlashValues()

    def activateFirstEnabledGroup(self):
        for i in range(self.cv('flash-groups', 6)):
            if not self.disabled(i):
                self.activateGroup(chr(ord('A') + i))
                return True
        return False

    def activateGroup(self, group_id):
        self.onKeyPress(ENTER)
        e = self.elem(f'#flash-{group_id}')
        if e:
            self.activeGroup = group_id
            for ch in range(ord('A'), ord('L') + 1):
                self.setActive(f'#flash-{chr(ch)}', False)
            self.setActive(e, True)

    def saveDebugHtml(self):
        js = "document.documentElement.outerHTML"
        html = self.window.evaluate_js(js)
        with open(util.path('html/debug.html'), 'w') as f:
            f.write(html)

    def convertFromFraction(self, power):
        if not isinstance(power, str):
            return power
        l = power.replace('1/', '').split('+')
        if len(l) > 1:
            try:
                b = float(l[1])
            except:
                b = 0.0
        else:
            b = 0
        try:
            an = int(l[0])
        except:
            an = 1
        a = min(enumerate(self.FRACTIONS), key = lambda x: abs(x[1] - an))[0]
        res = max(a + b, 0)
        print('Convert:', power, '=>', res)
        return res

    def normalizePower(self, gid, power):
        if power.find('/') >= 0:
            power = self.convertFromFraction(power)
        mode = self.cv(f'save/{gid}/mode', 'M')
        power = float(power)
        power = max(2.0, min(10.0, power)) if mode == 'M' else max(-3.0, min(3.0, power))
        power = str(round(power, 1))
        if mode == 'TTL' and power[0] != '-':
            power = '+' + power
        if power == '10.0':
            power = '10'
        return power

    def setPowerFast(self, gid, pwr):
        if self.delay:
            self.delay.cancel()
        self.overlayPwr = self.normalizePower(gid, pwr)
        self.delay = Timer(0.5, self.setPower, [gid, pwr])
        self.delay.start()
        if self.overlay:
            self.overlay.setValue_(self.overlayPwr)

    def setPower(self, group_id, power):
        print('setPower', group_id, power)
        if self.overlay:
            self.overlay.hide()
            self.overlayPwr = None
        power = self.normalizePower(group_id, power)
        mode = self.cv(f'save/{group_id}/mode', 'M')
        self.config['shooting-info'][meta.FLASHES][self.findex(group_id)]['Power'] = power
        self.config['save'][group_id]['Power' + mode] = power
        self.powerHtml(group_id)
        self.power = ''
        self.setFlashValues()

    def setFlashValues(self):
        if self.godox:
            self.godox.setValues(self.config['shooting-info'][meta.FLASHES])
        if self.metadata:
            self.metadata.setJson(self.forExiftool(self.config['shooting-info']))
        if self.nano:
            self.nano.setValues(self.config['shooting-info'][meta.FLASHES])

    def powerHtml(self, gid, power = None):
        e = self.elem(f'#flash-power-{gid}')
        s = str(power) if power else str(self.pwr(gid))
        s = self.normalizePower(gid, s)
        if s[0] in ['+', '-']:
            e.children[0].text = s[0]
            s = s[1:]
        else:
            e.children[0].text = ''
        e.children[1].text = s

    def onKeyPress(self, key):
        print('Key pressed', key, chr(key))
        manual = (self.cv(f'save/{self.activeGroup}/mode', 'M') == 'M')
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
        elif key == SPACE:
            self.setGroupDisabled(self.activeGroup, not self.disabled(self.activeGroup))
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
                pkey = f'shooting-info/{meta.FLASHES}/{self.findex(self.activeGroup)}/{meta.POWER}'
                self.elem(f'#flash-power-{self.activeGroup}').text = self.cv(pkey)
        elif key == ord('m'):
            self.setSound(not self.cv('Sound'))
        elif key == ord('z'):
            self.setLight(not self.cv('ModellingLight'))
        elif key == ord('t'):
            self.onModeClicked(None)

    def onTryAgain(self, e):
        self.setPulsing('#flash-button', True)
        self.setVisible('#try-trigger-button', False)
        self.elem('#flash-popup .message').text = 'Connecting...'
        self.godox.connect(self.cv('godox', {}))

    def onGodoxFailed(self, data):
        if data:
            msg = f'Unable to connect to Godox device: {data} and scan failed.'
        else:
            msg = 'Godox device scan failed.'
        self.setPulsing('#flash-button', False)
        self.setEnabled('#flash-button', False)
        self.elem('#flash-popup .message').text = msg
        self.setNotification('#flash-button', True)
        self.setVisible('#try-trigger-button', True)

    def onGodoxConnected(self, data):
        self.setPulsing('#flash-button', False)
        self.elem('#flash-popup .message').text = f'Connected to: {data}'
        self.setSoundAndLight()
        self.godox.setValues(self.config['shooting-info'][meta.FLASHES])

    def onGodoxConfig(self, data):
        self.config['godox'] = data

    def onNanoFailed(self, data):
        self.setPulsing('#nano-button', False)
        self.setEnabled('#nano-button', False)
        self.setVisible('#try-nano-button', True)
        self.setNotification('#nano-button', True)
        self.elem('#nano-popup .message').text = f'Unable to connect to nanoKontrol2 device.'

    def onNanoConnected(self, data):
        self.setPulsing('#nano-button', False)
        self.elem('#nano-popup .message').text = 'Connected to nanoKontrol2'
        self.nano.setValues(self.config['shooting-info'][meta.FLASHES])

    def nano2Power(self, gid, v):
        if self.cv(f'save/{gid}/mode', 'M') == 'M':
            v = 8.0 * (v / 127.0) + 2.0
        else:
            v = 6.0 * (v / 127.0) - 3.0
        return v

    def onNanoSlider(self, d):
        v = self.nano2Power(d[0], d[1])
        self.setPowerFast(d[0], v)

    def onNanoEvent(self, data):
        gid = '-'
        if isinstance(data[0], tuple):
            gid = data[0][0]
            cmd = data[0][1]
        else:
            cmd = data[0]
        v = data[1]
        print('onNanoEvent', gid, cmd, v)
        if cmd == 'SLIDER' or cmd == 'KNOB':
            if self.activeGroup != gid:
                self.activateGroup(gid)
            self.setPower(gid, self.nano2Power(gid, v))
        elif (cmd == 'RECORD' or cmd == 'SOLO' or cmd == 'MUTE') and gid != '-' and v == 0:
            self.activateGroup(gid)
            self.setGroupDisabled(gid, not self.disabled(gid))
        elif cmd == 'STOP' and gid == '-' and v == 0:
            self.onShutterClicked(None)
        elif cmd == 'RECORD' and gid == '-' and v == 0:
            self.setLight(not self.cv('ModellingLight'))
        elif cmd == 'PREV' and gid == '-' and v == 0:
            self.setSound(not self.cv('Sound'))

    def pwr(self, gid):
        mode = self.cv(f'save/{gid}/mode', 'M')
        default = '10' if mode == 'M' else '+0.0'
        pwr = self.cv(f'save/{gid}/Power{mode}', default)
        self.config['shooting-info'][meta.FLASHES][self.findex(gid)]['Power'] = pwr
        return pwr

    def onShowConfig(self, e):
        cfg = util.path('user/config.json')
        print(cfg)
        print(subprocess.Popen(['open', cfg]))

    def onMetadataMsg(self, msg):
        self.elem('#metadata-popup .message').append = f'<span>{msg[0]}</span><br'
        if msg[1] > 0:
            self.setNotification('#meta-button', True)

    def onShowFlashPopup(self, e):
        self.setVisible('#flash-popup', True)
        self.setVisible('#flash-close', True)
        self.setNotification('#flash-button', False)

    def onCloseFlashPopup(self, e):
        self.setVisible('#flash-popup', False)
        self.setVisible('#flash-close', False)

    def onShowMetaPopup(self, e):
        self.setVisible('#meta-popup', True)
        self.setVisible('#meta-close', True)
        self.setNotification('#meta-button', False)

    def onCloseMetaPopup(self, e):
        self.setVisible('#meta-popup', False)
        self.setVisible('#meta-close', False)

    def onShowNanoPopup(self, e):
        self.setVisible('#nano-popup', True)
        self.setVisible('#nano-close', True)
        self.setNotification('#nano-button', False)

    def onCloseNanoPopup(self, e):
        self.setVisible('#nano-popup', False)
        self.setVisible('#nano-close', False)

    def onOkPressed(self, e):
        # TODO save metadata
        self.close()

    def onCancelPressed(self, e):
        self.close()

    def onWheel(self, e):
        elem = self.elementFromPoint(e['clientX'], e['clientY'])
        if elem and 'id' in elem and elem['id'].startswith('flash-power-number'):
            gid = elem['id'][-1:]
            if e['wheelDelta'] < 0:
                n = min(round(e['wheelDelta'] / 5000.0, 1), -0.1)
            else:
                n = max(round(e['wheelDelta'] / 5000.0, 1), 0.1)
            if not self.overlayPwr:
                self.overlayPwr = self.pwr(gid)
            print(float(self.overlayPwr), n, float(self.overlayPwr) + n)
            n = float(self.overlayPwr) + n
            self.setPowerFast(gid, n)

    def bring_window_to_front(self):
        if platform.system() == 'Darwin':
            print(subprocess.run([
                'osascript', '-e',
                f'tell application "System Events" to set frontmost of the first process whose unix id is {os.getpid()} to true'
            ]))

    def findex(self, gid):
        return ord(gid.upper()) - ord('A')

    def onFramesChange(self, e):
        e = self.elem(e)
        self.config['shooting-info'][meta.EXPOSURES] = e.value

    def fill_shooting_info(self, si):
        self.fill_select('#stands', util.stringList('user/stands.txt'), 
                         self.value(si, meta.STAND))
        self.fill_select('#remotes', util.stringList('user/remotes.txt'), 
                         self.value(si, meta.REMOTE))
        self.fill_select('#triggers', util.stringList('user/triggers.txt'), 
                         self.value(si, meta.TRIGGER))
        self.fill_select('#tethering', util.stringList('user/tethering.txt'), 
                         self.value(si, meta.TETHERING))
        self.fill_select('#filters', util.stringList('user/filters.txt'), 
                         self.value(si, meta.FILTER))
        self.fill_select('#extension_tubes', util.stringList('user/extension_tubes.txt'), 
                         self.value(si, meta.EXTENSION_TUBE))
        e = self.elem(f'#frames-edit')
        e.value = self.value(si, meta.EXPOSURES, 1)
        e.events.change += self.onFramesChange

        for i in range(self.cv('flash-groups', 6)):
            fid = f'{meta.FLASHES}/{i}/'
            gid = self.value(si, fid + meta.ID, chr(ord('A') + i))
            c = self.elem('#scroll-container')
            e = c.append(flash_group.format(group_id = gid))
            e.events.click += self.onGroupClicked
            self.fill_select(f'#flash-{gid} .flash-name', util.stringList('user/flash_names.txt'),
                             self.value(si, fid + meta.NAME))
            self.fill_select(f'#flash-{gid} .flash-role', util.stringList('user/flash_roles.txt'),
                             self.value(si, fid + meta.ROLE))
            self.fill_select(f'#flash-{gid} .flash-modifier', 
                             util.stringList('user/flash_modifiers.txt'), 
                             self.value(si, fid + meta.MODIFIER))
            self.fill_select(f'#flash-{gid} .flash-accessory', 
                             util.stringList('user/flash_accessories.txt'), 
                             self.value(si, fid + meta.ACCESSORY))
            self.fill_select(f'#flash-{gid} .flash-gel', util.stringList('user/flash_gels.txt'), 
                             self.value(si, fid + meta.GEL))

            self.elem(f'#flash-mode-{gid}').events.click += self.onModeClicked
            default = 'M' if self.value(si, fid + meta.NAME) else '-'
            mode = self.value(si, fid + meta.MODE, default)
            smode = self.cv(f'save/{gid}/mode', 'M')
            self.setMode(gid, smode if mode == '-' else mode)

            e = self.elem(f'#flash-power-{gid}')
            e.events.click += self.onGroupClicked
            self.powerHtml(gid, self.value(si, fid + meta.POWER))

            self.elem(f'#flash-{gid} .flash-group').events.click += self.onGroupButtonClicked
            self.setGroupDisabled(gid, mode == '-')

    def init(self, window):
        super().init(window)

        splash.stop()

        self.elem('#shutter-button').events.click += self.onShutterClicked
        self.elem(f'#flash-sound-all').events.click += self.onSoundClicked
        self.setSound(self.cv('Sound', False))
        self.elem(f'#flash-light-all').events.click += self.onLightClicked
        self.setLight(self.cv('ModellingLight', False))

        self.elem('#try-trigger-button').events.click += self.onTryAgain
        self.elem('#skull-button').events.click += self.onShowConfig

        self.elem('#flash-button').events.click += self.onShowFlashPopup
        self.elem('#meta-button').events.click += self.onShowMetaPopup
        self.elem('#nano-button').events.click += self.onShowNanoPopup
        self.elem('#flash-close').events.click += self.onCloseFlashPopup
        self.elem('#meta-close').events.click += self.onCloseMetaPopup
        self.elem('#nano-close').events.click += self.onCloseNanoPopup

        self.elem('#ok-button').events.click += self.onOkPressed
        self.elem('#cancel-button').events.click += self.onCancelPressed

        for e in window.dom.get_elements('select'):
            e.events.change += self.onSelectChange
        self.window.events.closing += self.on_closing

        if not args.edit:
            self.fill_shooting_info(self.cv('shooting-info', {}))
        
            self.setVisible('#flash-button', True)
            self.setVisible('#meta-button', True)
            self.setVisible('#nano-button', True)
            self.setVisible('#flash-sound-all', True)
            self.setVisible('#shutter-button', True)
            self.setVisible('#flash-light-all', True)

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
            if tethering_path:
                self.metadata = RAWWatcher()
                self.metadata.start(tethering_path, tethering_pat)
                self.metadata.setJson(self.forExiftool(self.config['shooting-info']))
                self.metadata.callback('msg', self.onMetadataMsg)
                self.setEnabled('#metadata-popup', True)

        else:
            if len(args.edit) > 1:
                if os.path.exists(args.edit[1]):
                    data = util.json(args.edit[1])
                else:
                    self.messageBox(f'File not found: {args.edit[1]}')
                    self.close()
            else:
                if os.path.exists(args.edit[0]):
                    data = exiftool.read(args.edit[0])
                else:
                    self.messageBox(f'File not found: {args.edit[0]}')
                    self.close()

            self.fill_shooting_info(data)

            self.setVisible('#frames-edit', True)
            self.setVisible('#frames-text', True)
            self.setVisible('#ok-button', True)
            self.setVisible('#cancel-button', True)

        self.activateFirstEnabledGroup()

        # self.bring_window_to_front()
        if self.overlay:
            self.overlay.center_((self.config['x'], self.config['y'], 
                                  self.config['width'], self.config['height']))

        if (args.debug):
            self.saveDebugHtml()

        self.keyhandler.start(self)
        window.dom.document.events.wheel += DOMEventHandler(self.onWheel)

def main():
    splash.start(util.path('splash.png'), 20)
    FlashControlWindow('Flash Control', util.path('html/gui.html'))
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action = 'store_true')
    parser.add_argument('-e', '--edit', nargs = '+', help = 'Edit metadata in file')
    args = parser.parse_args()    
    main()
