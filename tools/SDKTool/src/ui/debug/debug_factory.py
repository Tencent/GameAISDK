# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from .game_reg_debug import GameRegDebug
from .ui_debug import UIDebug

from ...common.define import DebugType
from ...common.singleton import Singleton

logger = logging.getLogger("sdktool")


class DebugFactory(metaclass=Singleton):
    """ 调试工厂类，根据配置文件中的不同配置，返回不同的调试子类
        目前支持GameRegDebug和UIDebug
    """
    def __init__(self):
        self.__instance = None
        self.__debug_type = None

    def initialize(self, debug_type):
        if debug_type == DebugType.GameReg:
            self.__instance = GameRegDebug()
        elif debug_type == DebugType.UI:
            self.__instance = UIDebug()
        else:
            logger.error("wrong mode of debug: %s", debug_type)
            return False

        self.__debug_type = debug_type

        return True

    # 获取对象
    def get_product_instance(self):
        if self.__instance is None:
            logger.error("product instance is None")
            return None

        return self.__instance

    def get_debug_type(self):
        return self.__debug_type

    def set_debug_type(self, debug_type):
        self.__debug_type = debug_type

    def finish(self):
        if self.__instance is not None:
            self.__instance.finish()
            self.__debug_type = None
