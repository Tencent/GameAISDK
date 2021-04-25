# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict
from src.config_manager.ai.ai_manager import AIManager
from src.ui.utils import set_log_text, tool_to_sdk_path

logger = logging.getLogger("sdktool")


class AlgorithmData(object):
    def __init__(self):
        ai_mgr = AIManager()
        self.__parameter = OrderedDict()
        self.__ai_algorithm = ai_mgr.get_ai_algorithm()

    def save_ai_algorithm(self, algorithm_parameter):
        if len(algorithm_parameter) == 0:
            logger.info("action parameter is none")
            return

        parameter = OrderedDict()
        for key, value in algorithm_parameter.items():
            parameter[key] = value

        logger.debug("parameters %s", parameter)
        tool_to_sdk_path(parameter)

        flag, err = self.__ai_algorithm.update(**parameter)

        if not flag:
            logger.error("update ai action failed, reason %s", err)
            set_log_text(err)
