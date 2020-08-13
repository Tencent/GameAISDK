# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
import time
import logging
import configparser
from collections import deque

import numpy as np
import cv2

from aimodel.AIModel import AIModel
from agentenv.GameEnv import GameEnv
from util import util
from .BrainDQN import BrainDQN

LEARN_CFG_FILE = 'cfg/task/agent/DQNLearn.ini'

class DQNAIModel(AIModel):
    """
    DQN AIModel implement, train AI model and predict action
    """

    def __init__(self):
        AIModel.__init__(self)

    def Init(self, agentEnv):
        """
        Init DQN AIModel after object created
        """
        self.agentEnv = agentEnv
        self.actionSpace = self.agentEnv.GetActionSpace()

        result, learnArgs = self._LoadDQNPrams()
        if not result:
            return False

        self.trainFPS = learnArgs['train_frame_rate']
        self.trainStep = 0
        self.firstRunning = 0
        self.timePerFrame = 1.0/self.trainFPS
        self.testAgent = False

        self._ProcArgs(learnArgs)
        self.logger.info('learnArgs : {0}'.format(learnArgs))
        self.brain = BrainDQN(learnArgs)

        return True

    def Finish(self):
        """
        Exit DQN AIModel after object used
        """
        pass

    def _LoadDQNPrams(self):
        learnArgs = {}

        learnCfgFile = util.ConvertToSDKFilePath(LEARN_CFG_FILE)
        if not os.path.exists(learnCfgFile):
            self.logger.error('DQN param file {} not exist.'.format(learnCfgFile))
            return False, learnArgs

        try:
            config = configparser.ConfigParser()
            config.read(learnCfgFile)

            learnArgs['dueling_network'] = config.getboolean('DQN', 'DuelingNetwork', fallback=True)
            learnArgs['input_img_width'] = config.getint('DQN', 'InputImgWidth')
            learnArgs['input_img_height'] = config.getint('DQN', 'InputImgHeight')
            learnArgs['state_recent_frame'] = config.getint('DQN', 'StateRecentFrame')
            learnArgs['terminal_delay_frame'] = config.getint('DQN', 'TerminalDelayFrame')
            learnArgs['reward_discount'] = config.getfloat('DQN', 'RewardDiscount')
            learnArgs['learn_rate'] = config.getfloat('DQN', 'LearnRate')
            learnArgs['frame_per_action'] = config.getint('DQN', 'FramePerAction')
            learnArgs['observe_frame'] = config.getint('DQN', 'ObserveFrame')
            learnArgs['explore_frame'] = config.getint('DQN', 'ExploreFrame')
            learnArgs['initial_epsilon'] = config.getfloat('DQN', 'InitialEpsilon')
            learnArgs['final_epsilon'] = config.getfloat('DQN', 'FinalEpsilon')
            learnArgs['qnet_update_step'] = config.getint('DQN', 'QNetworkUpdateStep')
            learnArgs['memory_size'] = config.getint('DQN', 'MemorySize')
            learnArgs['show_img_state'] = config.getboolean('DQN', 'ShowImgState')
            learnArgs['mini_batch_size'] = config.getint('DQN', 'MiniBatchSize')
            learnArgs['train_with_double_q'] = config.getboolean('DQN', 'TrainWithDoubleQ')
            learnArgs['gpu_memory_fraction'] = config.getfloat('DQN', 'GPUMemoryFraction')
            learnArgs['gpu_memory_growth'] = config.getboolean('DQN', 'GPUMemoryGrowth')
            learnArgs['checkpoint_path'] = config.get('DQN', 'CheckPointPath')
            learnArgs['train_frame_rate'] = config.getint('DQN', 'TrainFrameRate')
            learnArgs['run_type'] = config.getint('DQN', 'RunType', fallback=1)
        except Exception as e:
            self.logger.error('Load file {} failed, error: {}.'.format(learnCfgFile, e))
            return False, learnArgs

        return True, learnArgs

    def _ProcArgs(self, learnArgs):
        learnArgs['action_space'] = self.actionSpace
        learnArgs['checkpoint_path'] = util.ConvertToSDKFilePath(learnArgs['checkpoint_path'])

        runType = learnArgs['run_type']
        if runType == 0:
            self.testAgent = False
        elif runType == 1:
            self.testAgent = True
            learnArgs['memory_size'] = 200
            learnArgs['initial_epsilon'] = 0.001
        else:
            pass

    def _FrameStep(self, action):
        if self.agentEnv.IsTrainable() is True:
            self.agentEnv.DoAction(action)

        #train the q-network
        begin = time.time()
        if self.testAgent != True:
            self.brain.Learn()
        self.trainStep += 1
        if self.trainStep % self.trainFPS == 0:
            end = time.time()
            self.logger.debug('train time: {0} ms'.format((end - begin) * 1000))

        timeNow = time.time()
        timePassed = timeNow - self.lastFrameTime
        if timePassed < self.timePerFrame:
            timeDelay = self.timePerFrame - timePassed
            time.sleep(timeDelay)
        else:
            overdTime = timePassed - self.timePerFrame
            if overdTime > self.timePerFrame/5.0:
                self.logger.warning('frame overtime: {0} ms'.format(overdTime * 1000))

        begin = time.time()
        img, reward, terminal = self.agentEnv.GetState()
        if self.trainStep % self.trainFPS == 0:
            end = time.time()
            self.logger.debug('GetState time: {0} ms'.format((end - begin) * 1000))

        self.lastFrameTime = time.time()

        return img, reward, terminal

    def _RunOneStep(self):
        if self.firstRunning == 0:
            action = np.zeros(self.actionSpace, np.uint8)
            action[0] = 1
        else:
            action = self.brain.GetAction()  #get action from dqn

        nextObservation, reward, terminal = self._FrameStep(action)

        if terminal is True:
            if self.agentEnv.IsTrainable() is True:
                self.brain.SetPerception(nextObservation, action, reward, True)
        else:
            if self.agentEnv.IsTrainable() is True:
                if self.firstRunning == 0:
                    self.brain.InitState(nextObservation)
                    self.firstRunning = 1
                else:
                    self.brain.SetPerception(nextObservation, action, reward, False)

    def OnEpisodeStart(self):
        """
        Abstract interface implement, reset time of get frame when episode start
        """
        self.lastFrameTime = time.time()

    def OnEpisodeOver(self):
        """
        Abstract interface implement, reset agent envwhen episode over
        """
        self.agentEnv.Reset()

    def OnEnterEpisode(self):
        """
        Abstract interface implement, do nothing
        """
        pass

    def OnLeaveEpisode(self):
        """
        Abstract interface implement, do nothing
        """
        pass

    def TrainOneStep(self):
        """
        Abstract interface implement, run one step (usually means get a image frame)
        when trian DQN AI model
        """
        self._RunOneStep()

    def TestOneStep(self):
        """
        Abstract interface implement, run one step (usually means get a image frame)
        when run AI test
        """
        self._RunOneStep()
