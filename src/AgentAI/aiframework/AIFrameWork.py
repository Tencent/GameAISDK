# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time
import os

from protocol import common_pb2
from connect.BusConnect import BusConnect
from .AIPlugin import AIPlugin
from util import util

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
        self.__logger = logging.getLogger('agent')
        self.__aiModel = None
        self.__agentEnv = None
        self.__runAIFunc = None
        self.__aiPlugin = AIPlugin()
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

        if self._send_resource_info() is not True:
            self.__logger.error('send the source info failed.')
            self._SendTaskReport(common_pb2.PB_TASK_INIT_FAILURE)
            return False

        if self._InitAIObject() is True:
            self.__logger.info('AIFrameWork.Init, _SendTaskReport PB_TASK_INIT_SUCCESS to MC.')
            self._SendTaskReport(common_pb2.PB_TASK_INIT_SUCCESS)
        else:
            self.__logger.error('AIFrameWork.Init, _SendTaskReport PB_TASK_INIT_FAILURE to MC.')
            self._SendTaskReport(common_pb2.PB_TASK_INIT_FAILURE)
            return False

        return True

    def _InitAIObject(self):
        if self.__aiPlugin.Init() is not True:
            return False

        self.__agentEnv = self.__aiPlugin.CreateAgentEnvObj()
        self.__aiModel = self.__aiPlugin.CreateAIModelObj()

        if self.__aiModel is None or self.__agentEnv is None:
            self.__logger.error('Create agent env or aimodel object failed.')
            return False

        self.__runAIFunc = self.__aiPlugin.CreateRunFunc()
        if self.__aiPlugin.UseDefaultRun() is not True and self.__runAIFunc is None:
            self.__logger.error('Create run function failed.')
            return False

        if self.__agentEnv.Init() is not True:
            self.__logger.error('Agent env init failed.')
            return False
        self.__logger.info('AIFrameWork.InitAIObject agentEnv init success')

        if self.__aiModel.Init(self.__agentEnv) is not True:
            self.__logger.error('AI model init failed.')
            return False

        self.__logger.info('AIFrameWork.InitAIObject aiModel init success')
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
        if self.__runAIFunc:
            logging.debug("execute the run ai func")
            self.__runAIFunc(self.__agentEnv, self.__aiModel, isTestMode)
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
        self.__logger.debug("execute the default run")
        self.__agentEnv.UpdateEnvState(ENV_STATE_WAITING_START, 'Wait episode start')
        while True:
            #wait new episode start
            self.__logger.debug("begin to wait the start")
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
            time.sleep(0.1)

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
        msg = self.__connect.RecvMsg(BusConnect.PEER_NODE_MC)
        if msg is None:
            return common_pb2.MSG_NONE

        msgID = msg.eMsgID
        self.__logger.info('the message from mc is %s, msgID: %d'.format(msg, msgID))

        if msgID == common_pb2.MSG_UI_GAME_START:
            self.__logger.info('Enter new episode...')
            self.__aiModel.OnEnterEpisode()
        elif msgID == common_pb2.MSG_UI_GAME_OVER:
            self.__logger.info('Leave episode')
            self.__aiModel.OnLeaveEpisode()
        else:
            self.__logger.info('Unknown msg id')

        return msgID

    def _send_resource_info(self):
        self.__logger.info('send source info to mc, project_path:%s'.format(os.environ.get('AI_SDK_PROJECT_FILE_PATH')))
        project_config_path = os.environ.get('AI_SDK_PROJECT_FILE_PATH')
        if not project_config_path:
            raise Exception('environ var(AI_SDK_PROJECT_FILE_PATH) is invalid')

        content = util.get_configure(project_config_path)
        if not content:
            self.__logger.warning("failed to get project config content, file:%s".format(project_config_path))
            return False

        if not content.get('source'):
            self.__logger.warning("invalid the source in the project config, content:%s".format(content))
            content['source'] = {}
            content['source']['device_type'] = "Android"
            content['source']['platform'] = "Local"
            content['source']['long_edge'] = 1280

        # if content['source'] is None:
        #     self.__logger.info("invalid the source in the project config, content:{}", content)
        #     return False
        self.__logger.info("the project config is {}, project_config_path:{}".format(content, project_config_path))
        source = content['source']
        source_res_message = util.create_source_response(source)
        self.__logger.info("send the source message to mc, source_res_message:{}".format(source_res_message))

        # 发送设备源信息到MC, 由MC把信息缓存起来
        if self.__connect.SendMsg(source_res_message, BusConnect.PEER_NODE_MC) == 0:
            self.__logger.info("send the source info to mc service success")
            return True

        self.__logger.warning("send the source info to mc service failed, please check")
        return False

    def _RegisterService(self):
        regMsg = common_pb2.tagMessage()
        regMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        regMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_REGISTER
        regMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(regMsg, BusConnect.PEER_NODE_MC) == 0:
            return True
        return False

    def _SendTaskReport(self, reportCode):
        taskMsg = common_pb2.tagMessage()
        taskMsg.eMsgID = common_pb2.MSG_TASK_REPORT
        taskMsg.stTaskReport.eTaskStatus = reportCode

        if self.__connect.SendMsg(taskMsg, BusConnect.PEER_NODE_MC) == 0:
            return True
        return False

    def _UnRegisterService(self):
        unRegMsg = common_pb2.tagMessage()
        unRegMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        unRegMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_UNREGISTER
        unRegMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(unRegMsg, BusConnect.PEER_NODE_MC) == 0:
            return True
        return False
