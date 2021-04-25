# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__ + '/../../AgentAI')

from actionmanager.PCActionMgrExt import PCActionMgrExt

class PCActionAPIMgr(object):
    """
    Action API for AI do actions
    """
    def __init__(self):
        self.__actionMgr = PCActionMgrExt()
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

    def MouseMove(self, px, py, frameSeq=-1, waitTime=0):
        """
        Move the mouse to the target point(px, py) immediately.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.MouseMove(px, py, frameSeq=frameSeq, waitTime=waitTime)

    def LButtonClick(self, px, py, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Left mouse click the target point(px, py) on contact. Just Down the point and wait for durationMS
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.LButtonClick(px, py, frameSeq=frameSeq, waitTime=waitTime, durationMS=durationMS)

    def LButtonDoubleClick(self, px, py, frameSeq=-1, waitTime=0):
        """
        Left mouse double click target point(px, py).
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.LButtonDoubleClick(px, py, frameSeq=frameSeq, waitTime=waitTime)

    def RButtonClick(self, px, py, frameSeq=-1, waitTime=0):
        """
        Right mouse click the target point(px, py).
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.RButtonClick(px, py, frameSeq=frameSeq, waitTime=waitTime)

    def LButtonDrag(self, sx, sy, ex, ey, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Left mouse drag from point(sx, sy) to point(ex, ey)
        and then Up.
        :param sx: x of start point
        :param sy: y of start point
        :param ex: x of end point
        :param ey: y of end point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.LButtonDrag(sx, sy, ex, ey, frameSeq=frameSeq, waitTime=waitTime, durationMS=durationMS)

    def InputKey(self, keys, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Input key in the keys list
        :param keys: input keys
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        if not isinstance(keys, list):
            return

        self.__actionMgr.InputKey(keys, frameSeq=frameSeq, waitTime=waitTime, durationMS=durationMS)

    def InputString(self, inputString, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Input string text
        :param inputString: input string
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        if not self.__enableFlag:
            return

        self.__actionMgr.InputString(inputString, frameSeq=frameSeq, waitTime=waitTime, durationMS=durationMS)

    def SetEnable(self, enableFlag=True):
        """
        Set the module whether to send action based on enableFlag.
        :param enableFlag: if True, send action; otherwise, not.
        :return:
        """
        self.__enableFlag = enableFlag
