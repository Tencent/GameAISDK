# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from .APIDefine import WAITTIME_MS
from .devicePlatform.WrappedPlatform import PlatformWrapper
from ..iMobileDeviceAPI import IMobileDeviceAPI

WINDOW_DUMP_PATH = 'window_dump.xml'


class AndroidDeviceAPI(IMobileDeviceAPI):
    def __init__(self, platform_type):
        super(AndroidDeviceAPI, self).__init__(platform_type)
        self.__platformWrapper = PlatformWrapper(platform_type)

    def Initialize(self, device_serial, long_edge, **kwargs):
        return self.__platformWrapper.Initialize(device_serial, long_edge, **kwargs)

    def DeInitialize(self):
        return self.__platformWrapper.DeInitialize()

    def GetFrame(self):
        return self.__platformWrapper.GetFrame()

    def InstallAPP(self, app_path):
        return self.__platformWrapper.InstallAPP(app_path)

    def LaunchAPP(self, package_name, activity_name=None):
        self.__platformWrapper.LauchAPP(package_name, activity_name)

    def ExitAPP(self, package_name):
        self.__platformWrapper.ExitAPP(package_name)

    def Click(self, px, py, contact=0, durationMS=-1, wait_time=0):
        # px, py = self._ConvertCoordinates(px, py)
        self.__platformWrapper.Click(px, py, contact=contact, duration_ms=durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Down(self, px, py, contact=0, wait_time=0):
        self.__platformWrapper.Down(px, py, contact=contact)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Up(self, contact=0, wait_time=0):
        self.__platformWrapper.Up(contact=contact)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def SwipeMove(self, px, py, contact=0, durationMS = 50, wait_time=0):
        self.__platformWrapper.SwipeMove(px, py, contact=contact, duration_ms = durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Swipe(self, sx, sy, ex, ey, contact=0, durationMS=50, needUp=True, wait_time=0):
        if needUp:
            self.__platformWrapper.SwipeDownMoveUp(sx, sy, ex, ey, contact=contact, duration_ms=durationMS)
        else:
            self.__platformWrapper.SwipeDownMove(sx, sy, ex, ey, contact=contact, duration_ms=durationMS)
        self.__platformWrapper.Wait(wait_time * WAITTIME_MS)

    def Move(self, px, py, contact=0, wait_time=0):
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

    def CurrentApp(self):
        return self.__platformWrapper.CurrentApp()

    def ClearAppData(self, appPackageName):
        self.__platformWrapper.ClearAppData(appPackageName)

    def TakeScreenshot(self, targetPath):
        self.__platformWrapper.TakeScreenshot(targetPath)

    def GetScreenOri(self):
        return self.__platformWrapper.GetScreenOri()

    def GetMaxContact(self):
        return self.__platformWrapper.GetMaxContact()

    def GetDeviceParame(self, packageName):
        return self.__platformWrapper.DeviceParam(packageName)
