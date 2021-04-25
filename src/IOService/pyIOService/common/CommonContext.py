# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os

from common.Define import TASK_STATUS_NONE, GAME_STATE_NONE


IO_SERVICE_CONTEXT = {
    'source_server_id': os.getenv('source_server_id', 'RESOURCE_APPLY_SERVER'),
    'task_id': None,
    'task_state': TASK_STATUS_NONE,
    'seesion_key': '0',
    'game_state': GAME_STATE_NONE,
    'frame': None,
    'frame_seq': 0,
    'frame_type': None,
    'extend': None,
    'test_mode': False,
    'io_service_type': os.getenv('io_service_type', 'ZMQ')
}
