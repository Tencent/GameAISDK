# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import os
import sys

from protocol import common_pb2
from connect.BusConnect import BusConnect
from aimodel.ImitationLearning.MainImitationLearning import MainImitationLearning

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

        if self.__connect.SendMsg(taskMsg) == 0:
            return True
        return False

    def _RegisterService(self):
        regMsg = common_pb2.tagMessage()
        regMsg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        regMsg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_REGISTER
        regMsg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_AI

        if self.__connect.SendMsg(regMsg) == 0:
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
