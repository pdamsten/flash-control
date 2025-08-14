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

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame.midi
from threading import Thread
from queue import Queue
import lib.metadata as meta

CC = 176
KEYDOWN = 127
KEYUP = 0
KEYS = {
    58: 'TRACK_PREV',
    59: 'TRACK_NEXT',
    46: 'CYCLE',
    60: 'MARKER_SET',
    61: 'MARKER_PREV',
    62: 'MARKER_NEXT',
    43: 'PREV',
    44: 'NEXT',
    42: 'STOP',
    41: 'PLAY',
    45: 'RECORD',
    32: ('A', 'SOLO'),
    33: ('B', 'SOLO'),
    34: ('C', 'SOLO'),
    35: ('D', 'SOLO'),
    36: ('E', 'SOLO'),
    37: ('F', 'SOLO'),
    38: ('G', 'SOLO'),
    39: ('H', 'SOLO'),
    48: ('A', 'MUTE'),
    49: ('B', 'MUTE'),
    50: ('C', 'MUTE'),
    51: ('D', 'MUTE'),
    52: ('E', 'MUTE'),
    53: ('F', 'MUTE'),
    54: ('G', 'MUTE'),
    55: ('H', 'MUTE'),
    64: ('A', 'RECORD'),
    65: ('B', 'RECORD'),
    66: ('C', 'RECORD'),
    67: ('D', 'RECORD'),
    68: ('E', 'RECORD'),
    69: ('F', 'RECORD'),
    70: ('G', 'RECORD'),
    71: ('H', 'RECORD'),
    0: ('A', 'SLIDER'),
    1: ('B', 'SLIDER'),
    2: ('C', 'SLIDER'),
    3: ('D', 'SLIDER'),
    4: ('E', 'SLIDER'),
    5: ('F', 'SLIDER'),
    6: ('G', 'SLIDER'),
    7: ('H', 'SLIDER'),
    16: ('A', 'KNOB'),
    17: ('B', 'KNOB'),
    18: ('C', 'KNOB'),
    19: ('D', 'KNOB'),
    20: ('E', 'KNOB'),
    21: ('F', 'KNOB'),
    22: ('G', 'KNOB'),
    23: ('H', 'KNOB'),
}

class NanoKontrol2:
    def __init__(self):
        self.callbacks = {}
        self.fromWorkerQueue = Queue()
        self.toWorkerQueue = Queue()
        self.worker = NanoKontrol2Worker(self.toWorkerQueue, self.fromWorkerQueue)
        self.worker.start()
        self.poller = Thread(target = self.poll)
        self.poller.start()

    def callback(self, name, callback):
        self.callbacks[name] = callback

    def connect(self, directCallback = None):
        self.sendMsg('connect', directCallback)

    def setValues(self, values):
        self.sendMsg('setValues', values)

    def setBeepAndLight(self, beep = True, light = True):
        self.sendMsg('setBeepAndLight', (beep, light))

    def stop(self):
        self.fromWorkerQueue.put(('quit', None))
        self.poller.join()
        print('* joined')

        print('* NanoKontrol2::close')
        self.sendMsg('stop')
        if self.worker:
            self.worker.join()
            self.worker = None

    def sendMsg(self, cmd, data = None):
        if self.worker:
            self.toWorkerQueue.put((cmd, data))

    def poll(self):
        while True:
            cmd, data = self.fromWorkerQueue.get()

            if cmd in self.callbacks:
                self.callbacks[cmd](data)
            if cmd == 'quit':
                print('* NanoKontrol2::poll quit')
                return


class NanoKontrol2Worker(Thread):
    def __init__(self, inQueue, outQueue):
        super().__init__()
        self.inQueue = inQueue
        self.outQueue = outQueue

        self.midi_in = None
        self.input_id = -1

        self.output_id = -1

        self.directCallback = None
    
    def sendMsg(self, cmd, data = None):
        if self.outQueue:
            self.outQueue.put((cmd, data))

    def setValues(self, values):
        a = []
        t = 0
        for ch in range(8):
            for btn in ['SOLO', 'MUTE', 'RECORD']:
                v = 0
                if ch < len(values):
                    v = 127 if values[ch][meta.MODE] != '-' else 0
                if ch in values:
                    gid = values[ch][meta.ID]
                else:
                    gid = chr(ord('A') + ch)
                a.append([[CC, self.invertedKeys[gid][btn], v], t]) 
                t += 10
        self.setLights(a) 

    def connect(self):
        pygame.midi.init()

        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            (_, name, input_dev, output_dev, _) = info
            name = name.decode()
            print(f"{i}: {name} (input={bool(input_dev)}, output={bool(output_dev)})")
            if "nanoKONTROL2" in name and bool(input_dev):
                self.input_id = i
            if "nanoKONTROL2" in name and bool(output_dev):
                self.output_id = i

        pygame.midi.quit()

        if self.output_id != -1 and self.input_id != -1:
            self.sendMsg('connected')
        else:
            self.sendMsg('failed')

    def setLights(self, a):
        if self.output_id >= 0:
            pygame.midi.init()
            midi_out = pygame.midi.Output(self.output_id)

            midi_out.write(a) 

            midi_out.close()
            del midi_out
            midi_out = None
            pygame.midi.quit()

    def resetLights(self):
        a = []
        def off(d, t):
            for _, v in d.items():
                t += 10
                if isinstance(v, dict):
                    t = off(v, t)
                else:
                    a.append([[CC, v, 0], t]) 
            return t
        t = off(self.invertedKeys, 0) + 10
        a.append([[CC, self.invertedKeys['STOP'], 127], t]) 

        self.setLights(a)

    def stop(self):
        if self.midi_in:
            self.midi_in.close()
            del self.midi_in
        if pygame.midi.get_init():
            pygame.midi.quit()

    def sendValue(self, e, d):
        self.sendMsg('event', (e, d))

    def setBeepAndLight(self, beep = True, light = True):
        a = []
        a.append([[CC, self.invertedKeys['PREV'], 127 if beep else 0], 0]) 
        a.append([[CC, self.invertedKeys['RECORD'], 127 if light else 0], 0]) 

        self.setLights(a) 

    def loop(self):
        while True:
            try:
                cmd = 'pass'
                cmd, data = self.inQueue.get(block = False, timeout = 0.1)
                print('- NanoKontrol2Worker::loop', cmd, '/', data)
            except:
                if self.input_id >= 0:
                    if not pygame.midi.get_init():
                        pygame.midi.init()
                        self.midi_in = pygame.midi.Input(self.input_id)
                    if self.midi_in.poll():
                        events = self.midi_in.read(10)
                        for event in events:
                            data, _ = event
                            if (KEYS[data[1]][1] == 'SLIDER' or KEYS[data[1]][1] == 'KNOB'):
                                if self.directCallback:
                                    self.directCallback((KEYS[data[1]][0], data[2]))
                            else:
                                self.sendMsg('event', (KEYS[data[1]], data[2]))

            if cmd == 'connect':
                print('NanoKontrol2Worker::connect')
                self.directCallback = data
                self.connect()
                self.resetLights()
            elif cmd == 'stop':
                self.stop()
                print('- NanoKontrol2Worker::stop')
                return
            elif cmd == 'setValues':
                print('- NanoKontrol2Worker::setValues', data)
                self.setValues(data)
            elif cmd == 'setBeepAndLight':
                print('- NanoKontrol2Worker::setBeepAndLight', data)
                self.setBeepAndLight(data[0], data[1])
            elif cmd == 'pass':
                pass
            else:
                print('- unknown command', cmd)

    def run(self):
        self.invertedKeys = {}
        for k, v in KEYS.items():
            if isinstance(v, str):
                self.invertedKeys[v] = k
            else:
                if v[0] not in self.invertedKeys:
                    self.invertedKeys[v[0]] = {}
                self.invertedKeys[v[0]][v[1]] = k

        self.loop()

if __name__ == '__main__':
    pass
