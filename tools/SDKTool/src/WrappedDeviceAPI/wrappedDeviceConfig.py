# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
from enum import Enum, unique

# ========== configurations you can modify ==========
# save current screen before taking an action
SAVE_PIC = False

# ========== configurations you should not modify ==========
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, 'log')


@unique
class DeviceType(Enum):
    Android = "Android"
    IOS = "IOS"
    Windows = "Windows"


@unique
class Platform(Enum):
    """
    Platform use case:
        "Local": "Android"|"IOS"|"Windows"
        "WeTest": "Android"
        "GAutomator": "Android"
    """
    Local = "Local"
    WeTest = "WeTest"
    GAutomator = "GAutomator"
