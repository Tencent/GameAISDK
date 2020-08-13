# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import os
import sys

import configparser
import cv2

from AgentAPI import AgentAPIMgr
from util import util

from aimodel.ImitationLearning.MainImitationLearning import MainImitationLearning
from .ImitationAction import ImitationAction
from .GameEnv import GameEnv

TASK_CFG_FILE = 'cfg/task/gameReg/Task.json'
TASK_REFER_CFG_FILE = 'cfg/task/gameReg/Refer.json'

REG_GROUP_ID = 1

START_TASK_ID = 1

GAME_STATE_INVALID = 0
GAME_STATE_RUN = 1
GAME_STATE_FINISH = 2

DATA_ROOT_DIR = '../'
if os.environ.get('AI_SDK_PATH') is not None:
    DATA_ROOT_DIR = os.environ.get('AI_SDK_PATH') + '/'


class ImitationEnv(GameEnv):
    """
    Env class for imitation learning
    """

    def __init__(self):
        GameEnv.__init__(self)
        self.actionCtrl = ImitationAction()
        self.__frameIndex = -1

        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()

        self.mainImitationLearning = MainImitationLearning()
        self.mainImitationLearning.Init()

        self.__inputImgWidth = self.mainImitationLearning.inputWidth
        self.__inputImgHeight = self.mainImitationLearning.inputHeight

        self.__timeMs = self.mainImitationLearning.actionTimeMs

        self.__gameState = GAME_STATE_FINISH

    def Init(self):
        """
        Int function for env
        """
        taskCfgFile = util.ConvertToSDKFilePath(TASK_CFG_FILE)
        taskReferCfgFile = util.ConvertToSDKFilePath(TASK_REFER_CFG_FILE)
        ret = self.__agentAPI.Initialize(taskCfgFile, referFile=taskReferCfgFile)
        if not ret:
            self.logger.error('Agent API Init Failed')
            return False

        ret = self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, REG_GROUP_ID)
        if not ret:
            self.logger.error('send message failed')
            return False

        return True

    def Finish(self):
        """
        Finish env
        """
        self.__agentAPI.Release()
        self.actionCtrl.Finish()

    def GetActionSpace(self):
        """
        Get action number
        """
        pass

    def Reset(self):
        """
        Reset env
        """
        pass

    def RestartAction(self):
        """
        Restart action
        """
        pass

    def StopAction(self):
        """
        Stop action
        """
        pass

    def DoAction(self, action, *args, **kwargs):
        """
        Do specific action
        """
        self._OutPutAction(action)

    def _OutPutAction(self, actionIndex):
        self.actionCtrl.DoAction(actionIndex,
                                 self.__imgHeight,
                                 self.__imgWidth,
                                 self.__timeMs,
                                 self.__frameIndex)

    def GetState(self):
        """
        Get game data , image and state
        """
        gameInfo = self._GetGameInfo()
        image = gameInfo['image']
        self.__frameIndex = gameInfo['frameSeq']
        state = self.__gameState
        img = image
        img = cv2.resize(img, (self.__inputImgWidth, self.__inputImgHeight))
        self.__isTerminal = True

        if state == GAME_STATE_RUN:
            self.__isTerminal = False

        return img, self.__isTerminal

    def IsTrainable(self):
        """
        Whether model is trainable
        """
        return True

    def IsEpisodeStart(self):
        """
        Whether game is begin
        """
        _ = self._GetGameInfo()
        if self.__gameState == GAME_STATE_RUN:
            self.__isTerminal = False
            return True

        return False

    def IsEpisodeOver(self):
        """
        Whether game is over
        """
        return self.__isTerminal

    def OnEpisodeStart(self):
        """
        Initital env when episode is begin
        """
        self.actionCtrl.Initialize(self.__imgHeight, self.__imgWidth)
        self.logger.info('init:  height: {}  width: {}'.format(self.__imgHeight, self.__imgWidth))

    def OnEpisodeOver(self):
        """
        End env when episode is over
        """
        pass

    def _GetBtnState(self, resultDict, taskID):
        state = False
        px = -1
        py = -1

        regResults = resultDict.get(taskID)
        if regResults is None:
            return (state, px, py)

        for item in regResults:
            flag = item[0]
            x = item[1]
            y = item[2]
            w = item[3]
            h = item[4]

            if flag is True:
                state = True
                px = int(x + w/2)
                py = int(y + h/2)
                break

        return (state, px, py)

    def _GetGameInfo(self):
        gameInfo = None

        while True:
            gameInfo = self.__agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)
            if gameInfo is None:
                time.sleep(0.002)
                continue

            result = gameInfo['result']
            if result is None:
                time.sleep(0.002)
                continue

            image = gameInfo['image']
            self.__imgHeight = image.shape[0]
            self.__imgWidth = image.shape[1]

            self.__gameState = GAME_STATE_RUN
            break

        return gameInfo
