# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import platform
__is_windows_system = platform.platform().lower().startswith('window')
__is_linux_system = platform.platform().lower().startswith('linux')
if __is_windows_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'windows'))
    from windows.detect_one_image_util import main
elif __is_linux_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ubuntu'))
    from ubuntu.detect_one_image_util import main
else:
    raise Exception('system is not support!')


if __name__ == '__main__':
    main()
