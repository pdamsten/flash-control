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

from threading import Thread
from queue import Queue
import asyncio
from copy import deepcopy

from bleak import BleakScanner
from bleak import BleakClient
import PyObjCTools
from crccheck.crc import Crc8Maxim

import lib.metadata as meta
import lib.power as power
from lib.logger import INFO, ERROR, EXCEPTION, DEBUG, VERBOSE

class Godox:
    def __init__(self):
        self.callbacks = {}
        self.fromWorkerQueue = Queue()
        self.toWorkerQueue = Queue()
        self.worker = GodoxWorker(self.toWorkerQueue, self.fromWorkerQueue)
        self.worker.start()
        self.poller = Thread(target = self.poll)
        self.poller.start()

    def callback(self, name, callback):
        self.callbacks[name] = callback

    def connect(self, cfg):
        self.sendMsg('connect', cfg)

    def setValues(self, values):
        self.sendMsg('setValues', values)

    def setBeepAndLight(self, beep = True, light = True):
        self.sendMsg('setBeepAndLight', (beep, light))

    def test(self):
        self.sendMsg('test')

    def stop(self):
        self.fromWorkerQueue.put(('quit', None))
        self.poller.join()

        INFO('Godox::close')
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
                DEBUG('Godox::poll quit')
                return


class GodoxWorker(Thread):
    modes = {'-': 3, 'T': 0, 'M': 1}

    def __init__(self, inQueue, outQueue):
        super().__init__()
        self.config = {}
        self.inQueue = inQueue
        self.outQueue = outQueue
        self.client = None
        self.pastValues = {}
    
    def sendMsg(self, cmd, data = None):
        if self.outQueue:
            self.outQueue.put((cmd, data))
    
    async def scan(self):
        INFO('scanning...')
        name = None
        try:
            devices = await BleakScanner.discover()
        except Exception as e:
            EXCEPTION('Scanning Failed.')
            self.sendMsg('failed', str(e))
            return False
        godox = None
        for device in devices:
            name = str(PyObjCTools.KeyValueCoding.getKey(device.details, 'name')[0])
            if name.startswith('GDBH'):
                INFO(f'Godox found: {name}')
                godox = device
                break
        uuid = None
        if godox:
            address = str(PyObjCTools.KeyValueCoding.getKey(godox.details, 'identifier')[0])
            DEBUG(f'Godox address: {address}')
            async with BleakClient(address) as client:
                for service in client.services:
                    pre = '**' if service.description.startswith('KDDI') else ' ' * 2
                    for ch in service.characteristics:
                        pre = '  **' if ch.uuid.startswith('0000fec7') else ' ' * 4
                        if pre.strip() != '':
                            uuid = ch.uuid
        if uuid:
            self.config = {}
            self.config['name'] = name
            self.config['address'] = address
            self.config['uuid'] = uuid
            self.sendMsg('config', self.config)
            return True
        else:
            ERROR(f'GodoxWorker::scan failed', self.config)
            self.sendMsg('failed', self.config['name'] if name and name in self.config else None)
            return False

    async def connect(self):
        tries = 0
        while tries < 2:
            if self.client and self.client.is_connected:
                INFO('already connected')
                return True

            if 'address' in self.config:
                if not self.client:
                    self.client = BleakClient(self.config['address'])
                try:
                    await self.client.connect()
                    self.sendMsg('connected', self.config['name'])
                    return True
                except:
                    pass

            if not await self.scan():
                return False

            tries += 1

    @staticmethod
    def checksum(command):
        crcinst = Crc8Maxim()
        crcinst.process(command)
        return command + crcinst.finalbytes()

    async def test(self):
        cmd = bytes.fromhex("31333234312C54657374")
        await self.sendCommand(cmd)

    async def setValues(self, values):
        def eq(key, i, a, b):
            if i >= len(a) or i >= len(b):
                return False
            if not key in a[i] or not key in b[i]:
                return False
            if a[i][key] != b[i][key]:
                return False
            return True
        
        for i, v in enumerate(values):
            if not eq(meta.POWER, i, self.pastValues, values) or \
               not eq(meta.MODE, i, self.pastValues, values):
                await self.setPower(v[meta.ID], v[meta.MODE][0], v[meta.POWER])
        self.pastValues = deepcopy(values)

    async def setBeepAndLight(self, beep = True, light = True):
        cmd = list(bytes.fromhex("F0A00A00000003000000FF0000"))
        cmd[3] = 0 # 0 = Channel 01
        cmd[4] = int(beep)
        cmd[5] = int(light)
        cmd[7] = 0 # strobe mode
        cmd[8] = 1 # Hz
        cmd[9] = 1 # Times
        await self.sendCommand(self.checksum(bytearray(cmd)))

    async def setPower(self, group, mode, pwr = '1/1'):
        cmd = list(bytes.fromhex("F0A10700000000000100"))
        cmd[3] = int('0' + group, 16)
        cmd[4] = int(GodoxWorker.modes[mode])
        if mode == 'M':
            cmd[5] = power.power2godox(pwr)
        elif mode == 'T':
            cmd[5] = 0x17
            cmd[9] = power.ttl2godox(pwr)
        await self.sendCommand(self.checksum(bytearray(cmd)))

    async def sendCommand(self, command):
        if self.client and self.client.is_connected:
            await self.client.write_gatt_char(self.config['uuid'], command)

    async def stop(self):
        if self.client:
            if self.client.is_connected:
                INFO('disconnect bt')
                await self.client.disconnect()

    async def loop(self):
        while True:
            cmd, data = self.inQueue.get()
            VERBOSE(f'Command: {cmd}', data)

            if cmd == 'connect':
                self.config = data
                await self.connect()
            elif cmd == 'stop':
                await self.stop()
                return
            elif cmd == 'setValues':
                await self.setValues(data)
            elif cmd == 'setBeepAndLight':
                await self.setBeepAndLight(data[0], data[1])
            elif cmd == 'test':
                await self.test()
            else:
                ERROR('unknown command', cmd)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.loop())
        loop.close()

if __name__ == '__main__':
    pass
