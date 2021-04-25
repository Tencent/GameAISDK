# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import csv
import logging
import operator
import os
import shutil
import numpy as np
import cv2
from .util import ObtainTaskDict, FindIndex, RepeatList


class GenerateImageSamples(object):
    """
    Generate samples class: generate image samples
    """

    def __init__(self, trainDataDir, testDataDir, trainClassDir, testClassDir, cfgData):
        self.logger = logging.getLogger('agent')
        self.trainDataDir = trainDataDir
        self.testDataDir = testDataDir

        self.trainClassDir = trainClassDir
        self.testClassDir = testClassDir

        self.inputHeight = cfgData['inputHeight']
        self.inputWidth = cfgData['inputWidth']

        self.roiRegion = cfgData.get('roiRegion')
        self.classImageTimes = cfgData['classImageTimes']

        self.imageSize = cfgData['imageSize']
        self.actionAheadNum = cfgData['actionAheadNum']
        self.actionDefine = cfgData.get('actionDefine')

        self.taskList, self.taskActionDict, self.actionNameDict = ObtainTaskDict(self.actionDefine)

        if os.path.exists(self.trainClassDir):
            shutil.rmtree(self.trainClassDir)
        if not os.path.exists(self.trainClassDir):
            os.mkdir(self.trainClassDir)

        if os.path.exists(self.testClassDir):
            shutil.rmtree(self.testClassDir)
        if not os.path.exists(self.testClassDir):
            os.mkdir(self.testClassDir)

    def LoadDataSave(self, sampleDir, mode='train'):
        """
        Load image samples
        """
        for item in os.listdir(sampleDir):
            filePath = os.path.join(sampleDir, item)
            if os.path.isdir(filePath):
                csvFileName = item + '_{}X{}_data.csv'.format(self.inputWidth, self.inputHeight)
                csvFilePath = os.path.join(filePath, csvFileName)
                self.LoadSampleSave(csvFilePath, mode)

    def LoadSampleSave(self, csvFilePath, mode):
        """
        Load label and image
        """
        logging.info(csvFilePath)

        imageNameList = list()
        actionList = list()
        outFileDir = ''

        with open(csvFilePath, 'r') as csvFd:
            csvReader = csv.reader(csvFd)

            for line in csvReader:
                if line[0] == 'name':
                    continue

                if mode == 'train':
                    index = [n for n in range(len(line[0])) if line[0][n] == '/']
                    if len(index) <= 2:
                        self.logger.error('Data path is wrong, should at least has two folders')
                        continue

                    fileName = line[0][index[-2] + 1:]
                    line[0] = os.path.join(self.trainDataDir, fileName)
                    outFileDir = self.trainClassDir

                if mode == 'test':
                    index = [n for n in range(len(line[0])) if line[0][n] == '/']
                    if len(index) <= 2:
                        self.logger.error('Data path is wrong, should at least has two folders')
                        continue

                    fileName = line[0][index[-2] + 1:]
                    line[0] = os.path.join(self.testDataDir, fileName)
                    outFileDir = self.testClassDir

                if not os.path.exists(outFileDir):
                    os.mkdir(outFileDir)

                if not os.path.isfile(line[0]):
                    continue

                actionTotalList = line[1::2]
                actionTotalList = [actionTotalList[n] for n in range(len(actionTotalList)) if
                                   actionTotalList[n] != '']
                actionTotalList = [int(actionTotalList[i]) for i in range(len(actionTotalList))]

                label = self.GetLabel(actionTotalList)

                if label is None:
                    continue

                actionList.append(label)
                imageNameList.append(line[0])

        imageNameListNew, actionListNew = self.SaveImageAhead(actionList, imageNameList, outFileDir)

        imageNameListAgu, actionListAug = self.DataClassSample(actionListNew, imageNameListNew)
        self.SaveTxt(outFileDir, imageNameListNew, actionListNew, name='dataOri.txt')
        self.SaveTxt(outFileDir, imageNameListAgu, actionListAug)

    def DataClassSample(self, label, feature):
        """
        Obtain samples for different classes:
        make sure the number of each class is higher than threshold
        """
        featureOut = list()
        labelOut = list()
        for taskIndex in self.taskList:
            featureTmp, labelTmp = self.ObtainTaskData(self.taskActionDict,
                                                       taskIndex,
                                                       self.classImageTimes,
                                                       label,
                                                       feature)
            featureOut = featureOut + featureTmp
            labelOut = labelOut + labelTmp
        return featureOut, labelOut

    def ObtainTaskData(self, taskActionDict, taskIndex, classImageTimes, label, feature):
        """
        Obtain samples for specific task.
        feature can be deep feature or image name
        """
        actionSpace = len(taskActionDict[taskIndex])
        numClassMinRatio = classImageTimes * 1.0 / actionSpace
        NumOneClass = np.round(len(label) * numClassMinRatio)
        labelTask = [labelTmp[taskIndex] for labelTmp in label]

        featureTmpDic = {}
        labelTmpDic = {}
        for n in range(actionSpace):
            indexAction = FindIndex(labelTask, n)
            self.logger.info('action number of action %s for taskIndex %s is %s',
                             str(n), str(taskIndex), str(indexAction))

            if len(indexAction) == 0:
                continue

            if isinstance(feature[0], str):
                featureSpecificClass = [feature[indexTmp] for indexTmp in indexAction]
            else:
                featureSpecificClass = feature[indexAction, :]

            repeatNum = NumOneClass * 1.0 / len(featureSpecificClass)
            if repeatNum < 1:
                repeatNum = 1
            else:
                repeatNum = int(repeatNum)

            if isinstance(feature[0], str):
                featureTmpDic[n] = RepeatList(featureSpecificClass, repeatNum)
            labelTmpDic[n] = [label[i] for i in indexAction] * repeatNum

            self.logger.info('New action number of action %s is %d', str(n), len(labelTmpDic[n]))

        feature, label = self.AppendData(actionSpace, featureTmpDic, labelTmpDic)

        return feature, label

    @staticmethod
    def AppendData(actionSpace, featureTmpDic, labelTmpDic):
        """
        combine feature and label from multi-task
        """
        feature = []
        label = []
        for n in range(actionSpace):
            if n not in featureTmpDic.keys():
                continue

            if len(feature) == 0:
                feature = featureTmpDic[n]
                label = labelTmpDic[n]
                continue

            if len(featureTmpDic[n]) == 0:
                continue

            feature = feature + featureTmpDic[n]
            label = label + labelTmpDic[n]
        return feature, label

    def SaveImageAhead(self, actionList, imageNameList, outFileDir):
        """
        Save image according to time of action delay
        """
        actionListNew = list()
        imageNameListNew = list()
        for n in range(len(actionList) - self.actionAheadNum):
            image = cv2.imread(imageNameList[n])
            label = actionList[n + self.actionAheadNum]

            if self.roiRegion is not None:
                image = image[self.roiRegion[1]: self.roiRegion[1] + self.roiRegion[3],
                              self.roiRegion[0]: self.roiRegion[0] + self.roiRegion[2], :]

            img = cv2.resize(image, (self.imageSize, self.imageSize))

            (prefileName1, tempfilename) = os.path.split(imageNameList[n])
            (_, prefileName2) = os.path.split(prefileName1)

            outFileDir2 = os.path.join(outFileDir, prefileName2)

            if not os.path.exists(outFileDir2):
                os.mkdir(outFileDir2)

            outImageName = os.path.join(outFileDir2, tempfilename[1:-4] + '.jpg')
            cv2.imwrite(outImageName, img)

            actionListNew.append(label)
            imageNameListNew.append(outImageName)

        return imageNameListNew, actionListNew

    @staticmethod
    def SaveTxt(outFileDir, imageNameList, actionList, name='data.txt'):
        """
        Save data to txt file
        """
        fw = open(os.path.join(outFileDir, name), 'a+')
        for n, imageName in enumerate(imageNameList):
            s = "{}".format(imageName)
            for i in range(len(actionList[n])):
                if i != len(actionList[n]) - 1:
                    s = s + " {}".format(actionList[n][i])
                else:
                    s = s + " {}\n".format(actionList[n][i])
            fw.write(s)
        fw.close()

    def GetLabel(self, actionTotalList):
        """
        Get label for multi-task
        """
        labelTot = list()
        for taskIndex in self.taskList:
            taskActionList = self.taskActionDict[taskIndex]
            actionName = self.actionNameDict[taskIndex]
            noneLabel = None
            for _, taskAction in enumerate(taskActionList):
                if taskAction["name"] == "None" or \
                   taskAction["name"] == "none":
                    noneLabel = actionName.index(taskAction["name"])

            label = noneLabel

            for _, taskAction in enumerate(taskActionList):
                if operator.eq(actionTotalList, taskAction["actionIDGroup"]):
                    label = actionName.index(taskAction["name"])
                    break
                elif set(taskAction["actionIDGroup"]) < set(actionTotalList):
                    label = actionName.index(taskAction["name"])

            labelTot.append(label)
        return labelTot
