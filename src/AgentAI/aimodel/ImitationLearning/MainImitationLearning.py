# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging

from .CfgParse import CfgParse
from .GenerateImageSamples import GenerateImageSamples
from .Network import Network
from .util import ObtainTaskDict


class MainImitationLearning(object):
    """
    Main code for training AI of imitation learning
    """

    def __init__(self):
        self.logger = logging.getLogger('agent')
        self.cfgParse = CfgParse()
        self.cfgParse.Init()
        self.cfgData = self.cfgParse.GetParseResult()

        self.trainDataDir = self.cfgData['trainDataDir']
        self.testDataDir = self.cfgData['testDataDir']
        if self.trainDataDir[-1] != '/':
            self.trainDataDir = self.trainDataDir + '/'
        if self.testDataDir[-1] != '/':
            self.testDataDir = self.testDataDir + '/'

        self.trainClassDir = os.path.join(os.path.dirname(self.trainDataDir[:-2]), 'Class_train')
        self.testClassDir = os.path.join(os.path.dirname(self.testDataDir[:-2]), 'Class_valid')

        self.imageSize = self.cfgData['imageSize']
        self.actionAheadNum = self.cfgData['actionAheadNum']
        self.classImageTimes = self.cfgData['classImageTimes']

        self.actionDefine = self.cfgData.get('actionDefine')
        self.actionName = [self.actionDefine[n]["name"] for n in range(len(self.actionDefine))]
        self.taskList, self.taskActionDict, self.actionNameDict = ObtainTaskDict(self.actionDefine)

        self.inputHeight = self.cfgData['inputHeight']
        self.inputWidth = self.cfgData['inputWidth']
        self.useLstm = self.cfgData['useLstm']
        self.actionPerSecond = self.cfgData['actionPerSecond']
        self.actionTimeMs = self.cfgData['actionTimeMs']

        self.netWork = Network(self.trainDataDir, self.testDataDir,
                               self.trainClassDir, self.testClassDir, self.cfgData)

        self.logger.info('Cfg is all parsed.')

        self.generateImageSamples = None

    def Init(self):
        """
        Initial function
        """
        self.logger.info("execute the default init in the imitation learning")

    def GenerateImageSamples(self):
        """
        Generate image samples based on recorded data
        """
        self.generateImageSamples = GenerateImageSamples(self.trainDataDir,
                                                         self.testDataDir,
                                                         self.trainClassDir,
                                                         self.testClassDir,
                                                         self.cfgData)

        self.generateImageSamples.LoadDataSave(self.trainDataDir, 'train')
        # self.generateImageSamples.CopyFiles(self.trainClassDir)

        self.generateImageSamples.LoadDataSave(self.testDataDir, 'test')
        # self.generateImageSamples.CopyFiles(self.testClassDir)

    def TrainNetwork(self):
        """
        Train network and Lstm
        """

        self.logger.info('Train Network')
        self.netWork.TrainGenerator()

        # # train NetworkLSTM
        self.logger.info('Train NetworkLSTM')
        self.netWork.TrainLSTM()


if __name__ == '__main__':
    mainImitationLearning = MainImitationLearning()
    mainImitationLearning.Init()
    mainImitationLearning.GenerateImageSamples()
    mainImitationLearning.TrainNetwork()
