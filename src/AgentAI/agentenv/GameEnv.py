# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import configparser
from abc import ABCMeta, abstractmethod

from connect.BusConnect import BusConnect
from protocol import common_pb2

class GameEnv(object):
    """
    Game envionment interface class, define abstract interface
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.logger = logging.getLogger('agent')
        self.__connect = BusConnect()

        if self.__connect.Connect() is not True:
            self.logger.error('Game env connect failed.')
            raise Exception('Game env connect failed.')

    def SendAction(self, actionMsg):
        """
        Send action msg to MC to do action
        """
        return self.__connect.SendMsg(actionMsg)

    def UpdateEnvState(self, stateCode, stateDescription):
        """
        Send agent state msg to MC when state change
        """
        stateMsg = common_pb2.tagMessage()
        stateMsg.eMsgID = common_pb2.MSG_AGENT_STATE
        stateMsg.stAgentState.eAgentState = int(stateCode)
        stateMsg.stAgentState.strAgentState = stateDescription
        return self.__connect.SendMsg(stateMsg)

    @abstractmethod
    def Init(self):
        """
        Abstract interface, Init game env object
        """
        raise NotImplementedError()

    @abstractmethod
    def Finish(self):
        """
        Abstract interface, Exit game env object
        """
        raise NotImplementedError()

    @abstractmethod
    def GetActionSpace(self):
        """
        Abstract interface, return number of game action
        """
        raise NotImplementedError()

    @abstractmethod
    def DoAction(self, action, *args, **kwargs):
        """
        Abstract interface, do game action in game env
        """
        raise NotImplementedError()

    @abstractmethod
    def StopAction(self):
        """
        Abstract interface, stop game action when receive special msg or signal
        """
        pass

    @abstractmethod
    def RestartAction(self):
        """
        Abstract interface, restart output game action when receive special msg or signal
        """
        pass

    @abstractmethod
    def GetState(self):
        """
        Abstract interface, return game state usually means game image or game data
        """
        raise NotImplementedError()

    @abstractmethod
    def Reset(self):
        """
        Abstract interface, reset date or state in game env
        """
        pass

    @abstractmethod
    def IsEpisodeStart(self):
        """
        Abstract interface, check whether episode start or not
        """
        return False

    @abstractmethod
    def IsEpisodeOver(self):
        """
        Abstract interface, check whether episode over or not
        """
        return True
