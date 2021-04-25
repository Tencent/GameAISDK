# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from ....common.define import AI_ACTION_TYPES, CONTACTS
from ....config_manager.ai.ai_manager import AIManager, AIAlgorithmType
from ...utils import get_value
from .action_data import ActionData

logger = logging.getLogger("sdktool")


class ImActionData(ActionData):
    @staticmethod
    def get_game_action_inner():
        return AIManager().get_game_action(AIAlgorithmType.IM)

    @staticmethod
    def get_ai_action_inner():
        return AIManager().get_ai_action(AIAlgorithmType.IM)

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
        return AI_ACTION_TYPES

    def init_swipe_params(self, params=None):
        if params is None:
            params = OrderedDict()
        swipe_param = OrderedDict()
        swipe_param['path'] = ''
        swipe_param['startPoint'] = OrderedDict()
        swipe_param['startPoint']['x'] = get_value(params, 'startX', 0)
        swipe_param['startPoint']['y'] = get_value(params, 'startY', 0)

        swipe_param['endPoint'] = OrderedDict()
        swipe_param['endPoint']['x'] = get_value(params, 'endX', 0)
        swipe_param['endPoint']['y'] = get_value(params, 'endY', 0)

        swipe_param['startRect'] = OrderedDict()
        swipe_param['startRect']['x'] = get_value(params, 'startRectx', 0)
        swipe_param['startRect']['y'] = get_value(params, 'startRecty', 0)
        swipe_param['startRect']['w'] = get_value(params, 'startRectWidth', 0)
        swipe_param['startRect']['h'] = get_value(params, 'startRectHeight', 0)

        swipe_param['endRect'] = OrderedDict()
        swipe_param['endRect']['x'] = get_value(params, 'endRectx', 0)
        swipe_param['endRect']['y'] = get_value(params, 'endRecty', 0)
        swipe_param['endRect']['w'] = get_value(params, 'endRectHeight', 0)
        swipe_param['endRect']['h'] = get_value(params, 'endRectWidth', 0)
        return swipe_param

    def new_game_action(self, action_name, game_action):
        action_value = OrderedDict()
        action_value['id'] = game_action.alloc_id()
        action_value['name'] = action_name
        action_value['contact'] = CONTACTS[0]
        action_value['sceneTask'] = -1
        action_value['type'] = AI_ACTION_TYPES[0]
        return action_value
