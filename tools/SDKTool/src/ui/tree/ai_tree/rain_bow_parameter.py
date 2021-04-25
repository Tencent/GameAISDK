# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from ....config_manager.ai.ai_manager import AIManager
from ...utils import valid_number_value, tool_to_sdk_path, sdk_to_tool_path, exchange_value
from ....config_manager.ai.ai_algorithm import AIAlgorithmType

logger = logging.getLogger("sdktool")


class RainbowParameter(object):

    def __init__(self):
        self.__parameter = OrderedDict()
        self._ai_parameter_inst = None
        self._ai_mgr = AIManager()

    def init(self):
        if not self.__parameter:
            return self._ai_mgr.load_learning_config(AIAlgorithmType.RAINBOW)
        return True

    def get_parameters(self):
        save_parameter = self.__get_params().get_config()
        if save_parameter:
            self.__parameter.update(save_parameter)

        sdk_to_tool_path(self.__parameter)
        return self.__parameter

    def __get_params(self):
        if self._ai_parameter_inst is None:
            self._ai_parameter_inst = self._ai_mgr.get_ai_parameter(AIAlgorithmType.RAINBOW)
        return self._ai_parameter_inst

    def save_parameter(self, configure):
        valid_number_value(configure)
        for key, value in configure.items():
            if key in self.__parameter.keys():
                self.__parameter[key] = exchange_value(key, value)
            else:
                logger.error('unknown key %s', key)

        tool_to_sdk_path(self.__parameter)
        self.__get_params().set_config(self.__parameter)
