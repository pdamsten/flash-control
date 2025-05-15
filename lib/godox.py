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

from bleak import BleakScanner
from bleak import BleakClient
import PyObjCTools
from crccheck.crc import Crc8Maxim
from threading import Thread
from threading import Timer
from queue import Queue
import asyncio

class Godox:
    def __init__(self):
        self.callbacks = {}
        self.fromWorkerQueue = Queue()
        self.toWorkerQueue = Queue()
        self.quit = False
        self.worker = None

    def callback(self, name, callback):
        self.callbacks[name] = callback

    def connect(self, cfg):
        self.worker = GodoxWorker(self.toWorkerQueue, self.fromWorkerQueue)
        self.worker.start()
        self.sendMsg('connect', cfg)
        Timer(0.5, self.poll).start()

    def close(self):
        self.quit = True
        self.sendMsg('stop')
        if self.worker:
            self.worker.join()
            self.worker = None

    def setValues(self, values):
        self.sendMsg('setValues', values)

    def sendMsg(self, cmd, data = None):
        if self.worker:
            self.toWorkerQueue.put((cmd, data))

    def poll(self):
        msg = self.fromWorkerQueue.get()

        if msg[0] in self.callbacks:
            self.callbacks[msg[0]](msg[1])

        if not self.quit:
            Timer(1.0, self.poll).start()

class GodoxWorker(Thread):
    modes = {'-': 3, 'T': 0, 'M': 1}
    fractions = [2 ** n for n in range(9)]

    def __init__(self, inQueue, outQueue):
        super().__init__()
        self.config = {}
        self.inQueue = inQueue
        self.outQueue = outQueue
        self.client = None
    
    def sendMsg(self, cmd, data = None):
        if self.outQueue:
            self.outQueue.put((cmd, data))

    @staticmethod
    def fraction2godox(s):
        l = s.replace('1/', '').split('+')
        if len(l) > 1:
            try:
                b = float(l[1])
            except:
                b = 0.0
            b = b if b < 1.0 else b / 10.0
            b = int(max(min(0.9, b), 0.0) * 10)
        else:
            b = 0
        try:
            an = int(l[0])
        except:
            an = 1
        a = min(range(len(Godox.fractions)), key = lambda n : abs(Godox.fractions[n] - an))
        res = max(a * 10 - b, 0)
        print(' =>', s, '=', res)
        return res

    async def scan(self):
        print('scanning...')
        devices = await BleakScanner.discover()
        godox = None
        for device in devices:
            name = str(PyObjCTools.KeyValueCoding.getKey(device.details, 'name')[0])
            if name.startswith('GDBH'):
                print('Godox found:', name)
                godox = device
                break
        uuid = None
        if godox:
            address = str(PyObjCTools.KeyValueCoding.getKey(godox.details, 'identifier')[0])
            print('address:', address)
            async with BleakClient(address) as client:
                for service in client.services:
                    pre = '**' if service.description.startswith('KDDI') else ' ' * 2
                    print(pre, service.description, service.handle)
                    for ch in service.characteristics:
                        pre = '  **' if ch.uuid.startswith('0000fec7') else ' ' * 4
                        print(pre, ch.handle, ch.uuid)
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
            self.sendMsg('failed', self.config['name'])
            return False

    async def connect(self):
        tries = 0
        while tries < 2:
            if self.client and self.client.is_connected:
                print('already connected')
                return True

            if 'address' in self.config:
                if not self.client:
                    self.client = BleakClient(self.config['address'])
                    print('new client')
                try:
                    await self.client.connect()
                    self.sendMsg('connected')
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
        cmd = bytes.fromhex("37353035362C54657374")
        await self.sendCommand(cmd)

    async def setValues(self, values):
        pass

    async def setModellingLight(self, godox, on = True, group = None):
        cmd = list(bytes.fromhex("F0A00AFF000003000404FF0000"))
        cmd[5] = int(on)
        #cmd[6] = int('0' + group, 16)
        await self.sendCommand(self.checksum(bytearray(cmd)))

    async def setPower(self, group, mode, power = '1/1'):
        print(group, mode, power)
        cmd = list(bytes.fromhex("F0A10700000000000100"))
        cmd[3] = int('0' + group, 16)
        cmd[4] = int(Godox.modes[mode])
        if mode == 'M':
            cmd[5] = Godox.fraction2godox(power)
        elif mode == 'T':
            cmd[5] = 0x17
            cmd[9] = power
        await self.sendCommand(self.checksum(bytearray(cmd)))

    async def sendCommand(self, command):
        if await self.connect():
            #print(self.uuid, ''.join('{:02x}'.format(x) for x in command))
            await self.client.write_gatt_char(self.uuid, command)

    async def stop(self):
        if self.client:
            if self.client.is_connected:
                print('disconnect bt')
                await self.client.disconnect()

    async def loop(self):
        while True:
            cmd, data = self.inQueue.get()

            if cmd == 'connect':
                print('connect')
                self.config = data
                await self.connect(data)
            elif cmd == 'stop':
                print('stop')
                await self.stop()
                return
            elif cmd == 'setValues':
                print('setValues', data)
                await self.setValues(data)
            else:
                print('unknown command', cmd)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.loop())
        loop.close()

if __name__ == '__main__':
    pass
