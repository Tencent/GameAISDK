# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import platform
__is_windows_system = platform.platform().lower().startswith('window')
__is_linux_system = platform.platform().lower().startswith('linux')
if __is_windows_system:
    from .demo_windows.PlatformWeTest import PlatformWeTest
    from .demo_windows.common.AdbTool import AdbTool
elif __is_linux_system:
    from .demo_ubuntu16.PlatformWeTest import PlatformWeTest
    from .demo_ubuntu16.common.AdbTool import AdbTool
else:
    raise Exception('system is not support!')


def GetInstance():
    return PlatformWeTest()
