# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from abc import ABCMeta, abstractmethod

from AgentAPI import AgentAPIMgr
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
        return self.__connect.SendMsg(actionMsg, BusConnect.PEER_NODE_MC)

    def UpdateEnvState(self, stateCode, stateDescription):
        """
        Send agent state msg to MC when state change
        """
        stateMsg = common_pb2.tagMessage()
        stateMsg.eMsgID = common_pb2.MSG_AGENT_STATE
        stateMsg.stAgentState.eAgentState = int(stateCode)
        stateMsg.stAgentState.strAgentState = stateDescription
        return self.__connect.SendMsg(stateMsg, BusConnect.PEER_NODE_MC)

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
        self.logger.info("execute the default stop action")

    @abstractmethod
    def RestartAction(self):
        """
        Abstract interface, restart output game action when receive special msg or signal
        """
        self.logger.info("execute the default restart action")

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
        self.logger.info("execute the default reset action")

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

    def update_scene_task(self, result_dict, action_dict, agent_api):
        total_task = list(result_dict.keys())
        disable_task = list()

        for action_id in action_dict.keys():
            action_context = action_dict[action_id]
            self.logger.debug("update the action action_id: %s, action_context: %s",
                              str(action_id), str(action_context))
            scene_task_id = action_context.get('sceneTask')

            if scene_task_id is None:
                self.logger.debug("the action has no scene task, action_id:%s", str(action_id))
                continue

            if action_context['type'] == 'click':
                flag, px, py = self._get_position(result_dict, scene_task_id)
                self.logger.debug("get result of scene task id is %s, %s, %s", str(flag), str(px), str(py))
                if flag is True:
                    action_context['updateBtn'] = True
                    action_context['updateBtnX'] = px
                    action_context['updateBtnY'] = py
                    disable_task.append(scene_task_id)

        # 发送消息给gameReg
        enable_task = [total_task[n] for n in range(len(total_task)) if total_task[n] not in disable_task]
        self.logger.debug("the enable_task is %s and disable_task is %s", str(enable_task), str(disable_task))
        self.__send_update_task(disable_task, enable_task, agent_api)

    @staticmethod
    def _get_position(result_dict, task_id):
        state = False
        px = -1
        py = -1

        reg_results = result_dict.get(task_id)
        if reg_results is None:
            return state, px, py

        for result in reg_results:
            x = result['ROI']['x']
            y = result['ROI']['y']
            w = result['ROI']['w']
            h = result['ROI']['h']

            if x > 0 and y > 0:
                state = True
                px = int(x + w/2)
                py = int(y + h/2)
                break

        return state, px, py

    def __send_update_task(self, disable_task, enable_task, agent_api):
        task_flag_dict = dict()
        for taskID in disable_task:
            task_flag_dict[taskID] = False

        for taskID in enable_task:
            task_flag_dict[taskID] = True

        ret = agent_api.SendCmd(AgentAPIMgr.MSG_SEND_TASK_FLAG, task_flag_dict)

        if not ret:
            self.logger.error('AgentAPI MSG_SEND_TASK_FLAG failed, task_flag_dict:{}'.format(task_flag_dict))
            return False

        self.logger.debug("AgentAPI MSG_SEND_TASK_FLAG success, task_flag_dict:{}".format(task_flag_dict))
        return True
