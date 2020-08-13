# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from .ActionMgr import ActionMgr

OP_MOUSE_MOVE = 0
OP_MOUSE_CLICK = 1
OP_MOUSE_DOUBLE_CLICK = 2
OP_MOUSE_RIGHT_CLICK = 3
OP_MOUSE_LONG_CLICK = 4
OP_MOUSE_DRAG = 5
OP_KEY_INPUT = 6
OP_KEY_INPUT_STRING = 7

LOG = logging.getLogger('agent')

class PCActionMgrExt(object):
    """
    ActionMgr Extension implement for common use, based on ActionMgr
    """
    def __init__(self):
        self.__actionMgr = ActionMgr()

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

        LOG.debug('send frame data, frameIndex={} Move ({}, {}) Wait {}ms'.format(frameSeq, px, py, waitTime))

        return self.__actionMgr.SendAction(actionID=OP_MOUSE_MOVE, actionData=actionData, frameSeq=frameSeq)

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

        LOG.debug('send frame data, frameIndex={} LMouse click ({}, {}) Wait {}ms'.format(frameSeq, px, py, waitTime))

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

        LOG.debug('send frame data, frameIndex={} LMouse double click ({}, {})'
                  ' Wait {}ms'.format(frameSeq, px, py, waitTime))

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

        LOG.debug('send frame data, frameIndex={} RMouse click ({}, {}) Wait {}ms'.format(frameSeq, px, py, waitTime))

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

        LOG.debug('send frame data, frameIndex={} LMouse drag ({}, {})->({}, {})'
                  ' Wait {}ms duration {}ms'.format(frameSeq, sx, sy, ex, ey, waitTime, durationMS))

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

        LOG.debug('send frame data, frameIndex={} input key {} '
                  'Wait {}ms duration {}ms'.format(frameSeq, keys, waitTime, durationMS))

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

        LOG.debug('send frame data, frameIndex={} input string {} '
                  'Wait {}ms duration {}ms'.format(frameSeq, inputString, waitTime, durationMS))

        return self.__actionMgr.SendAction(actionID=OP_KEY_INPUT_STRING, actionData=actionData, frameSeq=frameSeq)
