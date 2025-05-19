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

    def connect(self, cfg):
        self.sendMsg('connect', cfg)

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
    
    def sendMsg(self, cmd, data = None):
        if self.outQueue:
            print('- out', cmd, data)
            self.outQueue.put((cmd, data))

    def setValues(self, values):
        pass
    
    def sendCommand(self, command):
        if self.client and self.client.is_connected:
            #print(self.config['uuid'], ''.join('{:02x}'.format(x) for x in command))
            self.client.write_gatt_char(self.config['uuid'], command)

    def stop(self):
        if self.client:
            if self.client.is_connected:
                print('disconnect bt')
                self.client.disconnect()

    def loop(self):
        while True:
            cmd, data = self.inQueue.get()
            print('- NanoKontrol2Worker::loop', cmd, '/', data)

            if cmd == 'connect':
                print('NanoKontrol2Worker::connect')
                self.config = data
                self.connect()
            elif cmd == 'stop':
                self.stop()
                print('- NanoKontrol2Worker::quit')
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
