# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABCMeta, abstractmethod


class IPcDeviceAPI(object):
    __metaclass__ = ABCMeta

    def __init__(self, platform):
        """
        :param platform:
                    'local': 在本地运行  (必须实现)
                    'wetest': 在wetest运行 (不是必须实现)
        :excetption: 错误信息以异常的形式返回
        """
        self.platform = platform

    @abstractmethod
    def Initialize(self, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def DeInitialize(self):
        raise NotImplementedError()
