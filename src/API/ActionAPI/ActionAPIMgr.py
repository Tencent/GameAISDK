# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__ + '/../../AgentAI')

from actionmanager.MobileActionMgrExt import MobileActionMgrExt


class ActionAPIMgr(object):
    """
    Action API for AI do actions
    """
    def __init__(self):
        self.__actionMgr = MobileActionMgrExt()
        self.__enableFlag = True

    def Initialize(self):
        """
        Call this initialize method before any other methods.
        :return: True or false
        """
        return self.__actionMgr.Initialize()

    def Finish(self):
        """
        Call this method at the end of process.
        :return:
        """
        self.__actionMgr.Finish()

    def SendAction(self, actionID, actionData, frameSeq=-1):
        """
        Raw interface for send action to client.
        :param actionID: actionID
        :param actionData: the action context data correspond to actionID
        :param frameSeq: frameSeq
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.SendAction(actionID, actionData, frameSeq=frameSeq)

    def Reset(self, frameSeq=-1):
        """
        Call Reset action to reset all contacts to up and clear all the actions in the queue.
        :param frameSeq: frameSeq
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Reset(frameSeq=frameSeq)

    def MovingInit(self, centerX, centerY, radius, contact=0, frameSeq=-1, waitTime=1000):
        """
        Initialize the center point, radius and contact of the moving control panel. Just Down the
        center point and wait some time.
        :param centerX: x of center point
        :param centerY: y of center point
        :param radius: radius of the moving control panel
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.MovingInit(centerX, centerY, radius, contact=contact,
                                    frameSeq=frameSeq, waitTime=waitTime)

    def MovingFinish(self, frameSeq=-1):
        """
        Finsih the the moving control panel. Just Up the contact.
        :param frameSeq: frameSeq
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.MovingFinish(frameSeq=frameSeq)

    def Moving(self, dirAngle, frameSeq=-1, durationMS=50):
        """
        Move the contact in MovingInit() to the dirAngle point which is computed by center
        point, radius and dirAngle(0:forward, 90:right, 180:backward, 270:left).
        :param dirAngle: the angle([0, 360)) of moving direction
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Moving(dirAngle, frameSeq=frameSeq, durationMS=durationMS)

    def Move(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Move the contact to the target point(px, py) immediately. No make up points in the process.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Move(px, py, contact=contact, frameSeq=frameSeq, waitTime=waitTime)

    def Click(self, px, py, contact=0, frameSeq=-1, durationMS=-1):
        """
        Click the target point(px, py) on contact. Just Down the point and wait for durationMS
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Click(px, py, contact=contact, frameSeq=frameSeq, durationMS=durationMS)

    def Down(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Down the target point(px, py) on contact.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Down(px, py, contact=contact, frameSeq=frameSeq, waitTime=waitTime)

    def Up(self, contact=0, frameSeq=-1, waitTime=0):
        """
        Up the contact.
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Up(contact=contact, frameSeq=frameSeq, waitTime=waitTime)

    def Swipe(self, sx, sy, ex, ey, contact=0, frameSeq=-1, durationMS=50, needUp=True):
        """
        Swipe from start point(sx, sy) to end point(ex, ey) on contact. The process
        costs durationMS time.
        :param sx: x of start point
        :param sy: y of start point
        :param ex: x of end point
        :param ey: y of end point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :param needUp: if True, the end point will Up; otherwise, will always Down the end point
        until next action on the contact.
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.Swipe(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq,
                               durationMS=durationMS, needUp=needUp)

    def SwipeMove(self, px, py, contact=0, frameSeq=-1, durationMS=50):
        """
        Move the contact to the target point(px, py) with make up points in the process.
        The process costs durationMS time.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: frameSeq
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.SwipeMove(px, py, contact=contact, frameSeq=frameSeq,
                                   durationMS=durationMS)

    def SetEnable(self, enableFlag=True):
        """
        Set the module whether to send action based on enableFlag.
        :param enableFlag: if True, send action; otherwise, not.
        :return:
        """
        self.__enableFlag = enableFlag
