# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from .action_dqn_data import DqnActionData
from ....config_manager.ai.ai_manager import AIManager, AIAlgorithmType

logger = logging.getLogger("sdktool")


class RainBowActionData(DqnActionData):
    def __init__(self):
        ai_mgr = AIManager()
        self.__game_action = ai_mgr.get_game_action(3)
        self.__ai_action = ai_mgr.get_ai_action(3)

    @staticmethod
    def get_game_action_inner():
        return AIManager().get_game_action(AIAlgorithmType.RAINBOW)

    @staticmethod
    def get_ai_action_inner():
        return AIManager().get_ai_action(AIAlgorithmType.RAINBOW)
