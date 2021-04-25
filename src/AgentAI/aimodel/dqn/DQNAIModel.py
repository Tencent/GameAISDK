# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import os
import time

import numpy as np
from aimodel.AIModel import AIModel
from util import util

from .BrainDQN import BrainDQN

LEARN_CFG_FILE = 'cfg/task/agent/DQNLearning.json'

class DQNAIModel(AIModel):
    """
    DQN AIModel implement, train AI model and predict action
    """

    def __init__(self):
        AIModel.__init__(self)
        self.testAgent = False
        self.actionSpace = None
        self.trainFPS = None
        self.trainStep = 0
        self.firstRunning = 0
        self.timePerFrame = None
        self.testAgent = False
        self.brain = None
        self.testAgent = False
        self.lastFrameTime = None


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

            config = self._GetConfigure(learnCfgFile)
            learnArgs['dueling_network'] = config['network']['duelingNetwork']
            learnArgs['input_img_width'] = config['network']['inputImgWidth']
            learnArgs['input_img_height'] = config['network']['inputImgHeight']
            learnArgs['state_recent_frame'] = config['network']['stateRecentFrame']
            learnArgs['terminal_delay_frame'] = config['network']['terminalDelayFrame']
            learnArgs['reward_discount'] = config['network']['rewardDiscount']
            learnArgs['learn_rate'] = config['network']['learnRate']
            learnArgs['frame_per_action'] = config['network']['framePerAction']
            learnArgs['observe_frame'] = config['network']['observeFrame']
            learnArgs['explore_frame'] = config['network']['exploreFrame']
            learnArgs['initial_epsilon'] = config['network']['initialEpsilon']
            learnArgs['final_epsilon'] = config['network']['finalEpsilon']
            learnArgs['qnet_update_step'] = config['network']['qNetworkUpdateStep']
            learnArgs['memory_size'] = config['network']['memorySize']
            learnArgs['show_img_state'] = config['network']['showImgState']
            learnArgs['mini_batch_size'] = config['network']['miniBatchSize']
            learnArgs['train_with_double_q'] = config['network']['trainWithDoubleQ']
            learnArgs['gpu_memory_fraction'] = config['network']['gpuMemoryFraction']
            learnArgs['gpu_memory_growth'] = config['network']['gpuMemoryGrowth']
            learnArgs['checkpoint_path'] = config['network']['checkPointPath']
            learnArgs['train_frame_rate'] = config['network']['trainFrameRate']
            learnArgs['run_type'] = config['network']['runType']

            self.logger.info("the learnArgs is {0}".format(learnArgs))

            # config = configparser.ConfigParser()
            # config.read(learnCfgFile)
            #
            # learnArgs['dueling_network'] = config.getboolean('DQN', 'DuelingNetwork', fallback=True)
            # learnArgs['input_img_width'] = config.getint('DQN', 'InputImgWidth')
            # learnArgs['input_img_height'] = config.getint('DQN', 'InputImgHeight')
            # learnArgs['state_recent_frame'] = config.getint('DQN', 'StateRecentFrame')
            # learnArgs['terminal_delay_frame'] = config.getint('DQN', 'TerminalDelayFrame')
            # learnArgs['reward_discount'] = config.getfloat('DQN', 'RewardDiscount')
            # learnArgs['learn_rate'] = config.getfloat('DQN', 'LearnRate')
            # learnArgs['frame_per_action'] = config.getint('DQN', 'FramePerAction')
            # learnArgs['observe_frame'] = config.getint('DQN', 'ObserveFrame')
            # learnArgs['explore_frame'] = config.getint('DQN', 'ExploreFrame')
            # learnArgs['initial_epsilon'] = config.getfloat('DQN', 'InitialEpsilon')
            # learnArgs['final_epsilon'] = config.getfloat('DQN', 'FinalEpsilon')
            # learnArgs['qnet_update_step'] = config.getint('DQN', 'QNetworkUpdateStep')
            # learnArgs['memory_size'] = config.getint('DQN', 'MemorySize')
            # learnArgs['show_img_state'] = config.getboolean('DQN', 'ShowImgState')
            # learnArgs['mini_batch_size'] = config.getint('DQN', 'MiniBatchSize')
            # learnArgs['train_with_double_q'] = config.getboolean('DQN', 'TrainWithDoubleQ')
            # learnArgs['gpu_memory_fraction'] = config.getfloat('DQN', 'GPUMemoryFraction')
            # learnArgs['gpu_memory_growth'] = config.getboolean('DQN', 'GPUMemoryGrowth')
            # learnArgs['checkpoint_path'] = config.get('DQN', 'CheckPointPath')
            # learnArgs['train_frame_rate'] = config.getint('DQN', 'TrainFrameRate')
            # learnArgs['run_type'] = config.getint('DQN', 'RunType', fallback=1)
        except Exception as e:
            self.logger.error('Load file {} failed, error: {}.'.format(learnCfgFile, e))
            return False, learnArgs

        return True, learnArgs

    def _GetConfigure(self, learnCfgFile: str):
        try:
            with open(learnCfgFile, 'r', encoding='utf-8') as file:
                jsonStr = file.read()
                dqn_configure = json.loads(jsonStr)
                return dqn_configure
        except Exception as err:
            self.logger.error('Load game state file {} error! Error msg: {}'.format(learnCfgFile, err))
            return None

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
        if not self.testAgent:
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
                self.logger.info("set Perception when terminate condition, action:{}, reward:{}".format(action, reward))
                self.brain.SetPerception(nextObservation, action, reward, True)
        else:
            if self.agentEnv.IsTrainable() is True:
                if self.firstRunning == 0:
                    self.logger.info("set Perception when fist running, action:{}, reward:{}".format(action, reward))
                    self.brain.InitState(nextObservation)
                    self.firstRunning = 1
                else:
                    self.logger.info("set Perception when normal condition, action:{}, reward:{}"
                                     .format(action, reward))
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
