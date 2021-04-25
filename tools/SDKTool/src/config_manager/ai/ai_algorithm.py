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
from collections import OrderedDict

from ...common.singleton import Singleton
from ...common.define import AIAlgorithmType, AI_CONFIG_IM_ACTION_PATH, AI_CONFIG_DQN_ACTION_PATH, \
    AI_CONFIG_RAINBOW_ACTION_PATH, AI_CONFIG_IM_LEARNING_PATH, AI_CONFIG_DQN_LEARNING_PATH, \
    AI_CONFIG_RAINBOW_LEARNING_PATH, AI_CONFIG_IM_ENV_PATH, AI_CONFIG_DQN_ENV_PATH, AI_CONFIG_RAINBOW_ENV_PATH, \
    AI_CONFIG_ALGORITHM_PATH

AI_ALG_TYPE_KEY_NAME = 'type'

AI_ALG_ACTION_FILES = {
    AIAlgorithmType.IM: AI_CONFIG_IM_ACTION_PATH,
    AIAlgorithmType.DQN: AI_CONFIG_DQN_ACTION_PATH,
    AIAlgorithmType.RAINBOW: AI_CONFIG_RAINBOW_ACTION_PATH
}

AI_ALG_LEARNING_FILES = {
    AIAlgorithmType.IM: AI_CONFIG_IM_LEARNING_PATH,
    AIAlgorithmType.DQN: AI_CONFIG_DQN_LEARNING_PATH,
    AIAlgorithmType.RAINBOW: AI_CONFIG_RAINBOW_LEARNING_PATH
}

AI_ALG_ENV_FILES = {
    AIAlgorithmType.IM: AI_CONFIG_IM_ENV_PATH,
    AIAlgorithmType.DQN: AI_CONFIG_DQN_ENV_PATH,
    AIAlgorithmType.RAINBOW: AI_CONFIG_RAINBOW_ENV_PATH
}


logger = logging.getLogger("sdktool")


class Algorithm(metaclass=Singleton):
    def __init__(self):
        self.__alg_parameter = {AI_ALG_TYPE_KEY_NAME: AIAlgorithmType.IM}

    def get_alg_action_file(self, project_path: str) -> str:
        alg_type = self.get_algorithm_type()
        if alg_type is None:
            return None
        return os.path.join(project_path, AI_ALG_ACTION_FILES[alg_type])

    def get_alg_learning_file(self, project_path: str) -> str:
        alg_type = self.get_algorithm_type()
        if alg_type is None:
            return None
        return os.path.join(project_path, AI_ALG_LEARNING_FILES[alg_type])

    def get_alg_env_file(self, project_path: str) -> str:
        alg_type = self.get_algorithm_type()
        if alg_type is None:
            return None
        return os.path.join(project_path, AI_ALG_ENV_FILES[alg_type])

    def clear(self):
        self.__alg_parameter.clear()

    def load_algorithm(self, project_path: str):
        alg_file = os.path.join(project_path, AI_CONFIG_ALGORITHM_PATH)
        if not os.path.exists(alg_file):
            logger.warning('failed to find algorithm file(%s), use default im algorithm' % alg_file)
            self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = AIAlgorithmType.IM
            self.dump_algorithm_parameter(project_path, AIAlgorithmType.IM)
            return True

        try:
            with open(alg_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            self.__alg_parameter = json.loads(json_str, object_pairs_hook=OrderedDict)
            if AI_ALG_TYPE_KEY_NAME not in self.__alg_parameter:
                logger.warning('failed to find algorithm file(%s), use default im algorithm' % alg_file)
                self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = AIAlgorithmType.IM
            return True

        except FileNotFoundError:
            logger.error('file(%s) is not found', project_path)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')
        return False

    def get_algorithm_type(self):
        return self.__alg_parameter[AI_ALG_TYPE_KEY_NAME]

    def update(self, **kwargs) -> tuple:
        try:
            for key, value in kwargs.items():
                if key == 'Algorithm' and value == 'IM':
                    self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = AIAlgorithmType.IM
                elif key == 'Algorithm' and value == 'DQN':
                    self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = AIAlgorithmType.DQN
                elif key == 'Algorithm' and value == 'RAINBOW':
                    self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = AIAlgorithmType.RAINBOW
            return True, ''

        except KeyError as err:
            logger.error("update the algorithm type KeyError:{}".format(err))
            return False, 'action has no key: {}'.format(err)

    def dump_algorithm_parameter(self, project_path: str, alg_type: int):
        alg_file = os.path.join(project_path, AI_CONFIG_ALGORITHM_PATH)
        try:

            self.__alg_parameter[AI_ALG_TYPE_KEY_NAME] = alg_type
            json_str = json.dumps(self.__alg_parameter, indent=4, ensure_ascii=False)
            with open(alg_file, 'w', encoding='utf-8') as file:
                file.write(json_str)
            return True

        except FileNotFoundError:
            logger.error('file(%s) is not found', project_path)

        return False
