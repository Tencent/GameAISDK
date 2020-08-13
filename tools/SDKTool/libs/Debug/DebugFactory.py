# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from .GameRegDebug import *
from .UIDebug import *

cfgPath = "cfg/SDKTool.ini"

# 调试工厂类，根据配置文件中的不同配置，返回不同的调试子类
# 目前支持GameRegDebug和UIDebug
class DebugFactory():

    def __init__(self):
        self.__logger = logging.getLogger("sdktool")
        self.__productInstance = None

    def initialize(self, canvas=None, ui=None):
        self.config = configparser.ConfigParser()
        self.config.read(cfgPath)

        # 根据配置来实例化对应的类
        self.debug = self.config.get("debug", "debug")
        if self.debug == "GameReg":
            self.__productInstance = GameRegDebug(canvas, ui)
        elif self.debug == "UI":
            self.__productInstance = UIDebug(canvas, ui)
        else:
            self.__logger.error("wrong mode of debug: {}".format(self.debug))
            return False

        return True

    # 获取对象
    def get_product_instance(self):
        if self.__productInstance is None:
            self.__logger.error("product instance is None")
            return None

        return self.__productInstance