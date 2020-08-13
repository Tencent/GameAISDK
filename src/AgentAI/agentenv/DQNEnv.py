# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import os
import configparser
import json

import numpy as np
import cv2

from actionmanager import ActionController
from AgentAPI import AgentAPIMgr
from util import util
from .GameEnv import GameEnv


ACTION_CFG_FILE = 'cfg/task/agent/DQNAction.json'
ENV_CFG_FILE = 'cfg/task/agent/DQNEnv.ini'
TASK_CFG_FILE = 'cfg/task/gameReg/Task.json'

REG_GROUP_ID = 1

BEGIN_TASK_ID = 1
WIN_TASK_ID = 2
LOSE_TASK_ID = 3
DATA_TASK_ID = 4

GAME_STATE_INVALID = 0
GAME_STATE_RUN = 1
GAME_STATE_WIN = 2
GAME_STATE_LOSE = 3

class DQNEnv(GameEnv):
    """
    Game env implement for DQN
    """

    def __init__(self):
        GameEnv.__init__(self)
        self._LoadCfgFilePath()
        self._LoadEnvParams()
        self.__actionController = ActionController.ActionController()
        self.__actionController.Initialize(self.__actionCfgFile)
        self.Reset()
        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()
        self.__frameIndex = -1

    def Init(self):
        """
        Initialize game env object, create recognize task use AgentAPI
        """
        ret = self.__agentAPI.Initialize(self.__recognizeCfgFile)
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
        Exit game env after object used, release AgentAPI
        """
        self.__agentAPI.Release()

    def GetActionSpace(self):
        """
        Return number of game action
        """
        return self.__actionController.GetActionNum()

    def DoAction(self, action, *args, **kwargs):
        """
        Output game action use ActionAPI
        action: one hot vector
        """
        actionIndex = np.argmax(action)
        self.__actionController.DoAction(actionIndex, self.__frameIndex)

    def ResetAction(self):
        """
        Reset game action use ActionAPI
        """
        self.__actionController.Reset()

    def StopAction(self):
        """
        Stop game action when receive special msg or signal
        """
        self.__actionController.Reset()

    def RestartAction(self):
        """
        Restart output game action when receive special msg or signal
        """
        self.__actionController.Reset()

    def GetState(self):
        """
        Return (s, r, t): game image, reward, terminal
        """

        #get game data , image and state
        gameInfo = self._GetGameInfo()
        data = gameInfo['result'].get(DATA_TASK_ID)[0]['num']
        image = gameInfo['image']
        self.__frameIndex = gameInfo['frameSeq']
        state = self.__gameState

        imgHeight = image.shape[0]
        imgWidth = image.shape[1]

        img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img = img[self.__beginRow:self.__endRow, self.__beginColumn:self.__endColumn]
        if imgWidth < imgHeight:
            img = cv2.transpose(img)
            img = cv2.flip(img, 1)

        img = cv2.resize(img, (176, 108))
        reward = self._CaculateReward(data)

        self.__isTerminal = True
        if state == GAME_STATE_LOSE:
            reward = self.__loseReward
        elif state == GAME_STATE_WIN:
            reward = self.__winReward
        elif state == GAME_STATE_RUN:
            self.__isTerminal = False
        else:
            self.logger.error('error game state')

        if data == -1 and self.__isTerminal is not True:
            self.logger.debug('detect data -1, set 0 reward')
            reward = 0

        self.logger.debug('data: {0} reward: {1}'.format(data, reward))

        return img, reward, self.__isTerminal

    def Reset(self):
        """
        Reset date, action or state in game env
        """
        self.__lastScore = self.__initScore
        self.__lastRewardScore = self.__initScore
        self.__scoreRepeatedTimes = 0
        self.__isTerminal = True
        self.__gameState = GAME_STATE_INVALID
        self.__actionController.Reset()

    def IsTrainable(self):
        """
        Check whether the game state can used for training DQN model or not
        """
        return True

    def IsEpisodeStart(self):
        """
        Check whether episode start or not, according to recognize resulet
        """
        self._GetGameInfo()
        if self.__gameState == GAME_STATE_RUN:
            self.__isTerminal = False
            return True

        return False

    def IsEpisodeOver(self):
        """
        Check whether episode over or not, according to recognize resulet
        """
        return self.__isTerminal

    def _GetBtnState(self, resultDict, taskID):
        state = False
        px = -1
        py = -1
        regResults = resultDict.get(taskID)
        if regResults is None:
            return (state, px, py)

        for item in regResults:
            flag = item['flag']
            if flag:
                x = item['boxes'][0]['x']
                y = item['boxes'][0]['y']
                w = item['boxes'][0]['w']
                h = item['boxes'][0]['h']

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

            flag, _, _ = self._GetBtnState(result, BEGIN_TASK_ID)
            if flag is True:
                self.__gameState = GAME_STATE_RUN
                self.logger.debug('frameindex = {0}, detect begin'.format(gameInfo['frameSeq']))

            flag, _, _ = self._GetBtnState(result, WIN_TASK_ID)
            if flag is True:
                self.__gameState = GAME_STATE_WIN
                self.logger.debug('frameindex = {0}, detect win'.format(gameInfo['frameSeq']))

            flag, _, _ = self._GetBtnState(result, LOSE_TASK_ID)
            if flag is True:
                self.__gameState = GAME_STATE_LOSE
                self.logger.debug('frameindex = {0}, detect lose'.format(gameInfo['frameSeq']))

            data = None
            if result.get(DATA_TASK_ID) is not None:
                data = result.get(DATA_TASK_ID)[0]

            if data is None:
                time.sleep(0.002)
                continue
            else:
                break

        return gameInfo

    def _LoadEnvParams(self):
        if os.path.exists(self.__envCfgFile):
            config = configparser.ConfigParser()
            config.read(self.__envCfgFile)

            self.__beginColumn = config.getint('IMAGE_ROI', 'StartX')
            self.__beginRow = config.getint('IMAGE_ROI', 'StartY')
            self.__cutWidth = config.getint('IMAGE_ROI', 'Width')
            self.__cutHeight = config.getint('IMAGE_ROI', 'Height')
            self.__endColumn = self.__beginColumn + self.__cutWidth
            self.__endRow = self.__beginRow + self.__cutHeight

            self.__initScore = config.getfloat('REWARD_RULE', 'InitScore')
            self.__maxScoreRepeatedTimes = config.getint('REWARD_RULE', 'MaxScoreRepeatedTimes')
            self.__rewardOverRepeated = config.getfloat('REWARD_RULE', 'RewardOverRepeatedTimes')

            self.__winReward = config.getfloat('REWARD_RULE', 'WinReward')
            self.__loseReward = config.getfloat('REWARD_RULE', 'LoseReward')

            self.__maxRunningReward = config.getfloat('REWARD_RULE', 'MaxRunningReward')
            self.__minRunningReward = config.getfloat('REWARD_RULE', 'MinRunningReward')
            self.__rewardPerPostive = config.getfloat('REWARD_RULE', 'RewardPerPostiveSection')
            self.__rewardPerNegtive = config.getfloat('REWARD_RULE', 'RewardPerNegtiveSection')
            self.__scorePerSection = config.getfloat('REWARD_RULE', 'ScorePerSection')
        else:
            self.logger.error('dqn_env cfg file not exist.')

    def _CaculateReward(self, curScore):
        reward = 0

        if abs(curScore - self.__lastRewardScore) >= self.__scorePerSection:
            if curScore > self.__lastRewardScore:
                sections = int((curScore - self.__lastRewardScore)/self.__scorePerSection)
                reward = sections * self.__rewardPerPostive
            else:
                sections = int((self.__lastRewardScore - curScore)/self.__scorePerSection)
                reward = sections * self.__rewardPerNegtive

            self.__lastRewardScore = curScore

            if reward > self.__maxRunningReward:
                reward = self.__maxRunningReward
            elif reward < self.__minRunningReward:
                reward = self.__minRunningReward

        if self.__lastScore == curScore:
            self.__scoreRepeatedTimes += 1
            if self.__scoreRepeatedTimes >= self.__maxScoreRepeatedTimes:
                reward = self.__rewardOverRepeated
        else:
            self.__scoreRepeatedTimes = 0

        self.__lastScore = curScore

        return reward

    def _LoadCfgFilePath(self):
        self.__actionCfgFile = util.ConvertToSDKFilePath(ACTION_CFG_FILE)
        self.__envCfgFile = util.ConvertToSDKFilePath(ENV_CFG_FILE)
        self.__recognizeCfgFile = util.ConvertToSDKFilePath(TASK_CFG_FILE)
