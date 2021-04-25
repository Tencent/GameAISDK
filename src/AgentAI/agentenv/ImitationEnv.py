# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import time

import cv2
from AgentAPI import AgentAPIMgr
from aimodel.ImitationLearning.MainImitationLearning import MainImitationLearning
from util import util

from .GameEnv import GameEnv
from .ImitationAction import ImitationAction

TASK_CFG_FILE = 'cfg/task/gameReg/Task.json'
TASK_REFER_CFG_FILE = 'cfg/task/gameReg/Refer.json'
IM_ENV_CFG_FILE = 'cfg/task/agent/ImitationEnv.json'

REG_GROUP_ID = 1

GAME_STATE_INVALID = 0
GAME_STATE_RUN = 1
GAME_STATE_OVER = 2



class ImitationEnv(GameEnv):
    """
    Env class for imitation learning
    """

    def __init__(self):
        GameEnv.__init__(self)
        self.__actionCtrl = ImitationAction()
        self.__beginTaskID = list()
        self.__overTaskID = list()

        self.__frameIndex = -1
        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()

        self.mainImitationLearning = MainImitationLearning()
        self.mainImitationLearning.Init()

        self.__inputImgWidth = self.mainImitationLearning.inputWidth
        self.__inputImgHeight = self.mainImitationLearning.inputHeight

        self.__timeMs = self.mainImitationLearning.actionTimeMs

        self.__gameState = GAME_STATE_OVER
        self.__isTerminal = False

        self.__imgHeight = 0
        self.__imgWidth = 0

    def Init(self):
        """
        Int function for env
        """
        taskCfgFile = util.ConvertToSDKFilePath(TASK_CFG_FILE)
        taskReferCfgFile = util.ConvertToSDKFilePath(TASK_REFER_CFG_FILE)
        if not self.__agentAPI.Initialize(taskCfgFile, referFile=taskReferCfgFile):
            self.logger.error('Agent API Init Failed')
            return False

        if not self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, REG_GROUP_ID):
            self.logger.error('send message failed')
            return False

        if not self._LoadGameState():
            return False

        return True

    def Finish(self):
        """
        Finish env
        """
        self.__agentAPI.Release()
        self.__actionCtrl.Finish()

    def GetActionSpace(self):
        """
        Get action number
        """
        self.logger.info('execute the default get action space in the imitation env')

    def Reset(self):
        """
        Reset env
        """
        self.logger.info('execute the default reset in the imitation env')

    def RestartAction(self):
        """
        Restart action
        """
        self.logger.info('execute the default restart action in the imitation env')

    def StopAction(self):
        """
        Stop action
        """
        self.logger.info('execute the default stop action in the imitation env')

    def DoAction(self, action, *args, **kwargs):
        """
        Do specific action
        """
        self._OutPutAction(action)

    def _OutPutAction(self, actionIndex):
        self.__actionCtrl.DoAction(actionIndex,
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
        self.__actionCtrl.Initialize(self.__imgHeight, self.__imgWidth)
        self.logger.info('init:  height: {}  width: {}'.format(self.__imgHeight, self.__imgWidth))

    def OnEpisodeOver(self):
        """
        End env when episode is over
        """
        pass

    def _GetBtnPostion(self, resultDict, taskID):
        state = False
        px = -1
        py = -1

        regResults = resultDict.get(taskID)
        if regResults is None:
            return (state, px, py)

        for result in regResults:
            x = result['ROI']['x']
            y = result['ROI']['y']
            w = result['ROI']['w']
            h = result['ROI']['h']

            if x > 0 and y > 0:
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

            self.logger.debug("the result of game reg is %s, beginTask: %s, endTask: %s",
                              str(result), str(self.__beginTaskID), str(self.__overTaskID))

            self._ParseGameState(result)
            self._ParseBtnPostion(result)
            self._ParseSceneInfo(result)

            break

        return gameInfo

    def _ParseGameState(self, resultDict):
        for taskID in self.__beginTaskID:
            flag, _, _ = util.get_button_state(resultDict, taskID)
            if flag is True:
                self.__gameState = GAME_STATE_RUN
                self.logger.debug("the game state set game run state")

        for taskID in self.__overTaskID:
            flag, _, _ = util.get_button_state(resultDict, taskID)
            if flag is True:
                self.__gameState = GAME_STATE_OVER
                self.logger.debug("the game state set game over state")

    def _ParseBtnPostion(self, resultDict):
        totalTask = list(resultDict.keys())
        disableTask = list()

        for _, actionContext in self.__actionCtrl.actionsContextDict.items():
            sceneTaskID = actionContext.get('sceneTask')
            if sceneTaskID is None:
                continue

            if actionContext['type'] == 'click':
                flag, updateBtnX, updateBtnY = self._GetBtnPostion(resultDict, sceneTaskID)
                if flag is True:
                    actionContext['updateBtn'] = True
                    actionContext['updateBtnX'] = updateBtnX
                    actionContext['updateBtnY'] = updateBtnY
                    disableTask.append(sceneTaskID)

        enableTask = [totalTask[n] for n in range(len(totalTask)) if totalTask[n] not in disableTask]
        self.logger.debug("the enable_task is %s and disable_task is %s", str(enableTask), str(disableTask))
        self.SendUpdateTask(disableTask, enableTask)

    def _ParseSceneInfo(self, resultDict):
        pass

    def _LoadGameState(self):
        imEnvFile = util.ConvertToSDKFilePath(IM_ENV_CFG_FILE)
        try:
            with open(imEnvFile, 'r', encoding='utf-8') as file:
                jsonStr = file.read()
                gameStateCfg = json.loads(jsonStr)
                self.logger.info("the config of env is {}".format(gameStateCfg))
                self.__beginTaskID.extend(gameStateCfg['beginTaskID'])
                self.__overTaskID.extend(gameStateCfg['overTaskID'])
        except Exception as err:
            self.logger.error('Load game state file %s error! Error msg: %s', imEnvFile, str(err))
            return False

        return True

    def SendUpdateTask(self, disableTask, enableTask):
        taskFlagDict = dict()
        for taskID in disableTask:
            taskFlagDict[taskID] = False

        for taskID in enableTask:
            taskFlagDict[taskID] = True

        ret = self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_TASK_FLAG, taskFlagDict)
        if not ret:
            self.logger.error('AgentAPI MSG_SEND_TASK_FLAG failed')
            return False
        return True
