# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import queue
import re
import socket
import subprocess
import threading
import time
import traceback
import shutil
import tempfile
# from WrappedDeviceAPI.devicePlatform.IPlatformProxy import IPlatformProxy, DeviceInfo
from platformdefult.screen.ScreenMinicap import ScreenMinicap

from APIDefine import *
# from .MinitouchInstall import *
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINITOUCH_BASE_DIR = parentdir + '/vendor/minitouch/'

class MinitouchAction():
    def __init__(self):
        # self.__dev = device
        self.__touch_queue = None
        self.__minitouch_process = None
        self.__socket = None
        self.__screenHeight = -1
        self.__screenWidth = -1
        self.__maxContacts = -1
        self.__convertRate = 1.
        self.rotation = 0
        self.__configOri = UI_SCREEN_ORI_LANDSCAPE
        self.__currentScreenFrame = None
        
    def init(self, serial=None, device=None, width=None, height=None, showscreen=True, minitouchPort=None):
        self.__minitouchPort = minitouchPort
        if serial is None:
            self.__logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.__logger = logging.getLogger(serial)
        if device is None:
            self.__logger.error('there is no device')
            return False
        self.__dev = device
        self._OpenMinitouchStream()

        # self.__screenMinicap = ScreenMinicap(device, showscreen)
        # if not self.__screenMinicap.Initialize(height, width):
        #     self.__logger.error('Screen Minicap Initialize failed!')
        #     return False
        
        # self.__deviceInfo.display_height = height
        # self.__deviceInfo.display_width = width
        # self.__deviceInfo.touch_height = height
        # self.__deviceInfo.touch_width = width
        
        
        
        if width > height:
            self.__configOri = UI_SCREEN_ORI_LANDSCAPE
        else:
            self.__configOri = UI_SCREEN_ORI_PORTRAIT

        if height > width:
            height, width = width, height

        if self.__screenHeight > self.__screenWidth:
            self.__deviceHeightScale = float(self.__screenHeight) / width
            self.__deviceWidthScale = float(self.__screenWidth) / height
            self.__convertRate = float(self.__screenHeight) / float(self.__screenWidth)
        else:
            self.__deviceHeightScale = float(self.__screenHeight) / height
            self.__deviceWidthScale = float(self.__screenWidth) / width
        
        return True
    
    # def get_image(self):
    #     screenFrame = self.__screenMinicap.GetScreen()
    #     if screenFrame is not None:
    #         self.__currentScreenFrame = screenFrame
    #
    #     return self.__currentScreenFrame
    
    def touch_up(self, contact=0):
        cmds = 'u {0}\n' \
               'c\n'.format(contact)
        self.__touch_queue.put(cmds)
        self.__contactPoints[contact] = None

    def touch_down(self, px, py, contact=0, pressure=50):
        px, py = self._ConvertCoordinates(px, py)
        tx, ty = self._ConvertRotation(px, py)
        self.__logger.info("touch_down: {}, {}".format(tx, ty))
        cmds = 'd {0} {1} {2} 50\n' \
               'c\n'.format(contact, int(tx), int(ty))
        self.__touch_queue.put(cmds)
        self.__contactPoints[contact] = (px, py)

    def touch_move(self, px, py, contact=0, pressure=50):
        px, py = self._ConvertCoordinates(px, py)
        tx, ty = self._ConvertRotation(px, py)
        self.__logger.info("touch_move: {}, {}".format(tx, ty))
        cmds = 'm {0} {1} {2} 50\n' \
               'c\n'.format(contact, int(tx), int(ty))
        self.__touch_queue.put(cmds)
        self.__contactPoints[contact] = (px, py)

    def touch_wait(self, waitMS):
        cmds = 'w {0}\n' \
               'c\n'.format(waitMS)
        self.__logger.info("touch_wait: {}".format(waitMS))
        self.__touch_queue.put(cmds)

    def touch_reset(self):
        cmds = ''
        for contact in range(self.__maxContacts):
            cmds += 'u {0}\n'.format(contact)
        cmds += 'r\nc\n'
        self.__touch_queue.put(cmds)
        self.__contactPoints = [None] * self.__maxContacts
        
    def GetMaxContacts(self):
        return self.__maxContacts
    
    def GetVMSize(self):
        return self.__screenWidth, self.__screenHeight
        
    def touch_finish(self):
        self.touch_reset()
        beginTime = time.time()
        while not self.__touch_queue.empty():
            waitTime = time.time() - beginTime
            if waitTime > 1:
                break
            time.sleep(0.002)

    # def get_device_info(self):
    #     return self.__deviceInfo
    
    # def GetScreenResolution(self):
    #     return self.__screenHeight + 1, self.__screenWidth + 1
    
    # def GetMaxContact(self):
    #     return self.__maxContacts

    def IsTypeA(self):
        if self.__hasMTSlot:
            return False
        return True
    
    def ChangeRotation(self, rotation):
        self.rotation = rotation
        self.__logger.info('ChangeRotation: {0}'.format(rotation))
        
    def _OpenMinitouchStream(self):
        if self.__touch_queue is None:
            self.__touch_queue = queue.Queue()

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
        self.raw_cmd('forward', 'tcp:%s' % self.__minitouchPort, 'localabstract:minitouch').wait()

        # connect to minitouch server
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.__socket.connect(('127.0.0.1', self.__minitouchPort))

            headerTrunks = b''
            headerRecvdSize = 0
            headerTotalSize = 20
            while headerRecvdSize < headerTotalSize:
                assert self.__minitouch_process.poll() is None
                buf = self.__socket.recv(headerTotalSize - headerRecvdSize)
                bufSize = len(buf)
                if bufSize > 0:
                    headerTrunks += buf
                    headerRecvdSize += bufSize
            m = re.search('\^ (\d+) (\d+) (\d+) (\d+)', str(headerTrunks, 'utf-8'), re.S)
            self.__maxContacts, maxX, maxY, self.__hasMTSlot = map(int, m.groups())
            # self.__deviceInfo.touch_slot_number = self.__maxContacts
            self.__contactPoints = [None] * self.__maxContacts
            self.__screenHeight = maxX
            self.__screenWidth = maxY

        except:
            traceback.print_exc()
            self.__socket.close()
            self.raw_cmd('forward', '--remove', 'tcp:%s' % self.__minitouchPort).wait()

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
                self.raw_cmd('forward', '--remove', 'tcp:%s' % self.__minitouchPort).wait()

        threadSend = threading.Thread(target=MinitouchSend)
        threadSend.setDaemon(True)
        threadSend.start()
        
    def raw_cmd(self, *args, **kwargs):
        if self.__dev is None:
            cmds = ['adb'] + list(args)
            return subprocess.Popen(cmds, **kwargs)
        else:
            return self.__dev.raw_cmd(*args, **kwargs)

    def __InstallMinitouch(self):
        # install minitouch
        # InstallMinitouch(self.__dev)
        self.__logger.info("Minitouch install started!")
    
        # adb = functools.partial(run_adb, device=device, host=host, port=port)
    
        self.__logger.info("Make temp dir ...")
        tmpdir = tempfile.mkdtemp(prefix='ins-minitouch-')
        self.__logger.debug(tmpdir)
        try:
            # Get device abi and sdk version
            self.__logger.info("Retrive device information ...")
            abi = self.__dev.raw_cmd('shell', 'getprop', 'ro.product.cpu.abi').communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n').strip()
            # sdk = adb('shell', 'getprop', 'ro.build.version.sdk').strip()
        
            # push minitouch so file
            target_path = MINITOUCH_BASE_DIR + "libs/" + abi + "/minitouch"
            self.__logger.info("Push minitouch to device ....")
            self.__dev.raw_cmd('push', target_path, '/data/local/tmp').communicate()
            self.__dev.raw_cmd('shell', 'chmod', '0755', '/data/local/tmp/minitouch').communicate()
        
            self.__logger.info("Checking [dump device info] ...")
            # print adb('shell', '/data/local/tmp/minitouch -h')
            self.__logger.info("Minitouch install finished !")
    
        except Exception as e:
            self.__logger.error('error: %s', e)
        finally:
            if tmpdir:
                self.__logger.info("Cleaning temp dir")
                shutil.rmtree(tmpdir)
                
    def _ConvertRotation(self, px, py):
        if self.rotation == 3 or self.rotation == 2:
            newPx = self.__screenHeight - px
            newPy = self.__screenWidth - py
            return newPx, newPy
        else:
            return px, py
        
    def _ConvertCoordinates(self, px, py):
        if self.__configOri == UI_SCREEN_ORI_LANDSCAPE:
            nx = self.__screenHeight - py * self.__deviceHeightScale * self.__convertRate
            ny = px * self.__deviceWidthScale / self.__convertRate
        else:
            nx = px * self.__deviceHeightScale
            ny = py * self.__deviceWidthScale
        return int(nx), int(ny)


