# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import threading

import actionsampler.ADBEventParser as ADBEventParser
from actionmanager.TouchMinitouch import TouchMinitouch
from actionsampler.ADBEventParser import TouchPoint
from adbkit.ADBClient import ADBClient
from screen.ScreenMinicap import ScreenMinicap

SCREEN_ORI_LANDSCAPE = 0
SCREEN_ORI_PORTRAIT = 1

LOG = logging.getLogger('ActionSampler')


class ADBTouchSampler(object):
    def __init__(self):
        adb = ADBClient()
        self.__device = adb.device()
        self.__screen = ScreenMinicap(self.__device)
        self.__touch = TouchMinitouch(self.__device)
        maxContacts = self.__touch.GetMaxContacts()
        if self.__touch.IsTypeA():
            LOG.info('This is Type A device')
            self.__parser = ADBEventParser.ADBEventParserTypeA(maxContacts)
        else:
            LOG.info('This is Type B device')
            self.__parser = ADBEventParser.ADBEventParserTypeB(maxContacts)
        self.__rotation = SCREEN_ORI_LANDSCAPE
        self.__touchXMax = None
        self.__touchYMax = None

    def Init(self, captureHeight, captureWidth):
        self.__screenCaptureHeight = captureHeight
        self.__screenCaptureWidth = captureWidth
        self.__screen.Initialize(self.__screenCaptureHeight, self.__screenCaptureWidth)
        self.__touchXMax, self.__touchYMax = self.__touch.GetScreenResolution()

        if self.__screenCaptureHeight > self.__screenCaptureWidth:
            self.__rotation = SCREEN_ORI_PORTRAIT
        else:
            self.__rotation = SCREEN_ORI_LANDSCAPE

        p = self.__device.raw_cmd('shell', '-x', 'getevent', '-l')

        # 启动一个线程去实时解析adb shell getevent返回的结果
        def PullThreadMain():
            while True:
                line = p.stdout.readline().strip()
                if not line:
                    continue
                else:
                    self.__parser.Parse(line)

        t = threading.Thread(target=PullThreadMain)
        t.setDaemon(True)
        t.start()

    def GetSample(self):
        frame = self.__screen.GetScreen()
        retPoints = []
        points = self.__parser.GetTouchPoints()

        # 对points结果进行坐标转换到截图frame的坐标系下
        for p in points:
            if p is None:
                continue
            else:
                if p.x is None or p.y is None:
                    continue
                else:
                    if self.__rotation == SCREEN_ORI_PORTRAIT:
                        x = int(p.x / self.__touchXMax * self.__screenCaptureWidth)
                        y = int(p.y / self.__touchYMax * self.__screenCaptureHeight)
                    else:
                        x = int(p.y / self.__touchYMax * self.__screenCaptureWidth)
                        y = int(self.__screenCaptureHeight - p.x / self.__touchXMax * self.__screenCaptureHeight)

                    retPoints.append(TouchPoint(p.trackingId, x, y))
        return frame, retPoints
