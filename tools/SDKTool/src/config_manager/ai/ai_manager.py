# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import os
import logging
from enum import Enum, unique
from collections import OrderedDict

from .ai_parameter import AiParameter
from .game_state import GameState
from .ai_action import GameAction, AIAction
from ...common.singleton import Singleton
from .ai_algorithm import Algorithm, AI_ALG_ENV_FILES, AI_ALG_LEARNING_FILES, AI_ALG_ACTION_FILES
from .ai_resolution import AIResolution
from ..task.task_manager import TaskManager
from ...ui.dialog.tip_dialog import show_warning_tips
from ...common.define import LEARNING_CONFIG_TASKID_LIST, LEARNING_CONFIG_EXCITATIONFUNCTION_Key, AIAlgorithmType


@unique
class AIType(Enum):
    IMITATION_AI = AIAlgorithmType.IM
    DQN_AI = AIAlgorithmType.DQN
    RAIN_BOW_AI = AIAlgorithmType.RAINBOW


logger = logging.getLogger("sdktool")


class AIManager(metaclass=Singleton):

    # __init = False

    def __init__(self):
        super(AIManager, self).__init__()
        self.__ai_type = AIType.IMITATION_AI.value
        self.__ai_algorithm = Algorithm()
        self.__project_path = None
        self.__game_state_dict = {}
        self.__game_action_dict = {}
        self.__ai_action_dict = {}
        self.__ai_parameter_dict = {}
        self.__resolution_dict = {}
        self.__task_mgr = TaskManager()

        self.init_config()

    def set_ai_type(self, ai_type):
        self.__ai_type = ai_type

    def get_ai_type(self):
        return self.__ai_type

    def get_game_state(self, alg_type):
        if self.__game_state_dict:
            return self.__game_state_dict[alg_type]
        return None

    def get_game_action(self, alg_type):
        if self.__game_action_dict:
            return self.__game_action_dict[alg_type]
        return None

    def get_ai_action(self, alg_type):
        if self.__ai_action_dict:
            return self.__ai_action_dict[alg_type]
        return None

    def get_ai_parameter(self, alg_type):
        return self.__ai_parameter_dict[alg_type]

    def get_ai_algorithm(self):
        return self.__ai_algorithm

    def get_resolution(self, alg_type):
        return self.__resolution_dict[alg_type]

    def clear_config(self) -> None:
        self.__game_action_dict.clear()
        self.__ai_action_dict.clear()
        self.__game_state_dict.clear()
        self.__ai_parameter_dict.clear()
        self.__resolution_dict.clear()

        # 清除后，重新初始化
        self.init_config()

    def init_config(self):
        self.__game_state_dict = {AIAlgorithmType.IM: GameState(),
                                  AIAlgorithmType.DQN: GameState(),
                                  AIAlgorithmType.RAINBOW: GameState()}
        self.__game_action_dict = {AIAlgorithmType.IM: GameAction(),
                                   AIAlgorithmType.DQN: GameAction(),
                                   AIAlgorithmType.RAINBOW: GameAction()}
        self.__ai_action_dict = {AIAlgorithmType.IM: AIAction(),
                                 AIAlgorithmType.DQN: AIAction(),
                                 AIAlgorithmType.RAINBOW: AIAction()}
        self.__ai_parameter_dict = {AIAlgorithmType.IM: AiParameter(),
                                    AIAlgorithmType.DQN: AiParameter(),
                                    AIAlgorithmType.RAINBOW: AiParameter()}
        self.__resolution_dict = {AIAlgorithmType.DQN: AIResolution(),
                                  AIAlgorithmType.RAINBOW: AIResolution()}

    def load_config(self, project_path: str) -> bool:
        """ 加载配置

        :param project_path:
        :return:
        """
        self.__project_path = project_path
        if not self.__ai_algorithm.load_algorithm(project_path):
            return False

        algorithm_type = self.__ai_algorithm.get_algorithm_type()
        self.set_ai_type(algorithm_type)

        if not self._load_im_config(project_path):
            logger.warning('failed to load im config')

        if not self._load_dqn_config(project_path):
            logger.warning('failed to load dqn config')

        if not self._load_rain_bow_config(project_path):
            logger.warning('failed to load rainbow config')

        return True

    def _load_im_action_config(self, action_file: str):

        game_action = self.__game_action_dict[AIAlgorithmType.IM]
        ai_action = self.__ai_action_dict[AIAlgorithmType.IM]

        if not os.path.exists(action_file):
            logger.warning('file(%s) not exists, set empty actions' % action_file)
            game_action.load([])
            ai_action.load([])

            return True

        try:
            with open(action_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            action_cfg = json.loads(json_str, object_pairs_hook=OrderedDict)

            if isinstance(action_cfg['gameAction'], list):
                game_action.load(action_cfg['gameAction'])

            if isinstance(action_cfg['aiAction'], list):
                ai_action.load(action_cfg['aiAction'])

            return True

        except FileNotFoundError:
            logger.error('file(%s) is not found', action_file)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')

        return False

    def _load_dqn_action_config(self, action_file: str):
        game_action = self.__game_action_dict[AIAlgorithmType.DQN]

        if not os.path.exists(action_file):
            logger.warning('file(%s) not exists, set empty actions' % action_file)
            game_action.load([])
            return True

        try:
            with open(action_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            action_cfg = json.loads(json_str, object_pairs_hook=OrderedDict)

            if isinstance(action_cfg['actions'], list):
                game_action.load(action_cfg['actions'])

            resolution = self.__resolution_dict[AIAlgorithmType.DQN]
            resolution.load(action_cfg)
            return True
        except FileNotFoundError:
            logger.error('file(%s) is not found', action_file)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')

        return False

    def _load_rainbow_action_config(self, action_file: str):
        try:

            with open(action_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            action_cfg = json.loads(json_str, object_pairs_hook=OrderedDict)

            if isinstance(action_cfg['actions'], list):
                game_action = self.__game_action_dict[AIAlgorithmType.RAINBOW]
                game_action.load(action_cfg['actions'])

            resolution = self.__resolution_dict[AIAlgorithmType.RAINBOW]
            resolution.load(action_cfg)
            return True

        except FileNotFoundError:
            logger.error('file(%s) is not found', action_file)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')

        return False

    def _load_game_state_config(self, config_file: str, alg_type: int) -> bool:
        game_state = self.__game_state_dict[alg_type]
        if not os.path.exists(config_file):
            logger.warning('game state file(%s) not exists, set empty game state' % config_file)
            config = {
                "beginTaskID": [],
                "overTaskID": []
            }

            game_state.load(config)
            return True

        try:
            with open(config_file, 'r', encoding='utf-8') as fd:
                json_str = fd.read()
                config = json.loads(json_str, object_pairs_hook=OrderedDict)
                game_state.load(config)
            return True
        except FileNotFoundError:
            logger.error('file(%s) is not found', config_file)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')
        return False

    def _load_learning_config(self, config_file: str, alg_type: int) -> bool:
        if not os.path.exists(config_file):
            logger.error('algorithm param file(%s) not exists!' % config_file)
            return False

        try:
            with open(config_file, 'r', encoding='utf-8') as fd:
                json_str = fd.read()
                config = json.loads(json_str, object_pairs_hook=OrderedDict)
                ai_parameter = self.__ai_parameter_dict[alg_type]
                ai_parameter.load(config)
            return True
        except FileNotFoundError:
            logger.error('file(%s) is not found', config_file)
        except json.decoder.JSONDecodeError:
            logger.error('unable to decode string')
        return False

    def load_learning_config(self, alg_type: int) -> bool:
        """ 加载训练配置参数

        :param alg_type:
        :return:
        """
        project_path = os.environ.get('AI_SDK_PROJECT_PATH', self.__project_path)
        if not project_path or not os.path.exists(project_path):
            logger.error('failed to get project path(%s)' % project_path)
            return False

        config_file = os.path.join(project_path, AI_ALG_LEARNING_FILES[alg_type])
        return self._load_learning_config(config_file, alg_type)

    def _load_im_config(self, project_path: str) -> bool:

        im_action_file = os.path.join(project_path, AI_ALG_ACTION_FILES[AIAlgorithmType.IM])
        im_env_file = os.path.join(project_path, AI_ALG_ENV_FILES[AIAlgorithmType.IM])

        load_result = self._load_im_action_config(im_action_file)
        if not load_result:
            return False

        load_result = self._load_game_state_config(im_env_file, AIAlgorithmType.IM)
        if not load_result:
            return False

        load_result = self.load_learning_config(AIAlgorithmType.IM)
        if not load_result:
            return False

        return True

    def _load_dqn_config(self, project_path: str):
        dqn_action_file = os.path.join(project_path, AI_ALG_ACTION_FILES[AIAlgorithmType.DQN])
        dqn_env_file = os.path.join(project_path, AI_ALG_ENV_FILES[AIAlgorithmType.DQN])

        load_result = self.load_learning_config(AIAlgorithmType.DQN)
        if not load_result:
            return False

        load_result = self._load_dqn_action_config(dqn_action_file)
        if not load_result:
            return False

        load_result = self._load_game_state_config(dqn_env_file, AIAlgorithmType.DQN)
        if not load_result:
            return False

        return True

    def _load_rain_bow_config(self, project_path: str):
        rain_bow_action_file = os.path.join(project_path, AI_ALG_ACTION_FILES[AIAlgorithmType.RAINBOW])
        rain_bow_env_file = os.path.join(project_path, AI_ALG_ENV_FILES[AIAlgorithmType.RAINBOW])

        # 需保证rainbow算法参数加载正常
        load_result = self.load_learning_config(AIAlgorithmType.RAINBOW)
        if not load_result:
            return False

        load_result = self._load_rainbow_action_config(rain_bow_action_file)
        if not load_result:
            return False

        load_result = self._load_game_state_config(rain_bow_env_file, AIAlgorithmType.RAINBOW)
        if not load_result:
            return False

        return True

    def dump_config(self, project_path: str) -> bool:

        if not self.__ai_algorithm.dump_algorithm_parameter(project_path, self.__ai_type):
            return False

        action_file = self.__ai_algorithm.get_alg_action_file(project_path)
        learning_file = self.__ai_algorithm.get_alg_learning_file(project_path)
        env_file = self.__ai_algorithm.get_alg_env_file(project_path)

        if self.__ai_type == AIType.DQN_AI.value or self.__ai_type == AIType.RAIN_BOW_AI.value:
            if not self._dump_dqn_action_config(action_file):
                return False
        elif self.__ai_type == AIType.IMITATION_AI.value:
            if not self._dump_im_action_config(action_file):
                return False

        if not self._dump_json_config(self.__ai_parameter_dict[self.__ai_type], learning_file):
            return False

        is_ok, check_content, task_id = self._check_env_config()
        if not is_ok:
            show_warning_tips('Task(%s) 已被删除，请在(%s)重新配置' % (task_id, check_content))

        if not self._dump_json_config(self.__game_state_dict[self.__ai_type], env_file):
            return False

        return True

    def _check_im_action(self, game_action, ai_action):
        task_inst = self.__task_mgr.get_task()
        game_actions_id = []
        if game_action:
            for ele in game_action:
                if 'id' in ele and ele['id'] not in game_actions_id:
                    game_actions_id.append(ele['id'])
                if 'sceneTask' in ele:
                    task_id = ele.get('sceneTask', 0)
                    if task_id and not task_inst.has_id(task_id):
                        return False, 'Define Actions', task_id

        if ai_action:
            for ele in ai_action:
                action_id_group = ele.get('actionIDGroup', [])
                for action_id in action_id_group:
                    if action_id not in game_actions_id:
                        return False, 'Define Actions', action_id

        return True, 'Actions', None

    def _check_env_config(self):
        """ 检查env中是否存在无效task

        :return:
        """
        task_inst = self.__task_mgr.get_task()
        env_config = self.__game_state_dict[self.__ai_type].dump()

        if 'beginTaskID' in env_config and env_config['beginTaskID']:
            for task_id in env_config['beginTaskID']:
                if not task_inst.has_id(task_id):
                    return False, 'GameState(Begin)', task_id
        if 'overTaskID' in env_config and env_config['overTaskID']:
            for task_id in env_config['overTaskID']:
                if not task_inst.has_id(task_id):
                    return False, 'GameState(Over)', task_id
        return True, 'GameState', None

    def check_learning_config(self):
        task_inst = self.__task_mgr.get_task()
        learning_config = self.__ai_parameter_dict[self.__ai_type].dump()
        if self.__ai_type in [AIAlgorithmType.DQN, AIAlgorithmType.RAINBOW]:
            if LEARNING_CONFIG_EXCITATIONFUNCTION_Key in learning_config:
                excitation_function_config = learning_config[LEARNING_CONFIG_EXCITATIONFUNCTION_Key]
                for k, v in excitation_function_config.items():
                    if k in LEARNING_CONFIG_TASKID_LIST:
                        if isinstance(v, int):
                            if not task_inst.has_id(v):
                                return False, 'Model Parameter(%s)' % k, v
                        elif v is None:
                            return False, 'Model Parameter(%s) is None' % k, None

        return True, 'Model Parameter', None

    def _dump_im_action_config(self, action_file: str) -> bool:
        try:
            action_cfg = OrderedDict()
            game_action = self.__game_action_dict[self.__ai_type].dump()
            ai_action = self.__ai_action_dict[self.__ai_type].dump()
            is_ok, check_content, task_id = self._check_im_action(game_action, ai_action)
            if not is_ok:
                show_warning_tips('Task(%s) 已被删除，请在(%s)重新配置' % (task_id, check_content))
            action_cfg['gameAction'] = game_action
            action_cfg['aiAction'] = ai_action
            json_str = json.dumps(action_cfg, indent=4, ensure_ascii=False)
            with open(action_file, 'w', encoding='utf-8') as fd:
                fd.write(json_str)

            return True
        except FileNotFoundError:
            logger.error('file(%s) is not found', action_file)

        return False

    def _dump_dqn_action_config(self, action_file: str) -> bool:
        try:
            action_cfg = OrderedDict()
            action_cfg['screenHeight'] = self.__resolution_dict[self.__ai_type].dump()['screenHeight']
            action_cfg['screenWidth'] = self.__resolution_dict[self.__ai_type].dump()['screenWidth']
            action_cfg['actions'] = self.__game_action_dict[self.__ai_type].dump()
            json_str = json.dumps(action_cfg, indent=4, ensure_ascii=False)
            with open(action_file, 'w', encoding='utf-8') as fd:
                fd.write(json_str)
            return True

        except FileNotFoundError:
            logger.error('file(%s) is not found', action_file)

        return False

    @staticmethod
    def _dump_json_config(instance, config_file: str) -> bool:
        try:
            config = instance.dump()
            if not config:
                logger.info('config is empty, so quit')
                return True
            json_str = json.dumps(config, indent=4, ensure_ascii=False)
            with open(config_file, 'w', encoding='utf-8') as fd:
                fd.write(json_str)
            return True
        except FileNotFoundError:
            logger.error('file(%s) is not found', config_file)

        return False
