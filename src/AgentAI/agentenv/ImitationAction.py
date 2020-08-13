# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time
import sys

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
        self.actionsContextList = self.mainImitationLearning.cfgData['actionsContextList']
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

    def Initialize(self, height, width):
        """
        Action initialization
        """
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
                self.__actionMgr.Up(contact=n, frameSeq=frameIndex)
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

        for ind, actionId in enumerate(actionIdList):
            if self.actionDefine is not None:
                actionIdOriList = self.taskActionDict[ind][actionId]["actionIDGroup"]

                # if self.preAction[ind] == actionId:
                #     continue

                self.preAction[ind] = actionId
                for actionIdOri in actionIdOriList:
                    if self.actionsContextList[actionIdOri]['type'] == 0:
                        # self.ActionResetContact(frameIndex)
                        continue

                    contact = self.actionsContextList[actionIdOri]['contact']
                    if self.preAction[ind] != actionId:
                        if contact != self.contactJoyStick:
                            self.__actionMgr.Up(contact=contact, frameSeq=frameIndex)

                    actionType = self.actionsContextList[actionIdOri]['type']
                    self.DoSpecificAction(actionIdOri, actionType, ratioX, ratioY, frameIndex)

            else:
                self.logger.error('Should define actionDefine in imitationLearning.json')

    def DoSpecificAction(self, actionId, actionType, ratioX, ratioY, frameIndex):
        """
        Do specific action
        actionType == 0: no action
        actionType == 3: click
        actionType == 4: swipe
        actionType == 5: use joystick
        """
        if actionType == 0:
            return
        if actionType == 3:
            actionX = int((self.actionsContextList[actionId]['regionX1'] +
                           self.actionsContextList[actionId]['regionX2']) / 2 * ratioX)
            actionY = int((self.actionsContextList[actionId]['regionY1'] +
                           self.actionsContextList[actionId]['regionY2']) / 2 * ratioY)
            self.__actionMgr.Down(actionX, actionY,
                                  contact=self.actionsContextList[actionId]['contact'],
                                  frameSeq=frameIndex)

        if actionType == 4:
            swipeStartX = int(self.actionsContextList[actionId]['swipeStartX'] * ratioX)
            swipeStartY = int(self.actionsContextList[actionId]['swipeStartY'] * ratioY)
            swipeEndX = int(self.actionsContextList[actionId]['swipeEndX'] * ratioX)
            swipeEndY = int(self.actionsContextList[actionId]['swipeEndY'] * ratioY)

            self.__actionMgr.Swipe(swipeStartX, swipeStartY, swipeEndX, swipeEndY,
                                   contact=self.actionsContextList[actionId]['contact'],
                                   frameSeq=frameIndex, durationMS=80, needUp=False)

        if actionType == 5:
            self.timeNow = time.time()
            if self.timeNow - self.timeInit > self.resetWaitTime:
                self.centerx = int(self.actionsContextList[actionId]['centerx'] * ratioX)
                self.centery = int(self.actionsContextList[actionId]['centery'] * ratioY)
                self.radius = int(0.5 * (self.actionsContextList[actionId]['rangeInner'] +
                                         self.actionsContextList[actionId]['rangeOuter']) * ratioX)

                self.contactJoyStick = self.actionsContextList[actionId]['contact']

                self.ActionInit()
                self.timeInit = self.timeNow

            self.__actionMgr.Moving(self.actionsContextList[actionId]['angle'], frameSeq=frameIndex)
