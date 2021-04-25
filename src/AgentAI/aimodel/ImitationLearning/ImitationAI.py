# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time

import numpy as np
from aimodel.AIModel import AIModel

from .MainImitationLearning import MainImitationLearning


class ImitationAI(AIModel):
    """
    AI for imitation learning: output action based on input image
    """

    def __init__(self):
        AIModel.__init__(self)

        self.mainImitationLearning = MainImitationLearning()
        self.mainImitationLearning.Init()

        self.useLstm = self.mainImitationLearning.useLstm
        self.actionPerSecond = self.mainImitationLearning.actionPerSecond

        self.network = self.mainImitationLearning.netWork
        self.network.LoadWeights()

        self.agentEnv = None
        self.imgList = []
        self.featureConcat = []

        self.__timeCheckAI = -1
        self.__timeCheckAIWait = 1./self.actionPerSecond

    def Init(self, agentEnv):
        """
        Load params of AI and init agentEnv
        """
        self.agentEnv = agentEnv
        return True

    def Finish(self):
        """
        Finish AI
        """
        self.network.Finish()

    def OnEnterEpisode(self):
        """
        Enter Episode
        """
        self.logger.info('execute the enter episode in the imitation model')

    def OnLeaveEpisode(self):
        """
        Leave Episode
        """
        self.logger.info('execute the leave episode in the imitation model')

    def OnEpisodeStart(self):
        """
        Start Episode
        """
        self.imgList = []
        self.featureConcat = []
        self.agentEnv.OnEpisodeStart()

    def OnEpisodeOver(self):
        """
        Over Episode
        """
        self.agentEnv.OnEpisodeOver()
        self.agentEnv.Reset()
        self.imgList = []

    def TrainOneStep(self):
        """
        Train network
        """
        self.logger.info('execute the train one step in the imitation model')

    def OutputResults(self, action, netName):
        """
        Record action outputs
        """
        if len(self.mainImitationLearning.actionNameDict) == 2:
            self.logger.info('the action of %s is %s for task 0. %s is %s for task 1.',
                             netName, str(self.mainImitationLearning.actionNameDict[0][action[0]]),
                             netName, str(self.mainImitationLearning.actionNameDict[1][action[1]]))
        else:
            self.logger.info('the action of %s is %s',
                             netName, str(self.mainImitationLearning.actionNameDict[0][action]))

    def TestOneStep(self):
        """
        Test network
        """
        if time.time() - self.__timeCheckAI < self.__timeCheckAIWait:
            return

        self.__timeCheckAI = time.time()

        image, _ = self.agentEnv.GetState()

        if self.useLstm is False:
            action = self.network.Predict(image)
            self.logger.info("the predict action, action: %s", str(action))
            self.OutputResults(action, 'Net')
        else:

            timeStep = self.network.timeStep
            featureTmp = self.network.ExtractFeature(image)
            self.featureConcat.append(featureTmp)

            if len(self.featureConcat) < timeStep:
                return

            if len(self.featureConcat) > timeStep:
                self.featureConcat.pop(0)

            featureConcat = np.zeros([1, timeStep, featureTmp.shape[1]])
            for n in range(timeStep):
                featureConcat[0, n, :] = self.featureConcat[n]

            action = self.network.PredictLSTM(featureConcat)
            self.logger.info("the predict action with lstm, action: %s", str(action))
            self.OutputResults(action, 'NetLstm')

        self.agentEnv.DoAction(action)
