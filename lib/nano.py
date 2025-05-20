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

import pygame.midi
from threading import Thread
from queue import Queue

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

    def connect(self):
        self.sendMsg('connect')

    def setValues(self, values):
        self.sendMsg('setValues', values)

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
            print('* poll', cmd, data)

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
        self.midi_out = None
    
    def sendMsg(self, cmd, data = None):
        if self.outQueue:
            print('- out', cmd, data)
            self.outQueue.put((cmd, data))

    def setValues(self, values):
        print('nano values:', values)
        pass
    
    def connect(self):
        pygame.midi.init()

        output_id = None
        input_id = None
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            (_, name, input_dev, output_dev, _) = info
            name = name.decode()
            print(f"{i}: {name} (input={bool(input_dev)}, output={bool(output_dev)})")
            if "nanoKONTROL2" in name and bool(input_dev):
                input_id = i
            if "nanoKONTROL2" in name and bool(output_dev):
                output_id = i

        data = [True, True]
        if input_id is not None:
            print(f"Using nanoKONTROL2 input on device {input_id}")
            self.midi_in = pygame.midi.Input(input_id)
        else:
            print("nanoKONTROL2 input not found.")
            data[0] = False

        if output_id is not None:
            print(f"Using nanoKONTROL2 output on device {output_id}")
            self.midi_out = pygame.midi.Output(output_id)
        else:
            print("nanoKONTROL2 output not found.")
            data[1] = False

        if data != [True, True]:
            self.sendMsg('failed', data)
        else:
            self.sendMsg('connected')

    def stop(self):
        if self.midi_out:
            self.midi_out.close()
        if self.midi_in:
            self.midi_in.close()
        pygame.midi.quit()

    def loop(self):
        while True:
            cmd, data = self.inQueue.get()
            print('- NanoKontrol2Worker::loop', cmd, '/', data)

            if cmd == 'connect':
                print('NanoKontrol2Worker::connect')
                self.connect()
            elif cmd == 'stop':
                self.stop()
                print('- NanoKontrol2Worker::stop')
                return
            elif cmd == 'setValues':
                print('- NanoKontrol2Worker::setValues', data)
                self.setValues(data)
            else:
                print('- unknown command', cmd)

    def run(self):
        self.loop()

if __name__ == '__main__':
    pass
