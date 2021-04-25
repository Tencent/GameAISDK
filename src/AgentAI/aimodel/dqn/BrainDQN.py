# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import random
import numpy as np

from .QNetwork import QNetwork

class BrainDQN(object):
    """
    Deep Q-network class: trainning DQN, predict action from DQN
    """

    def __init__(self, args):
        self.stateImgWidth = args['input_img_width']
        self.stateImgHeight = args['input_img_height']
        self.stateRecentFrame = args['state_recent_frame']
        self.actionSpace = args['action_space']
        self.statePerAction = args['frame_per_action']
        self.observeState = args['observe_frame']
        self.exploreState = args['explore_frame']
        self.initialEpsilon = args['initial_epsilon']
        self.finalEpsilon = args['final_epsilon']

        self.logger = logging.getLogger('agent')
        self.epsilon = self.initialEpsilon
        self.stateStep = 0
        self.qNetWork = QNetwork(args)

        self.currentState = None

        self.logger.debug("the observeState is {}".format( self.observeState))

    def Learn(self):
        """
        QNetwork learning, trian DQN network
        """
        if self.stateStep > self.observeState:
            self.logger.debug("begin to train the model, stateStep:{}, observeState:{}".format(self.stateStep
                              , self.observeState))
            self.qNetWork.Train()

    def GetAction(self, extraEpsilon=0.):
        """
        Predict action from DQN
        """
        action = np.zeros(self.actionSpace, np.uint8)
        actionIndex = 0

        if self.stateStep % self.statePerAction == 0:
            if random.random() <= self.epsilon + extraEpsilon:
                actionIndex = random.randrange(self.actionSpace)
                action[actionIndex] = 1
            else:
                qValue = self.qNetWork.EvalQValue(self.currentState)
                actionIndex = np.argmax(qValue)
                action[actionIndex] = 1
        else:
            action[0] = 1 # do nothing

        return action

    def SetPerception(self, nextState, action, reward, terminal):
        """
        Add (s, a, r, t) to replay memory
        """
        self.qNetWork.StoreTransition(action, reward, nextState, terminal)

        nextState = np.reshape(nextState, (self.stateImgHeight, self.stateImgWidth, 1))
        self.currentState = np.append(self.currentState[:, :, 1:], nextState, axis=2)

        self.stateStep += 1
        self.logger.debug("get the step of state, stateStep:{}".format(self.stateStep))
        # change episilon
        if self.epsilon > self.finalEpsilon and self.stateStep > self.observeState:
            self.epsilon -= (self.initialEpsilon - self.finalEpsilon)/self.exploreState

        self._LogTrainingInfo()


    def InitState(self, state):
        """
        Create the initial state use the first game image state
        """
        recetStates = [state for _ in range(0, self.stateRecentFrame)]
        self.currentState = np.stack(recetStates, axis=2)


    def _LogTrainingInfo(self):
        state = ""
        step = self.stateStep
        if step <= self.observeState:
            state = "observe"
        elif step > self.observeState and step <= self.observeState + self.exploreState:
            state = "explore"
        else:
            state = "train"

        if step % 20 == 0:
            self.logger.debug('STEP: {}, STATE: {}, EPSILON: {}'.format(step, state, self.epsilon))
