# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging
import os

from .MobileActionMgrExt import MobileActionMgrExt

LOG = logging.getLogger('agent')


ACTION_TYPE_NONE = 0
ACTION_TYPE_PRESS_DOWN = 1
ACTION_TYPE_PRESS_UP = 2
ACTION_TYPE_CLICK = 3
ACTION_TYPE_SWIPE_ONCE = 4
ACTION_TYPE_SWIPE_ALONG = 5


class ActionController(object):
    """
    ActionController implement for GIE, based on MobileActionMgrExt
    """
    def __init__(self):
        self.__actionMgr = MobileActionMgrExt()
        self.__actionsDict = {}
        self.__actionsNum = 0
        self.__pressDownLastPx = -1
        self.__pressDownLastPy = -1
        self.__pressDownLastContact = -1

    def Initialize(self, cfgFilePath):
        """
        Initialize this module, load config from config file
        :param cfgFilePath: the path to config file
        :return: True or false
        """
        if not os.path.exists(cfgFilePath):
            LOG.error('Action Json Config file not exists[{0}]'.format(cfgFilePath))
            return False

        self._LoadActionData(cfgFilePath)

        return self.__actionMgr.Initialize()

    def Finish(self):
        """
        Finish this module
        :return:
        """
        self.__actionMgr.Finish()

    def Reset(self, frameSeq=-1):
        """
        Reset this module
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        self.__actionMgr.Reset(frameSeq)

    def DoAction(self, actionID, frameSeq=-1):
        """
        Do the specific action corresponding to the actionID
        :param actionID: actionID enum:
                            ACTION_TYPE_NONE = 0
                            ACTION_TYPE_PRESS_DOWN = 1
                            ACTION_TYPE_PRESS_UP = 2
                            ACTION_TYPE_CLICK = 3
                            ACTION_TYPE_SWIPE_ONCE = 4
                            ACTION_TYPE_SWIPE_ALONG = 5
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        if actionID not in range(self.__actionsNum):
            return

        actionContext = self.__actionsDict.get(actionID)
        actionType = actionContext.get('type')
        if actionType == ACTION_TYPE_NONE:
            self.DoNothing(frameSeq=frameSeq)
        elif actionType == ACTION_TYPE_PRESS_DOWN:
            px = actionContext.get('x')
            py = actionContext.get('y')
            contact = actionContext.get('contact')
            self.PressDown(px, py, contact=contact, frameSeq=frameSeq)
        elif actionType == ACTION_TYPE_PRESS_UP:
            px = actionContext.get('x')
            py = actionContext.get('y')
            contact = actionContext.get('contact')
            self.PressUp(px, py, contact=contact, frameSeq=frameSeq)
        elif actionType == ACTION_TYPE_CLICK:
            px = actionContext.get('x')
            py = actionContext.get('y')
            contact = actionContext.get('contact')
            durationMS = actionContext.get('durationMS')
            if durationMS is not None:
                self.Click(px, py, contact=contact, frameSeq=frameSeq, durationMS=durationMS)
            else:
                self.Click(px, py, contact=contact, frameSeq=frameSeq)
        elif actionType == ACTION_TYPE_SWIPE_ONCE:
            sx = actionContext.get('startX')
            sy = actionContext.get('startY')
            ex = actionContext.get('endX')
            ey = actionContext.get('endY')
            contact = actionContext.get('contact')
            durationMS = actionContext.get('durationMS')
            if durationMS is not None:
                self.SwipeOnce(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq,
                               durationMS=durationMS)
            else:
                self.SwipeOnce(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq)

    def GetActionNum(self):
        """
        Get the number of actions defined in config file
        :return: the number of actions
        """
        return self.__actionsNum

    def DoNothing(self, frameSeq=-1):
        """
        Do nothing
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        LOG.debug('DoNothing on frameSeq[{0}]'.format(frameSeq))

    def PressDown(self, px, py, contact=0, forced=False, frameSeq=-1):
        """
        Down the target point(px, py) on contact.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param forced: if True, force press down without check already pressed down
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        if not forced and self._IsPressDownAlready(px, py, contact):
            return
        self.__actionMgr.Down(px, py, contact=contact, frameSeq=frameSeq)
        self.__pressDownLastPx = px
        self.__pressDownLastPy = py
        self.__pressDownLastContact = contact
        LOG.debug('PressDown ({0}, {1}) on frameSeq[{2}]'.format(px, py, frameSeq))

    def PressUp(self, px, py, contact=0, frameSeq=-1):
        """
        Up the contact.
        :param px: x of target point, depreciated, not used
        :param py: y of target point, depreciated, not used
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        self.__actionMgr.Up(contact=contact, frameSeq=frameSeq)
        self._ClearPressDown(contact)
        LOG.debug('PressUp ({0}, {1}) on frameSeq[{2}]'.format(px, py, frameSeq))

    def Click(self, px, py, contact=0, frameSeq=-1, durationMS=-1):
        """
        Click the target point(px, py) on contact. Just Down the point and wait for durationMS
        and then Up.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        self.__actionMgr.Click(px, py, contact=contact, frameSeq=frameSeq, durationMS=durationMS)
        self._ClearPressDown(contact)
        LOG.debug('Click ({0}, {1}) on frameSeq[{2}]'.format(px, py, frameSeq))

    def SwipeOnce(self, sx, sy, ex, ey, contact=0, frameSeq=-1, durationMS=50, needUp=True):
        """
        Swipe from start point(sx, sy) to end point(ex, ey) on contact. The process
        costs durationMS time.
        :param sx: x of start point
        :param sy: y of start point
        :param ex: x of end point
        :param ey: y of end point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param durationMS: the duration time(ms) in this process
        :param needUp: if True, the end point will Up; otherwise, will always Down the end point
        until next action on the contact.
        :return:
        """
        self.__actionMgr.Swipe(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq,
                               durationMS=durationMS, needUp=needUp)
        self._ClearPressDown(contact)
        LOG.debug('SwipeOnce ({0}, {1})->({2}, {3}) on frameSeq[{4}]'.format(sx, sy, ex, ey,
                                                                             frameSeq))

    def _LoadActionData(self, actionCfgFile):
        with open(actionCfgFile) as fileData:
            data = json.load(fileData)
            self.__actionsNum = len(data['actions'])
            for item in data['actions']:
                self.__actionsDict[item['id']] = item

    def _ClearPressDown(self, contact):
        if self.__pressDownLastContact == contact:
            self.__pressDownLastPx = -1
            self.__pressDownLastPy = -1
            self.__pressDownLastContact = -1

    def _IsPressDownAlready(self, px, py, contact):
        if self.__pressDownLastPx == px and self.__pressDownLastPy == py \
                and self.__pressDownLastContact == contact:
            return True
        return False
