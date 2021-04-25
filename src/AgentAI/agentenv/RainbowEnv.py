# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import time

import cv2
import numpy as np
from AgentAPI import AgentAPIMgr
from actionmanager import ActionController
from agentenv.GameEnv import GameEnv
from util import util

ACTION_CFG_FILE = 'cfg/task/agent/RainbowAction.json'
ENV_CFG_FILE = 'cfg/task/agent/RainbowLearning.json'
TASK_CFG_FILE = 'cfg/task/gameReg/Task.json'

REG_GROUP_ID = 1

GAME_STATE_INVALID = 0
GAME_STATE_RUN = 1
GAME_STATE_WIN = 2
GAME_STATE_LOSE = 3

IMAGE_WIDTH = 84
IMAGE_HEIGHT = 84

SHOW_ENV = True


class RainbowEnv(GameEnv):
    """
    Proxy Env for Rainbow
    """

    def __init__(self):
        GameEnv.__init__(self)
        # convert action cfg path and create action controller object
        self.__actionCfgPath = util.ConvertToSDKFilePath(ACTION_CFG_FILE)
        self.__actionController = ActionController.ActionController()

        # convert env cfg path and load env parameters
        self.__envCfgPath = util.ConvertToSDKFilePath(ENV_CFG_FILE)
        self._load_env_params(self.__envCfgPath)

        # convert task cfg path and create agent API object
        self.__taskCfgPath = util.ConvertToSDKFilePath(TASK_CFG_FILE)
        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()

        self.__gameState = GAME_STATE_INVALID
        self.__frameIndex = 0

        self.__episodeCount = 0
        self.__episodeReward = 0

        self.Reset()

    def Init(self):
        """
        Initialize action controller and create recognize task use AgentAPI
        """
        self.logger.debug("begin to init rainbow env")
        ret = self.__actionController.Initialize(self.__actionCfgPath)
        if not ret:
            self.logger.error('initialize action controller failed')
            return False

        ret = self.__agentAPI.Initialize(self.__taskCfgPath)
        if not ret:
            self.logger.error('initialize agent API failed')
            return False

        ret = self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, REG_GROUP_ID)
        if not ret:
            self.logger.error('send agent API message failed')
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

    def DoAction(self, actionIndex, *args, **kwargs):
        """
        Output game action use ActionAPI
        """
        self.__actionController.DoAction(actionIndex, self.__frameIndex)

    def ResetAction(self):
        """
        Reset game action use ActionAPI
        """
        self.__actionController.Reset()

    def GetState(self):
        """
        Return (i, r, d, idx): image, reward, done, frameIndex
        """

        # get game data, image and state
        self.logger.debug("begin to get state from game reg")
        gameInfo = self._GetGameInfo()
        self.__gameState = self._GetGameState(gameInfo)
        self.logger.debug("get the game state, game state = {}".format(self.__gameState))
        self.__frameIndex = gameInfo['frameSeq']

        image = self._GetImage(gameInfo)
        reward = self._GetReward(gameInfo)
        done = self._GetDone()

        self.logger.debug("get the reward is {}".format(reward))

        if SHOW_ENV is True:
            if gameInfo['result'].get(self.__score_task_id)[0]['flag'] is True:
                cv2.imshow('Env Image', image)
                cv2.waitKey(1)

        if done is True:
            self.logger.info('episode over: frame index = {}, episode count = {}, episode reward = {:.2f}'.format(
                self.__frameIndex, self.__episodeCount, self.__episodeReward))
            self.__episodeCount += 1
            self.__episodeReward = 0
        else:
            self.__episodeReward += reward

        if gameInfo['result'].get(self.__score_task_id)[0]['flag'] is True:
            self.logger.debug("get the state from game reg, reward:{}, frameIndex:{}".format(reward, self.__frameIndex))
            return [image, reward, done, self.__frameIndex]
        else:
            self.logger.debug("get the state from game reg state is none")
            return None

    def Reset(self):
        """
        Reset action or state in game env
        """
        self.__gameState = GAME_STATE_INVALID

        self.__lastScore = self.__initScore
        self.__lastRewardScore = self.__initScore
        self.__scoreRepeatedTimes = 0

        self.__actionController.Reset()

    def IsEpisodeStart(self):
        """
        Check whether episode start or not, according to recognize result
        """
        self.logger.debug("check the Epsiode Start")
        gameInfo = self._GetGameInfo()
        self.__gameState = self._GetGameState(gameInfo)

        if self.__gameState == GAME_STATE_RUN:
            return True
        else:
            return False

    def IsEpisodeOver(self):
        """
        Check whether episode over or not, according to recognize result
        """
        if self.__gameState == GAME_STATE_WIN or self.__gameState == GAME_STATE_LOSE:
            return True
        else:
            return False

    def _GetGameInfo(self):
        while True:
            gameInfo = self.__agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)
            if gameInfo is None:
                # self.logger.debug('The game info is none')
                time.sleep(0.002)
                continue

            #self.logger.debug('The game info is {0}'.format(gameInfo))
            result = gameInfo['result']
            self.logger.debug('The result of game reg is {0}'.format(result))
            if result is None:
                time.sleep(0.002)
                continue
            else:
                break

        return gameInfo

    def _GetGameState(self, gameInfo):
        gameState = GAME_STATE_INVALID
        result = gameInfo['result']

        flag, _, _ = self._GetBtnInfo(result, self.__start_task_id)
        if flag is True:
            self.logger.debug('frame index = {}, detect run'.format(gameInfo['frameSeq']))
            gameState = GAME_STATE_RUN

        flag, _, _ = self._GetBtnInfo(result, self.__win_task_id)
        if flag is True:
            self.logger.info('frame index = {}, detect win'.format(gameInfo['frameSeq']))
            gameState = GAME_STATE_WIN

        flag, _, _ = self._GetBtnInfo(result, self.__lose_task_id)
        if flag is True:
            self.logger.debug('frame index = {}, detect lose'.format(gameInfo['frameSeq']))
            gameState = GAME_STATE_LOSE

        self.update_scene_task(result, self.__actionController.get_action_dict(), self.__agentAPI)

        return gameState

    def _GetBtnInfo(self, resultDict, taskID):
        flag = False
        px = -1
        py = -1
        results = resultDict.get(taskID)
        if results is None:
            return flag, px, py

        for item in results:
            if item['flag'] is True:
                x = item['boxes'][0]['x']
                y = item['boxes'][0]['y']
                w = item['boxes'][0]['w']
                h = item['boxes'][0]['h']

                flag = True
                px = int(x + w / 2)
                py = int(y + h / 2)
                break

        return flag, px, py

    def _GetImage(self, gameInfo):
        # colorImg = gameInfo['image']
        # grayImg = cv2.cvtColor(colorImg, cv2.COLOR_BGR2GRAY)
        #
        # roiImg = grayImg[self.__top:self.__down, self.__left:self.__right]
        # image = cv2.resize(roiImg, (IMAGE_WIDTH, IMAGE_HEIGHT))

        colorImg = gameInfo['image']
        sp = colorImg.shape
        self.logger.debug("the width {} and the height {} of real image".format(sp[1], sp[0]))
        self.__actionController.SetSolution(sp[1], sp[0])

        grayImg = cv2.cvtColor(colorImg, cv2.COLOR_BGR2GRAY)
        top = cv2.resize(grayImg, (IMAGE_WIDTH, int(IMAGE_HEIGHT / 2)))

        roiImg = grayImg[self.__top:self.__down, self.__left:self.__right]
        down = cv2.resize(roiImg, (IMAGE_WIDTH, int(IMAGE_HEIGHT / 2)))

        image = np.zeros([IMAGE_WIDTH, IMAGE_HEIGHT], dtype=np.uint8)
        image[0:int(IMAGE_HEIGHT / 2), :] = top
        image[int(IMAGE_HEIGHT / 2):, :] = down

        return image

    def _GetReward(self, gameInfo):
        speed = gameInfo['result'].get(self.__score_task_id)[0]['num']
        self.logger.debug("get the speed of the game, speed:{}".format(speed))
        reward = self._CaculateReward(speed)

        if self.__gameState == GAME_STATE_WIN:
            reward = self.__winReward

        if self.__gameState == GAME_STATE_LOSE:
            reward = self.__loseReward

        return reward

    def _GetDone(self):
        if self.__gameState == GAME_STATE_WIN or self.__gameState == GAME_STATE_LOSE:
            done = True
        else:
            done = False

        return done

    def _load_env_params(self, env_cfg_path):

        self.logger.info("the env_cfg_path={}".format(env_cfg_path))

        if os.path.exists(env_cfg_path):

            config = util.get_configure(env_cfg_path)

            self.__left = config['roiRegion']['region']['x']
            self.__top = config['roiRegion']['region']['y']
            self.__right = self.__left + config['roiRegion']['region']['w']
            self.__down = self.__top + config['roiRegion']['region']['h']

            # load reward rule
            self.__initScore = config['excitationFunction']['initScore']
            self.__maxScoreRepeatedTimes = config['excitationFunction']['maxScoreRepeatedTimes']
            self.__rewardOverRepeated = config['excitationFunction']['rewardOverRepeatedTimes']

            self.__winReward = config['excitationFunction']['winReward']
            self.__loseReward = config['excitationFunction']['loseReward']

            self.__maxRunningReward = config['excitationFunction']['maxRunningReward']
            self.__minRunningReward = config['excitationFunction']['minRunningReward']
            self.__rewardPerPos = config['excitationFunction']['rewardPerPostiveSection']
            self.__rewardPerNeg = config['excitationFunction']['rewardPerNegtiveSection']
            self.__scorePerSection = config['excitationFunction']['scorePerSection']

            self.__score_task_id = config['excitationFunction']['scoreTaskID']
            self.__win_task_id = config['excitationFunction']['winTaskID']
            self.__lose_task_id = config['excitationFunction']['loseTaskID']
            self.__start_task_id = config['excitationFunction']['startTaskID']
        else:
            self.logger.error('Rainbow env cfg not exist')

    def _CaculateReward(self, curScore):
        reward = 0

        if abs(curScore - self.__lastRewardScore) >= self.__scorePerSection:
            if curScore > self.__lastRewardScore:
                sections = int((curScore - self.__lastRewardScore) / self.__scorePerSection)
                reward = sections * self.__rewardPerPos
            else:
                sections = int((self.__lastRewardScore - curScore) / self.__scorePerSection)
                reward = sections * self.__rewardPerNeg

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

        if curScore > 140.0:
            reward = 0.5

        if curScore < 50.0:
            reward = -0.5

        return reward
