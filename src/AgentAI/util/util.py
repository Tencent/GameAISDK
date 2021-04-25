# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
import logging
from .config_path_mgr import DEFAULT_USER_CONFIG_DIR
from protocol import common_pb2

logger = logging.getLogger("agent")


def get_configure(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_str = file.read()
            dqn_configure = json.loads(json_str)
            return dqn_configure
    except Exception as err:
        logger.error('Load game state file {} error! Error msg: {}'.format(file_path, err))
        return None


def get_button_state(result_dict, task_id):
    state = False
    px = -1
    py = -1

    reg_results = result_dict.get(task_id)
    if reg_results is None:
        return state, px, py

    for item in reg_results:
        flag = item['flag']
        if flag:
            x = item['boxes'][0]['x']
            y = item['boxes'][0]['y']
            w = item['boxes'][0]['w']
            h = item['boxes'][0]['h']

            state = True
            px = int(x + w/2)
            py = int(y + h/2)
            break

    return state, px, py


def create_source_response(source_dict):
    source_res_message = common_pb2.tagMessage()
    source_res_message.eMsgID = common_pb2.MSG_PROJECT_SOURCE_RES

    if 'device_type' in source_dict:
        source_res_message.stSource.deviceType = source_dict['device_type']
        os.environ['AISDK_DEVICE_TYPE'] = source_dict['device_type']
    if 'platform' in source_dict:
        source_res_message.stSource.platform = source_dict['platform']
    if 'long_edge' in source_dict:
        source_res_message.stSource.longEdge = source_dict['long_edge']
    if 'window_size' in source_dict:
        source_res_message.stSource.windowsSize = source_dict['window_size']
    if 'window_qpath' in source_dict:
        source_res_message.stSource.queryPath = source_dict['window_qpath']

    return source_res_message

def ConvertToSDKFilePath(filePath):
    """Convert file path according to environment variable AI_SDK_PATH

    """
    env_path = os.environ.get('AI_SDK_PROJECT_PATH', DEFAULT_USER_CONFIG_DIR)
    sdk_file_path = os.path.join(env_path, filePath)
    return sdk_file_path

