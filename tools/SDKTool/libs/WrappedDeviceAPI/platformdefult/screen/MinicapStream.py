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
import shutil
import tempfile
import threading
import time
import traceback
import math
import logging
import cv2
import numpy as np

from APIDefine import *

SCREEN_ORI_LANDSCAPE = 0
SCREEN_ORI_PORTRAIT = 1

PULL_LOOP_RATE = 500
PULL_LOOP_SLEEP_TIME = 1./PULL_LOOP_RATE
DECODE_LOOP_RATE = 500
DECODE_LOOP_SLEEP_TIME = 1./DECODE_LOOP_RATE

__dir__ = os.path.dirname(os.path.abspath(__file__))
MINICAP_BASE_DIR = __dir__ + '/../vendor/minicap/'

# self.__logger = logging.getLogger('deviceapi')

def str2img(jpgstr, orientation=None):
    arr = np.fromstring(jpgstr, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if orientation == 1:
        return cv2.flip(cv2.transpose(img), 0) # counter-clockwise
    if orientation == 3:
        return cv2.flip(cv2.transpose(img), 1) # clockwise
    return img

class MinicapStream(object):
    def __init__(self, device=None, isShow=False, serial=None):
        if serial is None:
            self.logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.logger = logging.getLogger(serial)
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
        # if self.__dev is None:
        #     InstallMinicap()
        # else:
        #     InstallMinicap(serialno=self.__dev.serial)
        self.logger.info("Minicap install started!")

        # adb = functools.partial(run_adb, serialno=serialno, host=host, port=port)

        self.logger.info("Make temp dir ...")
        tmpdir = tempfile.mkdtemp(prefix='ins-minicap-')
        self.logger.debug(tmpdir)
        try:
            # Get device abi and sdk version
            self.logger.info("Retrive device information ...")
            abi = self.raw_cmd('shell', 'getprop', 'ro.product.cpu.abi').communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n').strip()
            sdk = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk').communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n').strip()
    
            # push minicap so file
            target_path = MINICAP_BASE_DIR + "jni/minicap-shared/aosp/libs/android-" \
                          + sdk + "/" + abi + "/minicap.so"
            self.logger.info("Push minicap.so to device ....")
            self.raw_cmd('push', target_path, '/data/local/tmp').communicate()
    
            # push minicap shell file
            target_path = MINICAP_BASE_DIR + "libs/" + abi + "/minicap"
            self.logger.info("Push minicap to device ....")
            self.raw_cmd('push', target_path, '/data/local/tmp').communicate()
            # self.raw_cmd('shell', 'chmod', '0755', '/data/local/tmp/minicap')
            self.raw_cmd('shell', 'chmod', '0755', '/data/local/tmp/minicap').communicate()
    
            # check minicap run normally
            self.logger.info("Checking [dump device info] ...")
            # print adb('shell', 'LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -i')
            self.logger.info("Minicap install finished !")

        except Exception as e:
            self.logger.error('error: %s', e)
        finally:
            if tmpdir:
                self.logger.info("Cleaning temp dir")
                shutil.rmtree(tmpdir)
                
    def GetVMSize(self):
        return self.__originalHeight, self.__originalWidth
    
    def GetScreenSize(self):
        return self.__screenHeight, self.__screenWidth
    
    def InitVMSize(self, capHeight=360, capWidth=640):
        if capHeight < capWidth:
            self.__orient = SCREEN_ORI_LANDSCAPE
        else:
            self.__orient = SCREEN_ORI_PORTRAIT

        # time.sleep(1)
        out = self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp',
                           '/data/local/tmp/minicap', '-i',
                           stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        self.logger.info('out value:{0}'.format(out))
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())
    
        # assume height < width
        self.__originalHeight, self.__originalWidth = min(w, h), max(w, h)
        
        if self.__orient == SCREEN_ORI_LANDSCAPE:
            scale = capWidth / self.__originalWidth
            capHeight = math.ceil(self.__originalHeight * scale)
        else:
            scale = capHeight / self.__originalWidth
            capWidth = math.ceil(self.__originalHeight * scale)

        self.__screenHeight = capHeight
        self.__screenWidth = capWidth

    def OpenMinicapStream(self, capHeight=360, capWidth=640, port=None):
        # kill previous minicap process
        try:
            if self.__minicap_process is not None:
                self.__minicap_process.kill()
            self.raw_cmd('shell', 'killall', 'minicap')
            self.logger.info('OpenMinicapStream')
            # if minicap is already started, kill it first.
            out = self.raw_cmd('shell', 'ps', '-C', '/data/local/tmp/minicap',
                               stdout=subprocess.PIPE).communicate(timeout=5)[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
            self.logger.info('OpenMinicapStream')
            out = out.strip().split('\n')
            if len(out) > 1:
                idx = out[0].split().index('PID')
                pid = out[1].split()[idx]
                self.logger.warning('minicap is running, killing {0}'.format(pid))
                self.raw_cmd('shell', 'kill', '-9', pid).wait()
                self.logger.info('OpenMinicapStream')
            else:
                out = self.raw_cmd('shell', 'ps', '-C', 'minicap',
                                   stdout=subprocess.PIPE).communicate(timeout=5)[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
                self.logger.info('OpenMinicapStream')
                out = out.strip().split('\n')
                if len(out) > 1:
                    idx = out[0].split().index('PID')
                    pid = out[1].split()[idx]
                    self.logger.warning('minicap is running, killing {0}'.format(pid))
                    self.raw_cmd('shell', 'kill', '-9', pid).wait()
        except Exception as e:
            self.logger.warning(e)

        # start minicap with -i to get information, such as screen width, height, rotation ...
        out = self.raw_cmd('shell', 'LD_LIBRARY_PATH=/data/local/tmp',
                           '/data/local/tmp/minicap', '-i',
                           stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        self.logger.info('OpenMinicapStream')
        m = re.search('"width": (\d+).*"height": (\d+).*"rotation": (\d+)', out, re.S)
        w, h, r = map(int, m.groups())

        # create minicap params
        if self.__orient == SCREEN_ORI_LANDSCAPE:
            scale = capWidth / self.__originalWidth
            capHeight = math.ceil(self.__originalHeight * scale)
            # if (capWidth > self.__originalWidth):
            #     capWidth = 1920
            #     capHeight = 1080
            params = '{x}x{y}@{cx}x{cy}/{r}'.format(x=self.__originalHeight, y=self.__originalWidth,
                                                    cx=capHeight, cy=capWidth, r=r)
        else:
            scale = capHeight / self.__originalWidth
            capWidth = math.ceil(self.__originalHeight * scale)
            # if (capHeight > self.__screenHeight):
            #     capWidth = self.__originalWidth
            #     capHeight = self.__originalHeight
            params = '{x}x{y}@{cx}x{cy}/{r}'.format(x=self.__originalHeight, y=self.__originalWidth,
                                                    cx=capWidth, cy=capHeight, r=r)
        self.logger.info('OpenMinicapStream')
        # start minicap cmd
        p = self.raw_cmd('shell',
                         'LD_LIBRARY_PATH=/data/local/tmp',
                         '/data/local/tmp/minicap',
                         '-P',
                         '%s' % params,
                         '-S',
                         stdout=subprocess.PIPE)
        self.logger.info('OpenMinicapStream')
        self.__minicap_process = p
        # wait for minicap start
        time.sleep(1)

        if p.poll() is not None:
            self.logger.error('start minicap failed.')
            return

        # adb forward to tcp port
        self.raw_cmd('forward', 'tcp:%s' % port, 'localabstract:minicap').wait()
        self.logger.info('OpenMinicapStream')
        # data recv buffer
        recvQueue = Queue.Queue()

        # pull data from socket
        def _pull():
            self.logger.info('start pull {0} {1}'.format(p.pid,
                                                  p.poll()))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                self.logger.info('try poll')
                assert p.poll() is None
                s.connect(('127.0.0.1', port))

                # pull banner message
                t = s.recv(24)
                version, bannerSize, _, self.__originalHeight, self.__originalWidth,\
                self.__captureHeight, self.__captureWidth, ori, quirk = struct.unpack('<2B5I2B', t)
                self.logger.info('minicap connected version[{0}],'
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
                        self.logger.debug('recv size {0}'.format(bufSize))
                        if bufSize > 0:
                            headerTrunks.append(buf)
                            headerRecvdSize += bufSize
                    headerBuf = b''.join(headerTrunks)

                    # Parse the header
                    bodySize = struct.unpack("<I", headerBuf)[0]
                    self.logger.debug('frame body size {0}'.format(bodySize))

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
                self.logger.info('exception')
                if p.poll() is not None: # subprocess has exit!
                    self.logger.error('pull thread exit.')
                    self.logger.error('{0}'.format(p.stdout.read()))
                    exceptionQueue.put('pull thread exit.')
                else:
                    self.logger.error('Stoping minicap ...')
                    exceptionQueue.put('Stoping minicap ...')
                    p.kill()
                self.__screen = None
            finally:
                self.logger.info('exit thread')
                s.close()
                # self.raw_cmd('forward', '--remove', 'tcp:%s' % port).wait()

        # start pull(recv) thread
        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        out = self.raw_cmd('shell', 'getprop', 'ro.build.version.sdk',
                           stdout=subprocess.PIPE).communicate()[0]
        self.logger.info('OpenMinicapStream')
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
                        self.logger.debug('decode thread exit.')
                        self.logger.debug('{0}'.format(p.stdout.read()))
                        exceptionQueue.put('decode thread exit.')
                        self.__screen = None
                        break
                    continue
                except:
                    exceptionQueue.put('decode thread exit.')
                    self.__screen = None
                    traceback.print_exc()

        t = threading.Thread(target=_decode)
        t.setDaemon(True)
        t.start()
        self.logger.info('OpenMinicapStream')

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
        self.logger.info('OpenMinicapStream')

    def raw_cmd(self, *args, **kwargs):
        if self.__dev is None:
            cmds = ['adb'] + list(args)
            self.logger.debug('cmds:{0}'.format(cmds))
            kwargs['stdout'] = kwargs.get('stdout', subprocess.PIPE)
            kwargs['stderr'] = kwargs.get('stderr', subprocess.PIPE)
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
