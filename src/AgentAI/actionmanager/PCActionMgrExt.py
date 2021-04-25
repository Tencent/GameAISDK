# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from .ActionMgr import ActionMgr

OP_MOUSE_MOVE = 0
OP_MOUSE_LONG_CLICK = 1
OP_MOUSE_DOUBLE_CLICK = 2
OP_MOUSE_RIGHT_CLICK = 3
OP_MOUSE_CLICK = 4   # pyIOService.msghandler.MsgHandler.py(_CreateUIActionList)定义的ACTION_ID_CLICK为4
OP_MOUSE_DRAG = 5  # pyIOService.msghandler.MsgHandler.py(_CreateUIActionList)定义的ACTION_ID_SWIPE为5
OP_KEY_INPUT = 6
OP_KEY_INPUT_STRING = 7
OP_MOUSE_LBUTTON_DOWN = 8
OP_MOUSE_LBUTTON_UP = 9
OP_SIMULATOR_KEY = 10

LOG = logging.getLogger('agent')

class PCActionMgrExt(object):
    """
    ActionMgr Extension implement for common use, based on ActionMgr
    """
    def __init__(self):
        self.__actionMgr = ActionMgr()
        self._last_contact_position = {}  # 对于Windows系统，contact的数量有且仅有一个

    def Initialize(self):
        """
        Initialize this module, call ActionMgr.Initialize
        :return:
        """
        return self.__actionMgr.Initialize()

    def Finish(self):
        """
        Finish this module, call ActionMgr.Finish
        :return:
        """
        self.__actionMgr.Finish()

    def SendAction(self, actionID, actionData, frameSeq=-1):
        """
        Send action to remote(client)
        :param actionID: the self-defined action ID
        :param actionData: the context data of the action ID
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        return self.__actionMgr.SendAction(actionID=actionID, actionData=actionData, frameSeq=frameSeq)

    def MouseMove(self, px, py, frameSeq=-1, waitTime=0):
        """
        Move the mouse to the target point(px, py) immediately.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime

        LOG.debug('send frame data, frameIndex= %d Move (%d, %d) Wait %dms',
                  frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_MOVE, actionData=actionData, frameSeq=frameSeq)

    def Click(self, px, py, contact=0, frameSeq=-1, durationMS=-1):
        LOG.debug('send frame data, frameSeq=%d, px=%d, py=%d, contact=%d, durationMS=%d',
                  frameSeq, px, py, contact, durationMS)

        return self.LButtonClick(px, py, frameSeq, 0)

    def LButtonClick(self, px, py, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Left mouse click the target point(px, py). Just Down the point and wait for durationMS
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime

        actionTmpID = OP_MOUSE_CLICK
        if durationMS > 0:
            actionData['during_time'] = durationMS
            actionTmpID = OP_MOUSE_LONG_CLICK

        LOG.debug('send frame data, frameIndex=%d LMouse click (%d, %d) Wait %dms',
                  frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=actionTmpID, actionData=actionData, frameSeq=frameSeq)

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
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime

        LOG.debug('send frame data, frameIndex=%d LMouse double click (%d, %d) Wait %dms',
                  frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_DOUBLE_CLICK, actionData=actionData, frameSeq=frameSeq)

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
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime

        LOG.debug('send frame data, frameIndex=%d RMouse click (%d, %d) Wait %dms', frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_RIGHT_CLICK, actionData=actionData, frameSeq=frameSeq)

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
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['start_x'] = sx
        actionData['start_y'] = sy
        actionData['end_x'] = ex
        actionData['end_y'] = ey
        actionData['wait_time'] = waitTime
        actionData['during_time'] = durationMS

        LOG.debug('send frame data, frameIndex=%d LMouse drag (%d, %d)->(%d, %d)'
                  ' Wait %dms duration %dms', frameSeq, sx, sy, ex, ey, waitTime, durationMS)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_DRAG, actionData=actionData, frameSeq=frameSeq)

    def InputKey(self, keys, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Input key in the keys list
        :param keys: input keys
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['keys'] = keys
        actionData['wait_time'] = waitTime
        actionData['during_time'] = durationMS

        LOG.debug('send frame data, frameIndex=%d input key %s Wait %dms duration %dms',
                  frameSeq, str(keys), waitTime, durationMS)

        return self.__actionMgr.SendAction(actionID=OP_KEY_INPUT, actionData=actionData, frameSeq=frameSeq)

    def InputString(self, inputString, frameSeq=-1, waitTime=0, durationMS=0):
        """
        Input string text
        :param inputString: input string
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['key_string'] = inputString
        actionData['wait_time'] = waitTime
        actionData['during_time'] = durationMS

        LOG.debug('send frame data, frameIndex=%d input string %s Wait %dms duration %dms',
                  frameSeq, str(inputString), waitTime, durationMS)

        return self.__actionMgr.SendAction(actionID=OP_KEY_INPUT_STRING, actionData=actionData, frameSeq=frameSeq)

    def Reset(self, frameSeq=-1):
        """
        Call Reset action to reset all contacts to up and clear all the actions in the queue.
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        LOG.debug('send frame data of reset, frameSeq:%d', frameSeq)
        return True

    def Down(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Down the target point(px, py) on contact.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime
        self._last_contact_position[contact] = (px, py)
        LOG.debug('send frame data, frameIndex=%d Mouse Down (%d, %d) Wait %dms', frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_LBUTTON_DOWN, actionData=actionData, frameSeq=frameSeq)

    def Up(self, contact=0, frameSeq=-1, waitTime=0):
        """
        Up the contact.
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        if contact not in self._last_contact_position:
            return True
        px, py = self._last_contact_position[contact]

        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['wait_time'] = waitTime
        self._last_contact_position[contact] = (px, py)
        LOG.debug('send frame data, frameIndex=%d Mouse up (%d, %d) Wait %dms', frameSeq, px, py, waitTime)

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_LBUTTON_UP, actionData=actionData, frameSeq=frameSeq)

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
        LOG.debug('send frame data, frameIndex=%d swipe (%d, %d)-(%d, %d) contact %d needUp %s Wait %dms',
                  frameSeq, sx, sy, ex, ey, contact, durationMS, str(needUp))
        return self.LButtonDrag(sx, sy, ex, ey, frameSeq, waitTime=0, durationMS=durationMS)

    def SimulatorKeyAction(self, px, py, contact=0, frameSeq=-1, alphabet="", action_type="", action_text=""):
        """ 发送模拟器键

        :param px: 坐标x，没用上
        :param py: 坐标y，没用上
        :param contact: 触控点，没用上
        :param frameSeq: 帧序号
        :param alphabet: 字母，不为空
        :param action_type: 动作类型
        :param action_text: 当action_type为text时，有效
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        actionData['px'] = px
        actionData['py'] = py
        actionData['contact'] = contact
        actionData['alphabet'] = alphabet
        actionData['action_type'] = action_type
        actionData['action_text'] = action_text
        LOG.debug('send the key action, px: %d, py:%d, frameIndex:%d, alphabet:%s, action_type: %s, action_text: %s',
                  px, py, frameSeq, alphabet, str(action_type), action_text)

        return self.__actionMgr.SendAction(actionID=OP_SIMULATOR_KEY, actionData=actionData, frameSeq=frameSeq)
