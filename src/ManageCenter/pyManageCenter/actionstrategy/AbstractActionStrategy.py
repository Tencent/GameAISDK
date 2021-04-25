# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from abc import ABC, abstractmethod


class AbstractActionStrategy(ABC):
    """
    Abstract Action Strategy class, define abstract interface
    """
    def __init__(self):
        pass

    @abstractmethod
    def Initialize(self):
        """
        Abstract interface, Initialize
        """
        ...

    @abstractmethod
    def Finish(self):
        """
        Abstract interface, Finish
        """
        ...

    @abstractmethod
    def Reset(self):
        """
        Abstract interface, Reset
        """
        ...

    @abstractmethod
    def Perform(self, action):
        """
        Abstract interface, Perform strategy
        """
        ...
