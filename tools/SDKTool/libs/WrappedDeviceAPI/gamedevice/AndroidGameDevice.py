# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import logging
import logging.config

from APIDefine import *
from .AbstractGameDevice import AbstractGameDevice
from devicePlatform.WrappedPlatform import PlatformWrapper

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

# self.__logger = logging.getLogger('DeviceAPI')

WINDOW_DUMP_PATH = 'window_dump.xml'




class AndroidGameDevice(AbstractGameDevice):
    def __init__(self, moduleName=None):
        AbstractGameDevice.__init__(self)
        self.__moduleName = moduleName

    def Initialize(self, deviceSerial, isPortrait, long_edge, kwargs):
        if deviceSerial is None:
            self.__logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.__logger = logging.getLogger(deviceSerial)
        self.__logger.info('Android deviceID is {0}'.format(deviceSerial))
        self.__platformWrapper = PlatformWrapper(self.__moduleName)
        if not self.__platformWrapper.Initialize(deviceSerial, isPortrait, long_edge, kwargs):
            self.__logger.error('action init failed')
            return False

        return True

    def DeInitialize(self):
        return self.__platformWrapper.DeInitialize()

    def Finish(self):
        self.__platformWrapper.Finish()

    def GetFrame(self):
        return self.__platformWrapper.GetFrame()

    def InstallAPP(self, APKPath):
        return self.__platformWrapper.InstallAPP(APKPath)

    def LaunchAPP(self, PackageName, ActivityName):
        self.__platformWrapper.LauchAPP(PackageName, ActivityName)

    def ExitAPP(self, PackageName):
        self.__platformWrapper.ExitAPP(PackageName)
        
    def Click(self, px, py, contact=0, durationMS=-1, wait_time=0):
        # px, py = self._ConvertCoordinates(px, py)
        self.__platformWrapper.Click(px, py, contact=contact, durationMS=durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Down(self, px, py, contact=0, wait_time=0):
        # px, py = self._ConvertCoordinates(px, py)
        self.__platformWrapper.Down(px, py, contact=contact)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Up(self, contact=0, wait_time=0):
        self.__platformWrapper.Up(contact=contact)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)
        
    def SwipeMove(self, px, py, contact=0, durationMS = 50, wait_time=0):
        self.__platformWrapper.SwipeMove(px, py, contact=contact, durationMS = durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Swipe(self, sx, sy, ex, ey, contact=0, durationMS=50, needUp=True, wait_time=0):
        # sx, sy = self._ConvertCoordinates(sx, sy)
        # ex, ey = self._ConvertCoordinates(ex, ey)
        if needUp:
            self.__platformWrapper.SwipeDownMoveUp(sx, sy, ex, ey, contact=contact, durationMS=durationMS)
        else:
            self.__platformWrapper.SwipeDownMove(sx, sy, ex, ey, contact=contact, durationMS=durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)
                
    def Move(self, px, py, contact=0, wait_time=0):
        # px, py = self._ConvertCoordinates(px, py)
        self.__platformWrapper.Move(px, py, contact)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)
        
    def Reset(self, wait_time=0):
        self.__platformWrapper.Reset()
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def ADBClick(self, px, py):
        self.__platformWrapper.ADBClick(px, py)
        
    def ADBSwipe(self, sx, sy, ex, ey, durationMS=50):
        self.__platformWrapper.ADBSwipe(sx, sy, ex, ey, durationMS)

    def Key(self, key):
        self.__platformWrapper.Key(key)

    def Text(self, text):
        self.__platformWrapper.Text(text)

    def Wake(self):
        self.__platformWrapper.Wake()

    def Sleep(self):
        self.__platformWrapper.Sleep()

    def WMSize(self):
        return self.__platformWrapper.WMSize()

    def GetScreenResolution(self):
        return self.__platformWrapper.GetScreenResolution()

    # def BindRotation(self, rotation):
    #     self.__device.bind_rotation(rotation)

    # def InstallApp(self, installPackage):
    #     self.__device.install(installPackage)

    def CurrentApp(self):
        return self.__platformWrapper.CurrentApp()

    def ClearAppData(self, appPackageName):
        self.__platformWrapper.ClearAppData(appPackageName)

    def TakeScreenshot(self, targetPath):
        self.__platformWrapper.TakeScreenshot(targetPath)

    # def DumpUIHierarchy(self, targetPath=WINDOW_DUMP_PATH):
    #     self.__device.uiautomatorDump()
    #     self.__device.pull('/sdcard/window_dump.xml', targetPath)

    def DeviceInfo(self):
        """Fetch hardware information of device
        Returns:
            A dict mapping hardware information keys to the corresponding values fetched.
            For example:
            {'brand': 'Mi',
             'model': 'Note 2',
             'version': '7.1.0'
             ...}
        """
        hwInfos = self.__device.device_hardware()
        return hwInfos

    def GetScreenOri(self):
        return self.__platformWrapper.GetScreenOri()
        
    def GetMaxContact(self):
        return self.__platformWrapper.GetMaxContact()

    def GetDeviceParame(self, packageName):
        return self.__platformWrapper.DeviceParam(packageName)

    # def _ConvertPos(self, px, py):
    #     if self.__configOri == UI_SCREEN_ORI_PORTRAIT:
    #         newPx = py
    #         newPy = self.__shortSide - px
    #     else:
    #         newPx = self.__shortSide - py
    #         newPy = px
    #     return newPx, newPy
    #
    # def _ConvertCoordinates(self, px, py):
    #     if self.__configOri == UI_SCREEN_ORI_LANDSCAPE:
    #         nx = self.__deviceHeight - py * self.__deviceHeightScale * self.__convertRate
    #         ny = px * self.__deviceWidthScale / self.__convertRate
    #     else:
    #         nx = px * self.__deviceHeightScale
    #         ny = py * self.__deviceWidthScale
    #     return int(nx), int(ny)
