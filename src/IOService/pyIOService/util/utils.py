# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging

LOG = logging.getLogger('IOService')

def load_json_file(file_name):
    try:
        with open(file_name, 'r') as f:
            content = json.load(f)
            return content
    except Exception as err:
        LOG.error("read the file err, file_name:{}, err:{}".format(file_name, err))
        return {}
