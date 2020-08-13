# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import configparser
import os
import sys
import time

from protocol import common_pb2
from connect.BusConnect import BusConnect
from util import util

OLD_PLUGIN_CFG_FILE = 'cfg/task/agent/agentai.ini'
PLUGIN_CFG_FILE = 'cfg/task/agent/AgentAI.ini'

ENV_STATE_WAITING_START = 0
ENV_STATE_PLAYING = 1
ENV_STATE_PAUSE_PLAYING = 2
ENV_STATE_RESTORE_PLAYING = 3
ENV_STATE_OVER = 4

class AIFrameWork(object):
    """
    Agent AI framework, run AI test
    """

    def __init__(self):
        self.__usePluginEnv = False
        self.__usePluginAIModel = False
        self.__useDefaultRunFunc = True
        self.__logger = logging.getLogger('agent')
        self.__aiModel = None
        self.__agentEnv = None
        self.__RunAIFunc = None
        self.__outputAIAction = True
        self.__connect = BusConnect()

    def Init(self):
        """
        Init tbus connect, register service, create ai & env object
        """
        if self.__connect.Connect() is not True:
            self.__logger.error('Agent connect failed.')
            return False

        if self._RegisterService() is not True:
            self.__logger.error('Agent register service failed.')
            self._SendTaskReport(common_pb2.PB_TASK_INIT_FAILURE)
            return False

        if self._InitAITask() is True:
            self._SendTaskReport(common_pb2.PB_TASK_INIT_SUCCESS)
        else:
            self._SendTaskReport(common_pb2.PB_TASK_INIT_FAILURE)
            return False

        return True

    def _InitAITask(self):
        if self._GetPluginInConfig() is not True:
            return False

        self._CreateAgentEnvObj()
        self._CreateAIModelObj()

        if self.__aiModel is None or self.__agentEnv is None:
            self.__logger.error('Create agent env or aimodel object failed.')
            return False

        self._CreateRunFunc()
        if self.__useDefaultRunFunc is not True and self.__RunAIFunc is None:
            self.__logger.error('Create run function failed.')
            return False

        if self.__agentEnv.Init() is not True:
            self.__logger.error('Agent env init failed.')
            return False

        if self.__aiModel.Init(self.__agentEnv) is not True:
            self.__logger.error('AI model init failed.')
            return False

        return True

    def Finish(self):
        """
        Disconnect tbus, unregister service, release ai & env object
        """
        self._UnRegisterService()
        if self.__aiModel is not None:
            self.__aiModel.Finish()
        if self.__agentEnv is not None:
            self.__agentEnv.Finish()
        self.__connect.Close()

    def Run(self, isTestMode=True):
        """
        Main framework, run AI test
        """
        if self.__RunAIFunc:
            self.__RunAIFunc(self.__agentEnv, self.__aiModel, isTestMode)
        else:
            self._DefaultRun(isTestMode)

    def StopAIAction(self):
        """
        Stop ai action when receive signal or msg
        """
        self.__outputAIAction = False
        self.__agentEnv.StopAction()
        self.__logger.info('Stop ai action')
        self.__agentEnv.UpdateEnvState(ENV_STATE_PAUSE_PLAYING, 'Pause ai playing')

    def RestartAIAction(self):
        """
        Restart ai action when receive signal or msg
        """
        self.__outputAIAction = True
        self.__agentEnv.RestartAction()
        self.__logger.info('Restart ai action')
        self.__agentEnv.UpdateEnvState(ENV_STATE_RESTORE_PLAYING, 'Resume ai playing')

    def _DefaultRun(self, isTestMode):
        self.__agentEnv.UpdateEnvState(ENV_STATE_WAITING_START, 'Wait episode start')
        while True:
            #wait new episode start
            self._WaitEpisode()
            self.__logger.info('Episode start')
            self.__agentEnv.UpdateEnvState(ENV_STATE_PLAYING, 'Episode start, ai playing')
            self.__aiModel.OnEpisodeStart()

            #run episode accroding to AI, until episode over
            self._RunEpisode(isTestMode)
            self.__logger.info('Episode over')
            self.__agentEnv.UpdateEnvState(ENV_STATE_OVER, 'Episode over')
            self.__aiModel.OnEpisodeOver()

            self.__agentEnv.UpdateEnvState(ENV_STATE_WAITING_START, 'Wait episode start')

        return

    def _WaitEpisode(self):
        while True:
            self._HandleMsg()

            if self.__agentEnv.IsEpisodeStart() is True:
                break
            time.sleep(0.001)

        return

    def _RunEpisode(self, isTestMode):
        while True:
            if self.__outputAIAction is True:
                if isTestMode is True:
                    self.__aiModel.TestOneStep()
                else:
                    self.__aiModel.TrainOneStep()
            else:
                self.__agentEnv.GetState()
                time.sleep(0.01)

            msgID = self._HandleMsg()
            if msgID == common_pb2.MSG_UI_GAME_OVER:
                break

            if self.__agentEnv.IsEpisodeOver() is True:
                break

        return

    def _HandleMsg(self):
        msg = self.__connect.RecvMsg()
        if msg is None:
            return common_pb2.MSG_NONE

        msgID = msg.eMsgID
        if msgID == common_pb2.MSG_UI_GAME_START:
            self.__logger.info('Enter new episode...')
            self.__aiModel.OnEnterEpisode()
        elif msgID == common_pb2.MSG_UI_GAME_OVER:
            self.__logger.info('Leave episode')
            self.__aiModel.OnLeaveEpisode()
        else:
            self.__logger.info('Unknown msg id')

        return msgID

    def _GetPluginInConfig(self):
        pluginCfgPath = util.ConvertToSDKFilePath(PLUGIN_CFG_FILE)
        if os.path.exists(pluginCfgPath):
            return self._LoadPlugInParams(pluginCfgPath)

        oldPluginCfgPath = util.ConvertToSDKFilePath(OLD_PLUGIN_CFG_FILE)
        if os.path.exists(oldPluginCfgPath):
            return self._LoadOldPlugInParams(oldPluginCfgPath)

        self.__logger.error('agentai cfg file {0} not exist.'.format(pluginCfgPath))
        return False

    def _LoadPlugInParams(self, pluginCfgPath):
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

    def _CreateAgentEnvObj(self):
        if self.__usePluginEnv is True:
            sys.path.append('PlugIn/ai')

        modulename = '{0}.{1}'.format(self.__envPackage, self.__envModule)
        envPackage = __import__(modulename)
        envModule = getattr(envPackage, self.__envModule)
        envClass = getattr(envModule, self.__envClass)
        self.__logger.info('agent env class: {0}'.format(envClass))
        self.__agentEnv = envClass()

        if self.__usePluginEnv is True:
            sys.path.pop()

    def _CreateAIModelObj(self):
        if self.__usePluginAIModel is True:
            sys.path.append('PlugIn/ai')
        else:
            sys.path.append('AgentAI/aimodel')

        modulename = '{0}.{1}'.format(self.__aiModelPackage, self.__aiModelModule)
        aiModelPackage = __import__(modulename)
        aiModelModule = getattr(aiModelPackage, self.__aiModelModule)
        aiModelClass = getattr(aiModelModule, self.__aiModelClass)
        self.__logger.info('aimodel class: {0}'.format(aiModelClass))
        self.__aiModel = aiModelClass()

        sys.path.pop()

    def _CreateRunFunc(self):
        if self.__useDefaultRunFunc is not True:
            sys.path.append('PlugIn/ai')

            modulename = '{0}.{1}'.format(self.__runFuncPackage, self.__runFuncModule)
            runFuncPackage = __import__(modulename)
            runFuncModule = getattr(runFuncPackage, self.__runFuncModule)
            self.__RunAIFunc = getattr(runFuncModule, self.__runFuncName)
            self.__logger.info('run function: {0}'.format(self.__RunAIFunc))

            sys.path.pop()

    def _RegisterService(self):
        regMsg = common_pb2.tagMessage()
        regMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        regMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_REGISTER
        regMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(regMsg) == 0:
            return True
        return False

    def _SendTaskReport(self, reportCode):
        taskMsg = common_pb2.tagMessage()
        taskMsg.eMsgID = common_pb2.MSG_TASK_REPORT
        taskMsg.stTaskReport.eTaskStatus = reportCode

        if self.__connect.SendMsg(taskMsg) == 0:
            return True
        return False


    def _UnRegisterService(self):
        unRegMsg = common_pb2.tagMessage()
        unRegMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        unRegMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_UNREGISTER
        unRegMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(unRegMsg) == 0:
            return True
        return False
