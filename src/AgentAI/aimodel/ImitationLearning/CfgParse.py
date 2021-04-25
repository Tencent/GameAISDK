# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import json
import os
import traceback
import cv2
import numpy as np

from util import util

ACTION_CFG_FILE = 'cfg/task/agent/ImitationAction.json'
IMITATION_CFG_FILE = 'cfg/task/agent/ImitationLearning.json'

ACTION_TYPE_NONE = 0
ACTION_TYPE_PRESS_DOWN = 1
ACTION_TYPE_PRESS_UP = 2
ACTION_TYPE_CLICK = 3
ACTION_TYPE_SWIPE_ONCE = 4
ACTION_TYPE_JOY_STICK = 5

np.seterr(divide='ignore', invalid='ignore')

class CfgParse(object):
    """
    Cfg parse class: load configures for imitation learning
    """

    def __init__(self):
        self.actionsContextDict = dict()
        self.data = dict()
        self.__logger = logging.getLogger('agent')
        self.__screenActionHeight = None
        self.__screenActionWidth = None
        self.__ratio = None

    def Init(self):
        """
        Load parameters for imitation learning
        """
        self._LoadAIParams()    # 加载AI参数信息
        self._LoadActionCfg()   # 加载action信息

    def _LoadAIParams(self):
        """
        Load AI parameters for training and test
        """
        self.data['imageSize'] = 224
        self.data['actionAheadNum'] = 1
        self.data['classImageTimes'] = 2

        imitationCfgFile = util.ConvertToSDKFilePath(IMITATION_CFG_FILE)
        if not os.path.exists(imitationCfgFile):
            self.__logger.error('Imitation cfg {} is not existed.'.format(imitationCfgFile))
            return False

        try:
            with open(imitationCfgFile, 'r', encoding='utf-8') as file:
                jsonStr = file.read()
                aiCfg = json.loads(jsonStr)

                networkCfg = aiCfg.get('network')
                if networkCfg is None:
                    self.__logger.error('No network params in imitation cfg!')
                    return False

                # training data params
                self.data['trainDataDir'] = util.ConvertToSDKFilePath(networkCfg.get('dataDir'))
                self.data['testDataDir'] = util.ConvertToSDKFilePath(networkCfg.get('dataDir'))
                self.data['validDataRatio'] = networkCfg.get('validDataRatio')
                # Whether use small network
                self.data['isSmallNet'] = networkCfg.get('isSmallNet')
                # Whether choose action with max score during test period
                self.data['isMax'] = networkCfg.get('isMax')
                # Random ratio for choosing action if "isMax" is set as 0
                self.data['randomRatio'] = networkCfg.get('randomRatio')
                # Frame number of ahead action considering action delay
                self.data['actionAheadNum'] = networkCfg.get('actionAheadNum')
                # Times for each class
                self.data['classImageTimes'] = networkCfg.get('classImageTimes')
                # Input height of image
                self.data['inputHeight'] = networkCfg.get('inputHeight')
                # Input width of image
                self.data['inputWidth'] = networkCfg.get('inputWidth')
                # whether use lstm
                self.data['useLstm'] = networkCfg.get('useLstm')
                # train Iter
                self.data['trainIter'] = networkCfg.get('trainIter')
                # timeStep is the frame length for LSTM (memory)
                self.data['timeStep'] = networkCfg.get('timeStep')
                # Whether use class balance
                self.data['useClassBalance'] = networkCfg.get('useClassBalance', True)
                # Whether use resNet
                self.data['useResNet'] = networkCfg.get('useResNet', True)

                actionCfg = aiCfg.get('action')
                if actionCfg is None:
                    self.__logger.error('No action params in imitation cfg!')
                    return False

                # action number for one second
                self.data['actionPerSecond'] = actionCfg.get('actionPerSecond')
                # action click time
                self.data['actionTimeMs'] = actionCfg.get('actionTimeMs')

                roiRegionCfg = aiCfg.get('roiRegion')
                if roiRegionCfg is None:
                    self.__logger.error('No roiRegion params in imitation cfg!')
                    return False

                # Input region for network
                imgShape = self._GetImageShape(roiRegionCfg['path'])
                if imgShape is None:
                    self.__logger.error('Get image(%s) shape error!' % roiRegionCfg['path'])
                    return False

                heightRatio = self.data['inputHeight']/imgShape[0]
                widthRatio = self.data['inputWidth']/imgShape[1]
                x = int(roiRegionCfg['region']['x'] * widthRatio)
                y = int(roiRegionCfg['region']['y'] * heightRatio)
                w = int(roiRegionCfg['region']['w'] * widthRatio)
                h = int(roiRegionCfg['region']['h'] * heightRatio)
                self.data['roiRegion'] = [x, y, w, h]

                if self.data['isSmallNet']:
                    self.data['imageSize'] = 50
                else:
                    self.data['imageSize'] = 150

                self.__logger.info('The imitation cfg is parsed.')
        except Exception as err:
            traceback.print_exc()
            self.__logger.error('Load imitation cfg {} error! Error msg: {}'.format(imitationCfgFile, err))
            return False

        return True

    def _GetRatio(self, data):
        self.__screenActionHeight = data['screenHeight']
        self.__screenActionWidth = data['screenWidth']
        self.__ratio = self.data['inputHeight'] / self.__screenActionHeight

    def _LoadActionCfg(self):
        actionCfgFile = util.ConvertToSDKFilePath(ACTION_CFG_FILE)
        if not os.path.exists(actionCfgFile):
            self.__logger.error('Action cfg {} not existed.'.format(actionCfgFile))
            return False

        try:
            # 加载action文件信息,
            with open(actionCfgFile, 'r', encoding='utf-8') as file:
                jsonStr = file.read()
                actionCfg = json.loads(jsonStr)

                # read action define
                # Set default task id for action define
                self.data['actionDefine'] = actionCfg['aiAction']
                for n in range(len(self.data['actionDefine'])):
                    if "task" not in self.data['actionDefine'][n].keys():
                        self.data['actionDefine'][n]["task"] = [0]

                # 获取gameAction
                for actionContext in actionCfg['gameAction']:
                    actionType = actionContext.get('type')
                    actionId = actionContext.get('id')

                    if actionType != 'none':
                        imageShape = self._GetImageShape(actionContext['actionRegion']['path'])
                        imageHeight = imageShape[0]
                        self.__ratio = self.data['inputHeight']/imageHeight

                    if actionType == 'none':
                        pass
                    elif actionType == 'down' or actionType == 'up' or actionType == 'click':
                        region = actionContext['actionRegion']['region']
                        buttonX = region['x'] + region['w']/2
                        buttonY = region['y'] + region['h']/2
                        actionContext['buttonX'] = int(buttonX * self.__ratio)
                        actionContext['buttonY'] = int(buttonY * self.__ratio)
                        actionContext['updateBtn'] = False
                        actionContext['updateBtnX'] = -1
                        actionContext['updateBtnY'] = -1
                    elif actionType == 'key':
                        region = actionContext['actionRegion']['region']
                        buttonX = region['x'] + region['w'] / 2
                        buttonY = region['y'] + region['h'] / 2
                        actionContext['buttonX'] = int(buttonX * self.__ratio)
                        actionContext['buttonY'] = int(buttonY * self.__ratio)
                        actionContext['updateBtn'] = False
                        actionContext['updateBtnX'] = -1
                        actionContext['updateBtnY'] = -1
                        actionContext['alphabet'] = actionContext['actionRegion']['alphabet']
                        actionContext['action_type'] = actionContext['actionRegion']['actionType']
                        actionContext['action_text'] = actionContext['actionRegion']['text']
                    elif actionType == 'swipe':
                        #regionX1, regionY1, regionX2, regionY2 = self._GetRegionSwipe(actionContext)
                        startPoint = actionContext['actionRegion']['startPoint']
                        endPoint = actionContext['actionRegion']['endPoint']
                        actionContext['swipeStartX'] = int(startPoint['x'] * self.__ratio)
                        actionContext['swipeStartY'] = int(startPoint['y'] * self.__ratio)
                        actionContext['swipeEndX'] = int(endPoint['x'] * self.__ratio)
                        actionContext['swipeEndY'] = int(endPoint['y'] * self.__ratio)
                    elif actionType == 'joystick':
                        center = actionContext['actionRegion']['center']
                        inner = actionContext['actionRegion']['inner']
                        outer = actionContext['actionRegion']['outer']
                        actionContext['centerx'] = int(center['x'] * self.__ratio)
                        actionContext['centery'] = int(center['y'] * self.__ratio)
                        actionContext['rangeInner'] = int((inner['w'] + inner['h']) * 0.25 * self.__ratio)
                        actionContext['rangeOuter'] = int((outer['w'] + outer['h']) * 0.25 * self.__ratio)
                        self._GetContextJoystick(actionContext, actionId)
                        continue
                    else:
                        self.__logger.error('Error action type')

                    self.actionsContextDict[actionId] = actionContext
                self.__logger.info("the actionsContextDict is {}".format(self.actionsContextDict))
                self.data['actionsContextDict'] = self.actionsContextDict
        except Exception as err:
            self.__logger.error('Load action cfg {} error! Error msg: {}'.format(actionCfgFile, err))
            return False

        return True

    def _GetRegionSwipe(self, actionContext):
        regionX1 = min(actionContext.get('startRectx'), actionContext.get('endRectx'))
        regionY1 = min(actionContext.get('startRecty'), actionContext.get('endRecty'))
        regionX2 = max(actionContext.get('startRectx') + actionContext.get('startRectWidth'),
                       actionContext.get('endRectx') + actionContext.get('endRectWidth'))
        regionY2 = max(actionContext.get('startRecty') + actionContext.get('startRectHeight'),
                       actionContext.get('endRecty') + actionContext.get('endRectHeight'))
        return regionX1, regionY1, regionX2, regionY2

    def _GetContextJoystick(self, actionContext, actionId):
        num = actionContext['actionRegion']['quantizeNumber']
        name = actionContext['name']
        contact = actionContext['contact']
        for i in range(num):
            context = dict()
            context['name'] = '{}_{}'.format(name, i)
            context['type'] = 'joystick'
            context['centerx'] = actionContext['centerx']
            context['centery'] = actionContext['centery']
            context['rangeInner'] = actionContext['rangeInner']
            context['rangeOuter'] = actionContext['rangeOuter']
            context['contact'] = contact
            context['angle'] = int(i * 1. / num * 360)
            self.actionsContextDict[actionId + i] = context
        return

    def _GetImageShape(self, imgFile):
        if not imgFile:
            return None
        image_path = util.ConvertToSDKFilePath(imgFile)
        if not os.path.exists(image_path):
            return None

        img = cv2.imread(image_path)
        if img is None:
            self.__logger.error('failed to read image(%s)' % image_path)
            return None
        return img.shape

    def GetParseResult(self):
        """
        Get parameters for imitation learning
        """
        return self.data


if __name__ == '__main__':
    cfgParse = CfgParse()
    cfgParse.Init()
    print(cfgParse.actionsContextDict)
