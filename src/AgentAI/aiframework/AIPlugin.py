# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import configparser
import os
import sys

from util import util
from .AIModelParameter import AIModelParameter
_cur_dir = os.path.dirname(os.path.abspath(__file__))

OLD_PLUGIN_CFG_FILE = 'cfg/task/agent/agentai.ini'
PLUGIN_CFG_FILE = 'cfg/task/agent/AgentAI.ini'

ALGORITHM_CONFIG_FILE = 'cfg/task/agent/Algorithm.json'

class AIPlugin(object):
    """
    AI plugin module, create aimodel object and agentenv object
    """

    def __init__(self):
        self.__logger = logging.getLogger('agent')
        self.__usePluginEnv = False
        self.__usePluginAIModel = False
        self.__useDefaultRunFunc = True

        self.__action_file_list = [
            'ImitationAction.json',
            'DQNAction.json',
            'RainbowAction.json'
        ]

        self.__model_parameter_dict = {
            1: AIModelParameter(0, 'agentenv', 'ImitationEnv', 'ImitationEnv', 0, 'ImitationLearning', 'ImitationAI',
                                'ImitationAI', 1),
            2: AIModelParameter(0, 'agentenv', 'DQNEnv', 'DQNEnv', 0, 'dqn', 'DQNAIModel', 'DQNAIModel', 1),
            3: AIModelParameter(0, 'agentenv', 'RainbowEnv', 'RainbowEnv', 0, 'rainbow', 'RainbowAIModel',
                                'RainbowAIModel', 1),
            4: AIModelParameter(0, 'agentenv', 'NavEnv', 'NavEnv', 0, 'nav', 'TraversalNavAI', 'TraversalNavAI', 1)
        }

        self.__envPackage = None
        self.__envModule = None
        self.__envClass = None
        self.__aiModelPackage = None
        self.__aiModelModule = None
        self.__aiModelClass = None
        self.__usePluginEnv = False
        self.__usePluginAIModel = False
        self.__useDefaultRunFunc = False

    def Init(self):
        """
        Load plugin config file, compatible with old style
        """
        # 首先加载自研的算法，如果加载失败，则加载插件信息
        if self.__load_ai_algorithm():
            return True

        pluginCfgPath = util.ConvertToSDKFilePath(PLUGIN_CFG_FILE)
        if os.path.exists(pluginCfgPath):
            return self._LoadPlugInParams(pluginCfgPath)

        oldPluginCfgPath = util.ConvertToSDKFilePath(OLD_PLUGIN_CFG_FILE)
        if os.path.exists(oldPluginCfgPath):
            return self._LoadOldPlugInParams(oldPluginCfgPath)

        self.__logger.error('agentai cfg file {0} not exist.'.format(pluginCfgPath))
        return False

    def __load_ai_algorithm(self):
        algorithm_config_path = util.ConvertToSDKFilePath(ALGORITHM_CONFIG_FILE)
        self.__logger.info("begin to load the ai algorithm configure, path:{}".format(algorithm_config_path))
        # 获取算法配置
        config = util.get_configure(algorithm_config_path)

        if config is None:
            self.__logger.warning("load the algorithm failed, please check other plugin file")
            return False

        alg_type = config['type']
        model_parameter = self.__model_parameter_dict[alg_type]
        if model_parameter is None:
            self.__logger.warning("get the model parameter failed, alg_type:{}".format(alg_type))
            return False

        if model_parameter.use_plugin_env == 0:
            self.__usePluginEnv = False
        else:
            self.__usePluginEnv = True

        if model_parameter.use_plugin_model == 0:
            self.__usePluginAIModel = False
        else:
            self.__usePluginAIModel = True

        if model_parameter.use_default_run_func == 0:
            self.__useDefaultRunFunc = False
        else:
            self.__useDefaultRunFunc = True

        # if self.__usePluginEnv is True:
        self.__envPackage = model_parameter.env_package
        self.__envModule = model_parameter.env_module
        self.__envClass = model_parameter.env_class

        # if self.__usePluginAIModel is True:
        self.__aiModelPackage = model_parameter.model_package
        self.__aiModelModule = model_parameter.model_module
        self.__aiModelClass = model_parameter.model_class

        self.__logger.info("get algorithm success, usePluginEnv:{}, usePluginAIModel:{}, useDefaultRunFunc:{}, "
                           "env_package:{}, env_model:{}, env_class:{}, "
                           "model_package:{}, model_module:{}, model_class:{}"
                           .format(self.__usePluginEnv, self.__usePluginAIModel, self.__useDefaultRunFunc,
                                   self.__envPackage, self.__envModule, self.__envClass,
                                   self.__aiModelPackage, self.__aiModelModule,  self.__aiModelClass))

        # if self.__useDefaultRunFunc is not True:
        #     self.__runFuncPackage = ""
        #     self.__runFuncModule = ""
        #     self.__runFuncName = ""

        return True

    def _LoadPlugInParams(self, pluginCfgPath):
        """
        Load new plugin config file
        """
        try:
            config = configparser.ConfigParser()
            config.read(pluginCfgPath)

            envSection = 'AGENT_ENV'
            aiSection = 'AI_MODEL'
            runSection = 'RUN_FUNCTION'

            if config.has_section('AgentEnv'):
                envSection = 'AgentEnv'

            if config.has_section('AIModel'):
                aiSection = 'AIModel'

            if config.has_section('RunFunc'):
                runSection = 'RunFunc'

            self.__usePluginEnv = config.getboolean(envSection, 'UsePluginEnv')
            self.__usePluginAIModel = config.getboolean(aiSection, 'UsePluginAIModel')
            self.__useDefaultRunFunc = config.getboolean(runSection, 'UseDefaultRunFunc')

            #if self.__usePluginEnv is True:
            self.__envPackage = config.get(envSection, 'EnvPackage')
            self.__envModule = config.get(envSection, 'EnvModule')
            self.__envClass = config.get(envSection, 'EnvClass')

            #if self.__usePluginAIModel is True:
            self.__aiModelPackage = config.get(aiSection, 'AIModelPackage')
            self.__aiModelModule = config.get(aiSection, 'AIModelModule')
            self.__aiModelClass = config.get(aiSection, 'AIModelClass')

            if self.__useDefaultRunFunc is not True:
                self.__runFuncPackage = config.get(runSection, 'RunFuncPackage')
                self.__runFuncModule = config.get(runSection, 'RunFuncModule')
                self.__runFuncName = config.get(runSection, 'RunFuncName')
        except Exception as e:
            self.__logger.error('Load file {} failed, error: {}.'.format(pluginCfgPath, e))
            return False

        return True

    def _LoadOldPlugInParams(self, pluginCfgPath):
        """
        Load old plugin config file
        """
        try:
            config = configparser.ConfigParser()
            config.read(pluginCfgPath)

            self.__usePluginEnv = config.getboolean('AgentEnv', 'UsePluginEnv')
            self.__usePluginAIModel = config.getboolean('AIModel', 'UsePluginAIModel')
            self.__useDefaultRunFunc = config.getboolean('RunFunc', 'UseDefaultRunFunc')

            #if self.__usePluginEnv is True:
            self.__envPackage = config.get('AgentEnv', 'EnvPackage')
            self.__envModule = config.get('AgentEnv', 'EnvModule')
            self.__envClass = config.get('AgentEnv', 'EnvClass')

            #if self.__usePluginAIModel is True:
            self.__aiModelPackage = config.get('AIModel', 'AIModelPackage')
            self.__aiModelModule = config.get('AIModel', 'AIModelModule')
            self.__aiModelClass = config.get('AIModel', 'AIModelClass')

            if self.__useDefaultRunFunc is not True:
                self.__runFuncPackage = config.get('RunFunc', 'RunFuncPackage')
                self.__runFuncModule = config.get('RunFunc', 'RunFuncModule')
                self.__runFuncName = config.get('RunFunc', 'RunFuncName')
        except Exception as e:
            self.__logger.error('Load file {} failed, error: {}.'.format(pluginCfgPath, e))
            return False

        return True

    def _AppendPluginPath(self):
        work_space_dir = os.path.abspath(os.path.join(_cur_dir, '..', '..'))
        pluginPath = os.path.join(work_space_dir, 'PlugIn', 'ai')
        # pluginPath = util.ConvertToSDKFilePath('PlugIn/ai')
        if os.path.isdir(pluginPath):
            sys.path.append(pluginPath)
            self.__logger.info('append external plugin path: {0}'.format(pluginPath))
        else:
            sys.path.append('PlugIn/ai')
            self.__logger.info('append internal plugin path')

    def _PopPluginPath(self):
        sys.path.pop()
        self.__logger.info('pop plugin path')

    def CreateAgentEnvObj(self):
        """
        Create agent env object from plugin script
        """
        if self.__usePluginEnv is True:
            self._AppendPluginPath()

        modulename = '{0}.{1}'.format(self.__envPackage, self.__envModule)
        envPackage = __import__(modulename)
        envModule = getattr(envPackage, self.__envModule)
        envClass = getattr(envModule, self.__envClass)
        self.__logger.info('agent env class: {0}'.format(envClass))
        agentEnv = envClass()

        if self.__usePluginEnv is True:
            self._PopPluginPath()

        return agentEnv

    def CreateAIModelObj(self):
        """
        Create ai model object from plugin script
        """
        if self.__usePluginAIModel is True:
            self._AppendPluginPath()
        else:
            sys.path.append('AgentAI/aimodel')

        modulename = '{0}.{1}'.format(self.__aiModelPackage, self.__aiModelModule)
        aiModelPackage = __import__(modulename)
        aiModelModule = getattr(aiModelPackage, self.__aiModelModule)
        aiModelClass = getattr(aiModelModule, self.__aiModelClass)
        self.__logger.info('aimodel class: {0}'.format(aiModelClass))
        aiModel = aiModelClass()

        self._PopPluginPath()

        return aiModel

    def CreateRunFunc(self):
        """
        Create ai run function object from plugin script
        """
        runAIFunc = None

        if self.__useDefaultRunFunc is not True:
            self._AppendPluginPath()
            modulename = '{0}.{1}'.format(self.__runFuncPackage, self.__runFuncModule)
            runFuncPackage = __import__(modulename)
            runFuncModule = getattr(runFuncPackage, self.__runFuncModule)
            runAIFunc = getattr(runFuncModule, self.__runFuncName)
            self.__logger.info('run function: {0}'.format(runAIFunc))
            self._PopPluginPath()

        return runAIFunc

    def UseDefaultRun(self):
        """
        Whether or not use defualt run function
        """
        return self.__useDefaultRunFunc
