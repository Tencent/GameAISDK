# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os

def ConvertToSDKFilePath(filePath):
    """
    Convert file path according to environment variable AI_SDK_PATH
    """
    sdkFilePath = ''
    envPath = os.environ.get('AI_SDK_PATH')

    if envPath is None:
        sdkFilePath = os.path.join('../', filePath)
    else:
        sdkFilePath = os.path.join(envPath, filePath)

    return sdkFilePath
