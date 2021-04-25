# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABCMeta, abstractmethod


class IMobileDeviceAPI(object):
    __metaclass__ = ABCMeta

    def __init__(self, platform_type):
        """
        :param platform_type:
                    'local': 在本地运行  (必须实现)
                    'wetest': 在wetest运行 (不是必须实现)
        :excetption: 错误信息以异常的形式返回
        """
        self._platform_type = platform_type

    @abstractmethod
    def Initialize(self, device_serial, long_edge, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def DeInitialize(self):
        raise NotImplementedError()

    @abstractmethod
    def GetFrame(self):
        raise NotImplementedError()

    @abstractmethod
    def InstallAPP(self, app_path):
        raise NotImplementedError()

    @abstractmethod
    def LaunchAPP(self, package_name, activity_name=None):
        raise NotImplementedError()

    @abstractmethod
    def ExitAPP(self, package_name):
        raise NotImplementedError()

    @abstractmethod
    def Click(self, px, py, contact=0, durationMS=-1, wait_time=0):
        raise NotImplementedError()

    # @abstractmethod
    # def Down(self, **kwargs):
    #     raise NotImplementedError()
    #
    # @abstractmethod
    # def Up(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def Swipe(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def Move(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def Key(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def Text(self, **kwargs):
    #     raise NotImplementedError()

    @abstractmethod
    def Wake(self):
        raise NotImplementedError()

    @abstractmethod
    def Sleep(self):
        raise NotImplementedError()

    # @abstractmethod
    # def LoginQQ(self, **kwargs):
    #     raise NotImplementedError()

    @abstractmethod
    def WMSize(self):
        raise NotImplementedError()

    # @abstractmethod
    # def BindRotation(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def CurrentApp(self):
    #     raise NotImplementedError()

    # @abstractmethod
    # def ClearAppData(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def TakeScreenshot(self, **kwargs):
    #     raise NotImplementedError()

    # @abstractmethod
    # def DeviceInfo(self):
    #     raise NotImplementedError()

    # @abstractmethod
    # def PerfStatsInit(self):
    #     raise NotImplementedError()

    # @abstractmethod
    # def PerfStatsData(self):
    #     raise NotImplementedError()

    # @abstractmethod
    # def PerfStatsFinish(self):
    #     raise NotImplementedError()

    # @abstractmethod
    # def GetScreenOri(self):
    #     raise NotImplementedError()
