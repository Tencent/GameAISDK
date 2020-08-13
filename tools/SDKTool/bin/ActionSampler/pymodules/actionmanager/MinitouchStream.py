# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

try:
  import Queue
except ImportError:
  import queue as Queue
import re
import socket
import subprocess
import threading
import time
import traceback

import numpy as np

from .MinitouchInstall import *

class MinitouchStream(object):
    def __init__(self, device):
        self.__dev = device
        self.__touch_queue = None
        self.__minitouch_process = None
        self.__socket = None
        self.__screenHeight = -1
        self.__screenWidth = -1
        self.mx = -1
        self.my = -1
        self.rotation = 0

    def __InstallMinitouch(self):
        # install minitouch
        InstallMinitouch(serialno=self.__dev.serial)

    def OpenMinitouchStream(self, port=1111):
        if self.__touch_queue is None:
            self.__touch_queue = Queue.Queue()

        # ensure minicap installed
        self.__InstallMinitouch()

        if self.__minitouch_process is not None:
            self.__minitouch_process.kill()

        self.raw_cmd('shell', 'killall', 'minitouch')

        out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minitouch',
                           stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        out = out.strip().split('\n')
        if len(out) > 1:
            idx = out[0].split().index('PID')
            pid = out[1].split()[idx]
            self.raw_cmd('shell', 'kill', '-9', pid).wait()
        else:
            out = self.raw_cmd('shell', 'ps', '-C', 'minitouch',
                               stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
            out = out.strip().split('\n')
            if len(out) > 1:
                idx = out[0].split().index('PID')
                pid = out[1].split()[idx]
                self.raw_cmd('shell', 'kill', '-9', pid).wait()

        self.__minitouch_process = self.raw_cmd('shell', '/data/local/tmp/minitouch')

        # wait for minitouch start
        time.sleep(1)

        if self.__minitouch_process.poll() is not None:
            print('start minitouch failed.')
            return

        # adb forward to tcp port
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minitouch').wait()

        # connect to minitouch server
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.__socket.connect(('127.0.0.1', port))

            headerTrunks = b''
            headerRecvdSize = 0
            headerTotalSize = 22
            while headerRecvdSize < headerTotalSize:
                assert self.__minitouch_process.poll() is None
                buf = self.__socket.recv(headerTotalSize - headerRecvdSize)
                bufSize = len(buf)
                if bufSize > 0:
                    headerTrunks += buf
                    headerRecvdSize += bufSize
            m = re.search('\^ (\d+) (\d+) (\d+) (\d+)', str(headerTrunks, 'utf-8'), re.S)
            self.__maxContacts, maxX, maxY, self.__hasMTSlot = map(int, m.groups())
            self.__screenHeight = maxX
            self.__screenWidth = maxY

        except:
            traceback.print_exc()
            self.__socket.close()
            self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        def MinitouchSend():
            try:
                while True:
                    cmd = self.__touch_queue.get() # wait here
                    if not cmd:
                        continue
                    elif cmd[-1] != '\n':
                        cmd += '\n'
                    self.__socket.send(bytes(cmd, 'utf-8'))
            except:
                traceback.print_exc()
            finally:
                self.__socket.close()
                self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        threadSend = threading.Thread(target=MinitouchSend)
        threadSend.setDaemon(True)
        threadSend.start()

    def raw_cmd(self, *args, **kwargs):
        if self.__dev is None:
            cmds = ['adb'] + list(args)
            return subprocess.Popen(cmds, **kwargs)
        else:
            return self.__dev.raw_cmd(*args, **kwargs)

    # Interface
    def Finish(self):
        beginTime = time.time()
        while not self.__touch_queue.empty():
            waitTime = time.time() - beginTime
            if waitTime > 1:
                break
            time.sleep(0.002)

    def Reset(self):
        cmds = 'r\n' \
               'c\n'
        self.__touch_queue.put(cmds)

    def Click(self, x, y, contact = 0):
        tx, ty = self._ConvertRotation(x, y)
        cmds = 'd {0} {1} {2} 50\n' \
               'c\n' \
               'w {3}\n' \
               'c\n' \
               'u {0}\n' \
               'c\n'.format(contact, int(tx), int(ty), 50)
        self.__touch_queue.put(cmds)

    def Down(self, x, y, contact = 0):
        tx, ty = self._ConvertRotation(x, y)
        cmds = 'd {0} {1} {2} 50\n' \
               'c\n'.format(contact, int(tx), int(ty))
        self.__touch_queue.put(cmds)
        self.mx = x
        self.my = y

    def Up(self, contact = 0):
        cmds = 'u {0}\n' \
               'c\n'.format(contact)
        self.__touch_queue.put(cmds)

    def Move(self, x, y, contact = 0):
        if self.mx != -1 and self.my != -1:
            beginPoint = np.array([self.mx, self.my])
            targetPoint = np.array([x, y])
            distance = np.linalg.norm(targetPoint - beginPoint)
            numMovingPoints = max(int(distance / 40.), 2)
            movingX = np.linspace(beginPoint[0], targetPoint[0], numMovingPoints).astype(int)
            movingY = np.linspace(beginPoint[1], targetPoint[1], numMovingPoints).astype(int)

            cmds = ''
            for i in range(numMovingPoints):
                tmpx, tmpy = self._ConvertRotation(movingX[i], movingY[i])
                cmds += 'm {0} {1} {2} 50\n' \
                        'c\n'.format(contact, int(tmpx), int(tmpy))
        else:
            tx, ty = self._ConvertRotation(x, y)
            cmds = 'm {0} {1} {2} 50\n' \
                   'c\n'.format(contact, int(tx), int(ty))
        self.__touch_queue.put(cmds)
        self.mx = x
        self.my = y

    def DownMoveUp(self, x, y, tx, ty, contact = 0):
        beginPoint = np.array([x, y])
        targetPoint = np.array([tx, ty])
        distance = np.linalg.norm(targetPoint - beginPoint)
        numMovingPoints = min(10, max(int(distance / 20.), 5))
        movingX = np.linspace(beginPoint[0], targetPoint[0], numMovingPoints).astype(int)
        movingY = np.linspace(beginPoint[1], targetPoint[1], numMovingPoints).astype(int)
        x, y = self._ConvertRotation(x, y)
        cmds = 'd {0} {1} {2} 50\n' \
               'c\n' \
               'w 4\n' \
               'c\n'.format(contact, int(x), int(y))
        for i in range(numMovingPoints):
            tmpx, tmpy = self._ConvertRotation(movingX[i], movingY[i])
            cmds += 'm {0} {1} {2} 50\n' \
                    'c\n' \
                    'w 4\n' \
                    'c\n'.format(contact, int(tmpx), int(tmpy))
        cmds += 'u {0}\n' \
                'c\n'.format(contact)
        self.__touch_queue.put(cmds)

    def Wait(self, waitMS):
        cmds = 'w {0}\n' \
               'c\n'.format(waitMS)
        self.__touch_queue.put(cmds)

    def GetScreenResolution(self):
        return self.__screenHeight+1, self.__screenWidth+1

    def ChangeRotation(self, rotation):
        self.rotation = rotation
        print('ChangeRotation: {0}'.format(rotation))

    def _ConvertRotation(self, px, py):
        if self.rotation == 3 or self.rotation == 2:
            newPx = self.__screenHeight - px
            newPy = self.__screenWidth - py
            return newPx, newPy
        else:
            return px, py

    def IsTypeA(self):
        if self.__hasMTSlot:
            return False
        return True

    def GetMaxContacts(self):
        return self.__maxContacts
