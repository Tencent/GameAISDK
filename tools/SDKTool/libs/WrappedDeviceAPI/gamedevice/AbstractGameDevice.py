# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABCMeta, abstractmethod

class AbstractGameDevice(object):
    __metaclass__ = ABCMeta

    def __init__(self, device=None):
        pass

    @abstractmethod
    def Initialize(self, deviceSerial, isPortrait, long_edge, kwargs):
        raise NotImplementedError()

    @abstractmethod
    def DeInitialize(self):
        raise NotImplementedError()

    @abstractmethod
    def Finish(self):
        raise NotImplementedError()

    @abstractmethod
    def GetFrame(self):
        raise NotImplementedError()

    @abstractmethod
    def InstallAPP(self, APKPath):
        raise NotImplementedError()

    @abstractmethod
    def LaunchAPP(self, PackageName, ActivityName):
        raise NotImplementedError()

    @abstractmethod
    def ExitAPP(self, PackageName):
        raise NotImplementedError()

    @abstractmethod
    def Click(self, px, py, type, contact, durationMS):
        raise NotImplementedError()

    @abstractmethod
    def Down(self, px, py, contact):
        raise NotImplementedError()

    @abstractmethod
    def Up(self, contact):
        raise NotImplementedError()

    @abstractmethod
    def Swipe(self, startPx, startPy, endPx, endPy, type, contact, durationMS, needUp):
        raise NotImplementedError()

    @abstractmethod
    def Move(self, px, py, contact):
        raise NotImplementedError()

    @abstractmethod
    def Key(self, key):
        raise NotImplementedError()

    @abstractmethod
    def Text(self, text):
        raise NotImplementedError()

    @abstractmethod
    def Wake(self):
        raise NotImplementedError()

    @abstractmethod
    def Sleep(self):
        raise NotImplementedError()

    @abstractmethod
    def LoginQQ(self, account, passwd):
        raise NotImplementedError()

    @abstractmethod
    def WMSize(self):
        raise NotImplementedError()

    @abstractmethod
    def BindRotation(self, rotation):
        raise NotImplementedError()

    @abstractmethod
    def CurrentApp(self):
        raise NotImplementedError()

    @abstractmethod
    def ClearAppData(self, appPackageName):
        raise NotImplementedError()

    @abstractmethod
    def TakeScreenshot(self, targetPath):
        raise NotImplementedError()

    @abstractmethod
    def DeviceInfo(self):
        raise NotImplementedError()

    @abstractmethod
    def PerfStatsInit(self):
        raise NotImplementedError()

    @abstractmethod
    def PerfStatsData(self):
        raise NotImplementedError()

    @abstractmethod
    def PerfStatsFinish(self):
        raise NotImplementedError()

    @abstractmethod
    def GetScreenOri(self):
        raise NotImplementedError()
