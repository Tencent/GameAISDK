# -*- coding: utf-8 -*-

import os
try:
  import Queue
except ImportError:
  import queue as Queue

import re
import socket
import struct
import subprocess
import threading
import time
import traceback
import logging
import cv2
import numpy as np
from .MinicapInstall import *

SCREEN_ORI_LANDSCAPE = 0
SCREEN_ORI_PORTRAIT = 1

PULL_LOOP_RATE = 100
PULL_LOOP_SLEEP_TIME = 1./PULL_LOOP_RATE
DECODE_LOOP_RATE = 100
DECODE_LOOP_SLEEP_TIME = 1./DECODE_LOOP_RATE

LOG = logging.getLogger('minicap')

def str2img(jpgstr, orientation=None):
    arr = np.fromstring(jpgstr, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if orientation == 1:
        return cv2.flip(cv2.transpose(img), 0) # counter-clockwise
    if orientation == 3:
        return cv2.flip(cv2.transpose(img), 1) # clockwise
    return img

class MinicapStream(object):
    def __init__(self, device, isShow):
        self.__dev = device
        self.__isShow = isShow
        self.__screen = None
        self.__minicap_process = None

        self.__frameCount = 0

        self.__originalWidth = -1
        self.__originalHeight = -1
        self.__captureWidth = -1
        self.__captureHeight = -1
        self.__orient = SCREEN_ORI_PORTRAIT
        # ensure minicap installed
        self.__InstallMinicap()

    def __InstallMinicap(self):
        if self.__dev is None:
            InstallMinicap()
        else:
            InstallMinicap(serialno=self.__dev.serial)

    def OpenMinicapStream(self, capHeight=360, capWidth=640, port=1313):
        if capHeight < capWidth:
            self.__orient = SCREEN_ORI_LANDSCAPE
        else:
            self.__orient = SCREEN_ORI_PORTRAIT

        # kill previous minicap process
        if self.__minicap_process is not None:
            self.__minicap_process.kill()

        self.raw_cmd('shell', 'killall', 'minicap')

        # if minicap is already started, kill it first.
        out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minicap',
                           stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        out = out.strip().split('\n')
        if len(out) > 1:
            idx = out[0].split().index('PID')
            pid = out[1].split()[idx]
            LOG.warning('minicap is running, killing {0}'.format(pid))
            self.raw_cmd('shell', 'kill', '-9', pid).wait()
        else:
            out = self.raw_cmd('shell', 'ps', '-C', 'minicap',
                               stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
            out = out.strip().split('\n')
            if len(out) > 1:
                idx = out[0].split().index('PID')
                pid = out[1].split()[idx]
                LOG.warning('minicap is running, killing {0}'.format(pid))
                self.raw_cmd('shell', 'kill', '-9', pid).wait()

        # start minicap with -i to get information, such as screen width, height, rotation ...
        out = self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp',
                           '/data/local/tmp/minicap', '-i',
                           stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())

        # assume height < width
        self.__originalHeight, self.__originalWidth = min(w, h), max(w, h)

        # create minicap params
        if self.__orient == SCREEN_ORI_LANDSCAPE:
            params = '{x}x{y}@{cx}x{cy}/{r}'.format(x=self.__originalHeight, y=self.__originalWidth,
                                                    cx=capHeight, cy=capWidth, r=r)
        else:
            params = '{x}x{y}@{cx}x{cy}/{r}'.format(x=self.__originalHeight, y=self.__originalWidth,
                                                    cx=capWidth, cy=capHeight, r=r)

        # start minicap cmd
        p = self.raw_cmd('shell',
                         'LD_LIBRARY_PATH=/data/local/tmp',
                         '/data/local/tmp/minicap',
                         '-P',
                         '%s' % params,
                         '-S',
                         stdout=subprocess.PIPE)
        self.__minicap_process = p
        # wait for minicap start
        time.sleep(1)

        if p.poll() is not None:
            LOG.error('start minicap failed.')
            return

        # adb forward to tcp port
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minicap').wait()

        # data recv buffer
        recvQueue = Queue.Queue()

        # pull data from socket
        def _pull():
            LOG.debug('start pull {0} {1}'.format(p.pid,
                                                  p.poll()))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                assert p.poll() is None
                s.connect(('127.0.0.1', port))

                # pull banner message
                t = s.recv(24)
                version, bannerSize, _, self.__originalHeight, self.__originalWidth,\
                self.__captureHeight, self.__captureWidth, ori, quirk = struct.unpack('<2B5I2B', t)
                LOG.info('minicap connected version[{0}],'
                         'realResolution[{1}x{2}] ,'
                         'capResolution[{3}x{4}] ,'
                         'ori:[{5}] ,'
                         'quirk:[{6}]'.format(version, self.__originalHeight,
                                              self.__originalWidth, self.__captureHeight,
                                              self.__captureWidth, ori, quirk))

                # pull data message
                while True:
                    # print timestamp
                    if PULL_LOOP_RATE > 0:
                        time.sleep(PULL_LOOP_SLEEP_TIME)
                    # Read header, 4 bytes
                    headerTrunks = []
                    headerRecvdSize = 0
                    headerTotalSize = 4
                    while headerRecvdSize < headerTotalSize:
                        assert p.poll() is None
                        buf = s.recv(headerTotalSize - headerRecvdSize)
                        bufSize = len(buf)
                        LOG.debug('recv size {0}'.format(bufSize))
                        if bufSize > 0:
                            headerTrunks.append(buf)
                            headerRecvdSize += bufSize
                    headerBuf = b''.join(headerTrunks)

                    # Parse the header
                    bodySize = struct.unpack("<I", headerBuf)[0]
                    LOG.debug('frame body size {0}'.format(bodySize))

                    # Read body
                    bodyTrunks = []
                    bodyRecvdSize = 0
                    while bodyRecvdSize < bodySize:
                        assert p.poll() is None
                        readSize = min(8192, bodySize-bodyRecvdSize)
                        buf = s.recv(readSize)
                        bufSize = len(buf)
                        if bufSize > 0:
                            bodyTrunks.append(buf)
                            bodyRecvdSize += bufSize
                    # Put the img data to recv queue
                    recvQueue.put(b''.join(bodyTrunks))
            except Exception as e:
                # if not isinstance(e, struct.error):
                #     traceback.print_exc()
                if p.poll() is not None: # subprocess has exit!
                    LOG.debug('pull thread exit.')
                    LOG.debug('{0}'.format(p.stdout.read()))
                else:
                    LOG.error('Stoping minicap ...')
                    p.kill()
            finally:
                s.close()
                # self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        # start pull(recv) thread
        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        out = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk',
                           stdout=subprocess.PIPE).communicate()[0]
        sdk = int(out.strip())
        orientation = r/90

        # start decode thread
        def _decode():
            while True:
                try:
                    if DECODE_LOOP_RATE > 0:
                        time.sleep(DECODE_LOOP_SLEEP_TIME)
                    frame = recvQueue.get_nowait()
                    for i in range(recvQueue.qsize()):
                        frame = recvQueue.get_nowait()
                    img = None
                    if self.__orient == SCREEN_ORI_LANDSCAPE:
                        if orientation == 0:
                            img = str2img(frame, 1)
                        else:
                            img = str2img(frame)
                    elif self.__orient == SCREEN_ORI_PORTRAIT:
                        if orientation == 1:
                            img = str2img(frame, 3)
                        else:
                            img = str2img(frame)
                    if img is not None:
                        self.__screen = img
                        self.__frameCount += 1
                        # if self.__isShow:
                        #     cv2.imshow('screen', self.__screen)
                        #     cv2.waitKey(1)
                except Queue.Empty:
                    if p.poll() is not None:
                        LOG.debug('decode thread exit.')
                        LOG.debug('{0}'.format(p.stdout.read()))
                        break
                    continue
                except:
                    traceback.print_exc()

        t = threading.Thread(target=_decode)
        t.setDaemon(True)
        t.start()

        if self.__isShow:
            def _screenShow():
                while True:
                    if self.__screen is not None:
                        cv2.imshow('screen', self.__screen)
                        cv2.waitKey(1)

            t = threading.Thread(target=_screenShow)
            t.setDaemon(True)
            t.start()
            self.__isShow = False

    def raw_cmd(self, *args, **kwargs):
        if self.__dev is None:
            cmds = ['adb'] + list(args)
            LOG.debug('cmds:{0}'.format(cmds))
            return subprocess.Popen(cmds, **kwargs)
        else:
            return self.__dev.raw_cmd(*args, **kwargs)

    def GetScreen(self):
        return self.__screen

    def frame_count(self):
        return self.__frameCount

    def clear_frame_count(self):
        self.__frameCount = 0

    def GetOriginalResolution(self):
        return self.__originalHeight, self.__originalWidth

    def GetCaptureResolution(self):
        return self.__captureHeight, self.__captureWidth
