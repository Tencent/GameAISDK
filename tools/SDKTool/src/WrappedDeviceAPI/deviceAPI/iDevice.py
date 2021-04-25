# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABCMeta, abstractmethod


class IDevice(object):
    __metaclass__ = ABCMeta
    # 可使用操作的列表，由子类实现，
    actions = []

    def __init__(self, platform):
        """
        :param platform:
                    'Local': 在本地运行  (必须实现)
                    'WeTest': 在wetest运行 (不是必须实现)
        :excetption: 错误信息以异常的形式返回
        """
        self.platform = platform

    @abstractmethod
    def initialize(self, log_dir, **kwargs):
        """
        初始化设备
        :param log_dir: str, 指定日志目录（由WrappedDeviceAPI指定）
        :param kwargs: 实现时定义
        :return: True/False
        :excetption: 错误信息以异常的形式返回
        """
        raise NotImplementedError()

    @abstractmethod
    def deInitialize(self):
        """
        回收设备资源
        :return: True/False
        :excetption: 错误信息以异常的形式返回
        """
        raise NotImplementedError()

    @abstractmethod
    def getScreen(self, **kwargs):
        """
        获取当前图像帧
        :return: Mat类型的图像/None
        :excetption: 错误信息以异常的形式返回
        """
        raise NotImplementedError()

    @abstractmethod
    def doAction(self, **kwargs):
        """
        执行动作
        :param kwargs: 实现时定义, 格式{"aType": "xxx", "param1": _, "param2":, _}
        :return: True/False
        :excetption: 错误信息以异常的形式返回
        """
        raise NotImplementedError()
