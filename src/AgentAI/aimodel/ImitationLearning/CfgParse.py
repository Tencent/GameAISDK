# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import json
import os
import numpy as np

DATA_ROOT_DIR = '../'
if os.environ.get('AI_SDK_PATH') is not None:
    DATA_ROOT_DIR = os.environ.get('AI_SDK_PATH') + '/'

IMITATION_CFG_FILE = os.path.join(DATA_ROOT_DIR, 'cfg/task/agent/ImitationLearning.json')

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
        self.actionsContextList = dict()
        self.__idleActionId = -1
        self.data = dict()
        self.__ratio = 1

    def Init(self):
        """
        Load parameters for imitation learning
        """
        self._LoadAIParams()
        self._LoadCfg()

    def _LoadAIParams(self):
        """
        Load AI parameters for training and test
        """
        self.data['imageSize'] = 224
        self.data['actionAheadNum'] = 1
        self.data['classImageTimes'] = 2

        if os.path.exists(IMITATION_CFG_FILE):
            with open(IMITATION_CFG_FILE, 'rb') as file:
                jsonStr = file.read()
                aiCfg = json.loads(str(jsonStr, encoding='utf-8'))
                # File path of training images
                self.data['trainDataDir'] = os.path.join(DATA_ROOT_DIR, aiCfg.get('trainDataDir'))
                # File path of test images
                self.data['testDataDir'] = os.path.join(DATA_ROOT_DIR, aiCfg.get('testDataDir'))
                # Whether use small network
                self.data['isSmallNet'] = aiCfg.get('isSmallNet')
                # Whether choose action with max score during test period
                self.data['isMax'] = aiCfg.get('isMax')
                # Random ratio for choosing action if "isMax" is set as 0
                self.data['randomRatio'] = aiCfg.get('randomRatio')
                # Frame number of ahead action considering action delay
                self.data['actionAheadNum'] = aiCfg.get('actionAheadNum')
                # Times for each class
                self.data['classImageTimes'] = aiCfg.get('classImageTimes')
                # Input height of image
                self.data['inputHeight'] = aiCfg.get('inputHeight')
                # Input width of image
                self.data['inputWidth'] = aiCfg.get('inputWidth')
                # Input region for network
                self.data['roiRegion'] = aiCfg.get('roiRegion')
                # whether use lstm
                self.data['useLstm'] = aiCfg.get('useLstm')
                # action number for one second
                self.data['actionPerSecond'] = aiCfg.get('actionPerSecond')
                # action click time
                self.data['actionTimeMs'] = aiCfg.get('actionTimeMs')
                # train Iter
                self.data['trainIter'] = aiCfg.get('trainIter')
                # timeStep is the frame length for LSTM (memory)
                self.data['timeStep'] = aiCfg.get('timeStep')
                # Action define
                self.data['actionDefine'] = aiCfg.get('actionDefine')

                # Whether use class balance
                self.data['useClassBalance'] = aiCfg.get('useClassBalance')
                if self.data['useClassBalance'] is None:
                    self.data['useClassBalance'] = True

                # Whether use resNet
                self.data['useResNet'] = aiCfg.get('useResNet')
                if self.data['useResNet'] is None:
                    self.data['useResNet'] = True

                # Set default task id for action define
                for n in range(len(self.data['actionDefine'])):
                    if "task" not in self.data['actionDefine'][n].keys():
                        self.data['actionDefine'][n]["task"] = [0]

                if self.data['isSmallNet']:
                    self.data['imageSize'] = 50
                else:
                    self.data['imageSize'] = 150

                logging.info('The AI cfg is parsed.')
                return

        else:
            logging.error('The AI cfg {} is not existed.'.format(IMITATION_CFG_FILE))

        return

    def _LoadCfg(self):

        self.__actionCfgFile = os.path.join(DATA_ROOT_DIR,
                                            'cfg/task/agent/ImitationAction.json')

        self._LoadActionCfg(self.__actionCfgFile)

    def _GetRatio(self, data):
        self.__screenActionHeight = data['screenHeight']
        self.__screenActionWidth = data['screenWidth']
        self.__ratio = self.data['inputHeight'] / self.__screenActionHeight

    def _LoadActionCfg(self, actionCfgFile):
        with open(actionCfgFile) as fileData:
            data = json.load(fileData)
            self._GetRatio(data)
            for actionContext in data['actions']:
                actionType = actionContext.get('type')
                actionId = actionContext.get('id')

                if actionType == ACTION_TYPE_NONE:
                    self.__idleActionId = actionId
                    regionX1 = 0
                    regionY1 = 0
                    regionX2 = 0
                    regionY2 = 0

                elif actionType == ACTION_TYPE_PRESS_UP:
                    actionContext['point'] = None
                    regionX1 = actionContext.get('startRectx')
                    regionY1 = actionContext.get('startRecty')
                    regionX2 = actionContext.get('startRectx') + actionContext.get('width')
                    regionY2 = actionContext.get('startRecty') + actionContext.get('height')
                elif actionType == ACTION_TYPE_SWIPE_ONCE:
                    actionContext['point'] = None
                    regionX1, regionY1, regionX2, regionY2 = self._GetRegionSwipe(actionContext)
                    sx = actionContext.get('startX')
                    sy = actionContext.get('startY')
                    ex = actionContext.get('endX')
                    ey = actionContext.get('endY')
                    actionContext['dirVect'] = np.array([ex - sx, ey - sy]) * self.__ratio
                elif actionType == ACTION_TYPE_JOY_STICK:
                    actionContext['centerx'] = int(actionContext['centerx'] * self.__ratio)
                    actionContext['centery'] = int(actionContext['centery'] * self.__ratio)
                    actionContext['rangeInner'] = int(actionContext['rangeInner'] * self.__ratio)
                    actionContext['rangeOuter'] = int(actionContext['rangeOuter'] * self.__ratio)
                    self._GetContextJoystick(actionContext, actionId)
                    continue
                else:
                    regionX1 = actionContext.get('startRectx')
                    regionY1 = actionContext.get('startRecty')
                    regionX2 = actionContext.get('startRectx') + actionContext.get('width')
                    regionY2 = actionContext.get('startRecty') + actionContext.get('height')

                actionContext['regionX1'] = int(regionX1 * self.__ratio)
                actionContext['regionY1'] = int(regionY1 * self.__ratio)
                actionContext['regionX2'] = int(regionX2 * self.__ratio)
                actionContext['regionY2'] = int(regionY2 * self.__ratio)

                if 'startX' in actionContext.keys():
                    actionContext['swipeStartX'] = int(actionContext['startX'] * self.__ratio)
                    actionContext['swipeStartY'] = int(actionContext['startY'] * self.__ratio)
                    actionContext['swipeEndX'] = int(actionContext['endX'] * self.__ratio)
                    actionContext['swipeEndY'] = int(actionContext['endY'] * self.__ratio)

                self.actionsContextList[actionId] = actionContext

                self.data['actionsContextList'] = self.actionsContextList

    def _GetRegionSwipe(self, actionContext):
        regionX1 = min(actionContext.get('startRectx'), actionContext.get('endRectx'))
        regionY1 = min(actionContext.get('startRecty'), actionContext.get('endRecty'))
        regionX2 = max(actionContext.get('startRectx')
                       + actionContext.get('startRectWidth'),
                       actionContext.get('endRectx')
                       + actionContext.get('endRectWidth'))
        regionY2 = max(actionContext.get('startRecty')
                       + actionContext.get('startRectHeight'),
                       actionContext.get('endRecty')
                       + actionContext.get('endRectHeight'))
        return regionX1, regionY1, regionX2, regionY2

    def _GetContextJoystick(self, actionContext, actionId):
        num = actionContext.get('QuantizedNumber')
        name = actionContext.get('name')
        contact = actionContext.get('contact')
        for i in range(num):
            context = dict()
            context['name'] = '{}_{}'.format(name, i)
            context['type'] = ACTION_TYPE_JOY_STICK
            context['centerx'] = actionContext['centerx']
            context['centery'] = actionContext['centery']
            context['rangeInner'] = actionContext['rangeInner']
            context['rangeOuter'] = actionContext['rangeOuter']
            context['contact'] = contact
            context['angle'] = int(i * 1. / num * 360)
            self.actionsContextList[actionId + i] = context
        return

    def GetParseResult(self):
        """
        Get parameters for imitation learning
        """
        return self.data


if __name__ == '__main__':
    cfgParse = CfgParse()
    cfgParse.Init()
    print(cfgParse.actionsContextList)
