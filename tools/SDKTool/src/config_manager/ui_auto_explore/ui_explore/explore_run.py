# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging

from ....config_manager.common.utils import load_json_file, save_json_file
from .auto_explore_config import auto_explore_cfg_inst
from .agentai_config import agentai_cfg_inst


class ExploreRun(object):
    def __init__(self, logger=None):
        self.__run_params_dict = {}
        self.__run_data_path = None
        self.__run_params_file_path = None
        self._logger = logger

    @property
    def run_data_path(self):
        return self.__run_data_path

    @run_data_path.setter
    def run_data_path(self, run_data_path):
        if not isinstance(run_data_path, str):
            msg = "run_data_path type error, only support str, type: {}".format(type(run_data_path))
            print(msg) if self._logger is None else self._logger.info(msg)
            return
        
        self.__run_data_path = run_data_path
        auto_explore_cfg_inst.set_run_data_path(run_data_path)
        agentai_cfg_inst.set_explore_run_inst(run_data_path)
        self.__run_params_file_path = os.path.abspath(os.path.join(self.__run_data_path,
                                                                   "..",
                                                                   "cache",
                                                                   "explore_run_params.json"))
        run_param_file_dir = os.path.dirname(self.__run_params_file_path)
        if not os.path.exists(run_param_file_dir):
            os.makedirs(run_param_file_dir)
        self.__run_params_dict = load_json_file(self.__run_params_file_path)


    @property
    def run_params_dict(self):
        if not self.__run_params_dict:
            auto_config_params = auto_explore_cfg_inst.get_auto_config_params()
            self.__run_params_dict['MaxClickNumber'] = auto_config_params['UiExplore']['MaxClickNumber']
            self.__run_params_dict['WaitTime'] = auto_config_params['UiExplore']['WaitTime']
            self.__run_params_dict['ComputeCoverage'] = auto_config_params['UiCoverage']['ComputeCoverage']
            self.__run_params_dict['ShowButton'] = auto_config_params['Debug']['ShowButton']

            use_plugin_env = agentai_cfg_inst.get('AGENT_ENV', 'usepluginenv')
            if use_plugin_env and int(use_plugin_env) == 1:
                self.__run_params_dict['EnvPackage'] = agentai_cfg_inst.get('AGENT_ENV', 'EnvPackage')
                self.__run_params_dict['EnvModule'] = agentai_cfg_inst.get('AGENT_ENV', 'EnvModule')
                self.__run_params_dict['EnvClass'] = agentai_cfg_inst.get('AGENT_ENV', 'EnvClass')
            else:
                self.__run_params_dict['EnvPackage'] = 'UIAuto'
                self.__run_params_dict['EnvModule'] = 'AppExploreEnv'
                self.__run_params_dict['EnvClass'] = 'Env'

            use_plugin_aimodel = agentai_cfg_inst.get('AI_MODEL', 'usepluginaimodel')
            if use_plugin_aimodel and int(use_plugin_aimodel) == 1:
                self.__run_params_dict['AIModelPackage'] = agentai_cfg_inst.get('AI_MODEL', 'AIModelPackage')
                self.__run_params_dict['AIModelModule'] = agentai_cfg_inst.get('AI_MODEL', 'AIModelModule')
                self.__run_params_dict['AIModelClass'] = agentai_cfg_inst.get('AI_MODEL', 'AIModelClass')
            else:
                self.__run_params_dict['AIModelPackage'] = 'UIAuto'
                self.__run_params_dict['AIModelModule'] = 'AppExploreAI'
                self.__run_params_dict['AIModelClass'] = 'AI'

        return self.__run_params_dict

    @run_params_dict.setter
    def run_params_dict(self, run_parmas_dict):
        if not isinstance(run_parmas_dict, dict):
            msg = "run_parmas_dict type error, only support dict, type: {}".format(type(run_parmas_dict))
            print(msg) if self._logger is None else self._logger.info(msg)
            return

        self.__run_params_dict = run_parmas_dict
        if self.__run_params_file_path:
            # save cached file
            save_json_file(self.__run_params_file_path, run_parmas_dict)

            # save auto_config_params
            auto_config_params = auto_explore_cfg_inst.get_auto_config_params()
            if 'UiExplore' in auto_config_params:
                auto_config_params['UiExplore']['MaxClickNumber'] = run_parmas_dict.get('MaxClickNumber', 100)
                auto_config_params['UiExplore']['WaitTime'] = run_parmas_dict.get('WaitTime', 4)
            if 'UiCoverage' in auto_config_params:
                auto_config_params['UiCoverage']['ComputeCoverage'] = True
            if "Debug" in auto_config_params:
                auto_config_params['Debug']['ShowButton'] = run_parmas_dict.get('ShowButton', True)
            auto_explore_cfg_inst.save_auto_config_params(auto_config_params)

            # AgentAI.ini
            agentai_cfg_inst.set('AGENT_ENV', 'usepluginenv', '1')
            agentai_cfg_inst.set('AI_MODEL', 'usepluginaimodel', '1')

            agentai_cfg_inst.set('AGENT_ENV', 'EnvPackage', run_parmas_dict.get('EnvPackage', 'UIAuto'))
            agentai_cfg_inst.set('AGENT_ENV', 'EnvModule', run_parmas_dict.get('EnvModule', 'AppExploreEnv'))
            agentai_cfg_inst.set('AGENT_ENV', 'EnvClass', run_parmas_dict.get('EnvClass', 'Env'))
            agentai_cfg_inst.set('AI_MODEL', 'AIModelPackage', run_parmas_dict.get('AIModelPackage', 'UIAuto'))
            agentai_cfg_inst.set('AI_MODEL', 'AIModelModule', run_parmas_dict.get('AIModelModule', 'AppExploreAI'))
            agentai_cfg_inst.set('AI_MODEL', 'AIModelClass', run_parmas_dict.get('AIModelClass', 'AI'))
            agentai_cfg_inst.save()


logger = logging.getLogger('sdktool')
explore_run_inst = ExploreRun(logger)
