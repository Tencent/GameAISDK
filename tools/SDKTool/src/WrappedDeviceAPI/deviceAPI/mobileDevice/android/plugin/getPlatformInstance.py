# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
import importlib
import os
import logging

from ..APIDefine import LOG_DEFAULT, PLUGIN_TOUCH_DIR

from wrappedDeviceConfig import Platform

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir + PLUGIN_TOUCH_DIR)


# 动态导入包，并获取组件对象
def GetPlatformInstance(serial=None, platform_type=None):
    if serial is None:
        logger = logging.getLogger(LOG_DEFAULT)
    else:
        logger = logging.getLogger(serial)

    if platform_type in [Platform.Local.value, Platform.WeTest.value]:
        module_class = importlib.import_module('PlatformWeTest')
        get_instance = getattr(module_class, "GetInstance")
        return get_instance()

    logger.error("unknown platform: %s", platform_type)
    return None
