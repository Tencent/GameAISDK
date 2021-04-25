# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from ....common.define import DQN_ACTION_TYPES, CONTACTS, AI_ACTION_TYPES
from ....config_manager.ai.ai_manager import AIManager, AIAlgorithmType
from .action_data import ActionData
from ...utils import get_value

logger = logging.getLogger("sdktool")


class DqnActionData(ActionData):
    @staticmethod
    def get_game_action_inner():
        return AIManager().get_game_action(AIAlgorithmType.DQN)

    @staticmethod
    def get_ai_action_inner():
        return AIManager().get_ai_action(AIAlgorithmType.DQN)

    def game_action_extend_param(self):
        param = OrderedDict()
        out_params = OrderedDict()
        out_params['path'] = ''
        out_params['region'] = OrderedDict()
        out_params['region']['x'] = 0
        out_params['region']['y'] = 0
        out_params['region']['w'] = 0
        out_params['region']['h'] = 0
        param['actionRegion'] = out_params
        param['durationMS'] = 0
        return param

    def get_type_param(self):
        out_params = OrderedDict()
        out_params['path'] = ''
        out_params['region'] = OrderedDict()
        out_params['region']['x'] = 0
        out_params['region']['y'] = 0
        out_params['region']['w'] = 0
        out_params['region']['h'] = 0
        return out_params

    def get_game_action_type_param(self):
        return DQN_ACTION_TYPES

    def init_swipe_params(self, params=None):
        if params is None:
            params = OrderedDict()
        swipe_param = OrderedDict()
        swipe_param['startX'] = get_value(params, 'startX', 0)
        swipe_param['startY'] = get_value(params, 'startY', 0)
        swipe_param['endX'] = get_value(params, 'endX', 0)
        swipe_param['endY'] = get_value(params, 'endY', 0)
        return swipe_param

    def new_game_action(self, action_name, game_action):
        action_value = OrderedDict()
        action_value['id'] = game_action.alloc_id()
        action_value['name'] = action_name
        action_value['contact'] = CONTACTS[0]
        action_value['sceneTask'] = -1
        action_value['type'] = AI_ACTION_TYPES[0]
        return action_value
