# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time

from ActionAPI.ActionAPIMgr import ActionAPIMgr
from aimodel.ImitationLearning.MainImitationLearning import MainImitationLearning


class ImitationAction(object):
    """
    Action class for imitation learning: define action of class
    """

    def __init__(self):
        self.logger = logging.getLogger('agent')
        self.__actionMgr = ActionAPIMgr()

        self.mainImitationLearning = MainImitationLearning()
        self.mainImitationLearning.Init()
        self.cfgData = self.mainImitationLearning.cfgData
        self.actionsContextDict = self.mainImitationLearning.cfgData['actionsContextDict']
        self.actionName = self.mainImitationLearning.actionName
        self.actionDefine = self.mainImitationLearning.cfgData['actionDefine']
        self.taskActionDict = self.mainImitationLearning.taskActionDict
        self.preAction = [None] * len(self.taskActionDict)

        self.resetWaitTime = 5
        self.timeInit = -1

        self.timeNow = -1
        self.centerx = -1
        self.centery = -1
        self.radius = -1
        self.contactJoyStick = -1

        self.downStateDict = dict()
        #最多3个触点[0，1，2]
        for contact in range(3):
            self.downStateDict[contact] = False

    def Initialize(self, height, width):
        """
        Action initialization
        """
        self.logger.info('the resolution of action, height:%d, width:%d',  height, width)
        return self.__actionMgr.Initialize()

    def Finish(self):
        """
        Finish Action
        """
        self.__actionMgr.Finish()

    def ActionInit(self):
        """
        Moving initialization
        """
        self.__actionMgr.MovingInit(self.centerx, self.centery,
                                    self.radius, contact=self.contactJoyStick,
                                    frameSeq=-1, waitTime=100)

    def ActionFinish(self, frameIndex):
        """
        Moving Finish
        """
        self.__actionMgr.MovingFinish(frameSeq=frameIndex)

    def ActionResetContact(self, frameIndex):
        """
        reset contanct
        """
        for n in range(3):
            if n != self.contactJoyStick:
                if self.downStateDict[n]:
                    self.__actionMgr.Up(contact=n, frameSeq=frameIndex)
                    self.downStateDict[n] = False
            else:
                self.__actionMgr.Moving(-1, frameSeq=frameIndex)

    def DoAction(self, actionIdListInput, imgHeight, imgWidth, timeMs, frameIndex):
        """
        Do action of "actionId" for timeMs milliseconds
        """
        ratioX = imgWidth * 1. / self.cfgData['inputWidth']
        ratioY = imgHeight * 1. / self.cfgData['inputHeight']
        actionIdList = list()
        if len(self.taskActionDict) == 1:
            actionIdList.append(actionIdListInput)
        else:
            actionIdList = actionIdListInput

        self.ActionResetContact(frameIndex)

        for ind in range(len(actionIdList)):
            actionId = actionIdList[ind]

            if self.actionDefine is not None:
                actionIdOriList = self.taskActionDict[ind][actionId]["actionIDGroup"]

                # if self.preAction[ind] == actionId:
                #     continue

                self.preAction[ind] = actionId
                for actionIdOri in actionIdOriList:
                    if self.actionsContextDict[actionIdOri]['type'] == 'none':
                        # self.ActionResetContact(frameIndex)
                        continue

                    contact = self.actionsContextDict[actionIdOri]['contact']
                    if self.preAction[ind] != actionId:
                        if contact != self.contactJoyStick:
                            if self.downStateDict[contact]:
                                self.__actionMgr.Up(contact=contact, frameSeq=frameIndex)
                                self.downStateDict[contact] = False

                    actionType = self.actionsContextDict[actionIdOri]['type']
                    self.DoSpecificAction(actionIdOri, actionType, ratioX, ratioY, frameIndex)
            else:
                self.logger.error('Should define actionDefine in imitationLearning.json')

    def DoSpecificAction(self, actionId, actionType, ratioX, ratioY, frameIndex):
        """
        Do specific action
        actionType == none: no action
        actionType == click: click
        actionType == swipe: swipe
        actionType == joystick: use joystick
        """
        if actionType == 'none':
            return
        if actionType == 'click':
            if self.actionsContextDict[actionId]['updateBtn'] is True:
                contact = self.actionsContextDict[actionId]['contact']
                self.downStateDict[contact] = True
                self.__actionMgr.Down(self.actionsContextDict[actionId]['updateBtnX'],
                                      self.actionsContextDict[actionId]['updateBtnY'],
                                      contact=contact,
                                      frameSeq=frameIndex)
                self.logger.info('Use the updated button position based on task for actionId %d', actionId)
            else:
                actionX = int(self.actionsContextDict[actionId]['buttonX'] * ratioX)
                actionY = int(self.actionsContextDict[actionId]['buttonY'] * ratioY)
                contact = self.actionsContextDict[actionId]['contact']
                self.downStateDict[contact] = True
                self.logger.info('execute the click action for actionId %d', actionId)
                self.__actionMgr.Down(actionX,
                                      actionY,
                                      contact=contact,
                                      frameSeq=frameIndex)
        if actionType == 'key':
            actionX = int(self.actionsContextDict[actionId]['buttonX'] * ratioX)
            actionY = int(self.actionsContextDict[actionId]['buttonY'] * ratioY)
            alphabet = self.actionsContextDict[actionId]['alphabet']
            action_type = self.actionsContextDict[actionId]['action_type']
            action_text = self.actionsContextDict[actionId]['action_text']
            contact = self.actionsContextDict[actionId]['contact']

            self.logger.info('execute the key action for actionId %d', actionId)
            self.logger.info('key action, actionId:%d, actionX:%d, actionY:%d, contact:%d',
                             actionId, actionX, actionY, contact)
            self.logger.info('key action, actionId: %d, alphabet: %s, type: %s, text: %s',
                             actionId, alphabet, str(action_type), action_text)

            self.__actionMgr.SimulatorKeyAction(actionX, actionY, contact=contact, frameSeq=frameIndex,
                                                alphabet=alphabet, action_type=action_type, action_text=action_text)

        if actionType == 'swipe':
            swipeStartX = int(self.actionsContextDict[actionId]['swipeStartX'] * ratioX)
            swipeStartY = int(self.actionsContextDict[actionId]['swipeStartY'] * ratioY)
            swipeEndX = int(self.actionsContextDict[actionId]['swipeEndX'] * ratioX)
            swipeEndY = int(self.actionsContextDict[actionId]['swipeEndY'] * ratioY)

            self.__actionMgr.Swipe(swipeStartX, swipeStartY, swipeEndX, swipeEndY,
                                   contact=self.actionsContextDict[actionId]['contact'],
                                   frameSeq=frameIndex, durationMS=80, needUp=False)

        if actionType == 'joystick':
            self.timeNow = time.time()
            if self.timeNow - self.timeInit > self.resetWaitTime:
                self.centerx = int(self.actionsContextDict[actionId]['centerx'] * ratioX)
                self.centery = int(self.actionsContextDict[actionId]['centery'] * ratioY)
                self.radius = int(0.5 * (self.actionsContextDict[actionId]['rangeInner'] +
                                         self.actionsContextDict[actionId]['rangeOuter']) * ratioX)

                self.contactJoyStick = self.actionsContextDict[actionId]['contact']

                self.ActionInit()
                self.timeInit = self.timeNow

            self.__actionMgr.Moving(self.actionsContextDict[actionId]['angle'], frameSeq=frameIndex)
