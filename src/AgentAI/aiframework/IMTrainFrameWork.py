# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import os

from protocol import common_pb2
from connect.BusConnect import BusConnect

from aimodel.ImitationLearning.MainImitationLearning import MainImitationLearning
from util.util import get_configure, create_source_response


# PROJECT_CONFIG_FILE = 'prj.aisdk'

class IMTrainFrameWork(object):
    """
    Imitation learnning train framework
    """

    def __init__(self):
        self.__logger = logging.getLogger('agent')
        self.__connect = BusConnect()
        self.__imTrain = MainImitationLearning()

    def Init(self):
        """
        Init tbus connect, register service to manager center
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

        return True

    def Train(self):
        """
        Load samples and train im model
        """
        self.__imTrain.GenerateImageSamples()
        self.__imTrain.TrainNetwork()

    def Finish(self):
        """
        Disconnect tbus, unregister service
        """
        self._UnRegisterService()
        self.__connect.Close()

    def _SendTaskReport(self, reportCode):
        taskMsg = common_pb2.tagMessage()
        taskMsg.eMsgID = common_pb2.MSG_TASK_REPORT
        taskMsg.stTaskReport.eTaskStatus = reportCode

        if self.__connect.SendMsg(taskMsg, BusConnect.PEER_NODE_MC) == 0:
            return True
        return False

    def _RegisterService(self):
        regMsg = common_pb2.tagMessage()
        regMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        regMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_REGISTER
        regMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(regMsg, BusConnect.PEER_NODE_MC) == 0:
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

    def _send_resource_info(self):
        self.__logger.info('send source info to mc, project_path: %s', os.environ.get('AI_SDK_PROJECT_FILE_PATH'))
        project_config_path = os.environ.get('AI_SDK_PROJECT_FILE_PATH')
        if not project_config_path:
            raise Exception('environ var(AI_SDK_PROJECT_FILE_PATH) is invalid')
        content = get_configure(project_config_path)

        if content['source'] is None:
            self.__logger.info("invalid the source in the project config, content: %s", content)
            return False
        self.__logger.info("the project config is %s, project_config_path: %s", str(content), project_config_path)
        source = content['source']
        source_res_message = create_source_response(source)

        if self.__connect.SendMsg(source_res_message, BusConnect.PEER_NODE_MC) == 0:
            self.__logger.info("send the source info to mc service success")
            return True
        self.__logger.warning("send the source info to mc service failed, please check")
        return False
