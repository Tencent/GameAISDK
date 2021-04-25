# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging
import os

from .MobileActionMgrExt import MobileActionMgrExt
from .PCActionMgrExt import PCActionMgrExt

LOG = logging.getLogger('agent')


ACTION_TYPE_NONE = 'none'
ACTION_TYPE_PRESS_DOWN = 'down'
ACTION_TYPE_PRESS_UP = 'up'
ACTION_TYPE_CLICK = 'click'
ACTION_TYPE_SWIPE_ONCE = 'swipe'
ACTION_TYPE_KEY = 'key'


class DeviceType(object):
    ANDROID = "Android"
    IOS = "IOS"
    WINDOWS = "Windows"


class ActionController(object):
    """
    ActionController implement for GIE, based on MobileActionMgrExt
    """
    def __init__(self):
        device_type = os.environ.get('AISDK_DEVICE_TYPE', DeviceType.ANDROID)
        if device_type == DeviceType.WINDOWS:
            self.__actionMgr = PCActionMgrExt()
        else:
            self.__actionMgr = MobileActionMgrExt()
        self.__actionsDict = dict()
        self.__actionsNum = 0
        self.__pressDownLastPx = -1
        self.__pressDownLastPy = -1
        self.__pressDownLastContact = -1
        self.__width = -1
        self.__height = -1
        self.__real_width = -1
        self.__real_height = -1

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
                            ACTION_TYPE_NONE = none
                            ACTION_TYPE_PRESS_DOWN = down
                            ACTION_TYPE_PRESS_UP = up
                            ACTION_TYPE_CLICK = click
                            ACTION_TYPE_SWIPE_ONCE = swipe
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        if actionID not in range(self.__actionsNum):
            return

        actionContext = self.__actionsDict.get(actionID)
        actionType = actionContext.get('type')
        LOG.debug("the actionID is {0} and type is {1}".format(actionID, actionType))

        if self.__real_height < 0 or self.__real_width < 0:
            LOG.warning("the real width or height invalid, width:{}, height:{}".format(self.__real_width,
                                                                                       self.__real_height))
            return

        if actionType == ACTION_TYPE_NONE:
            self.DoNothing(frameSeq=frameSeq)

        elif actionType == ACTION_TYPE_PRESS_DOWN:
            contact = actionContext.get('contact')


            px = self.__get_real_x(actionContext)
            py = self.__get_real_y(actionContext)
            LOG.debug("press down px:{0}, py:{1},contact:{2}, frameSeq:{3}".format(px, py, contact, frameSeq))
            self.PressDown(px, py, contact=contact, frameSeq=frameSeq)

        elif actionType == ACTION_TYPE_PRESS_UP:
            px = self.__get_real_x(actionContext)
            py = self.__get_real_y(actionContext)
            contact = actionContext.get('contact')
            LOG.debug("press up px:{0}, py:{1},contact:{2}, frameSeq:{3}".format(px, py, contact, frameSeq))
            self.PressUp(px, py, contact=contact, frameSeq=frameSeq)

        elif actionType == ACTION_TYPE_CLICK:
            contact = actionContext.get('contact')
            if 'updateBtn' in self.__actionsDict[actionID] and self.__actionsDict[actionID]['updateBtn'] is True:
                px = self.__actionsDict[actionID]['updateBtnX']
                py = self.__actionsDict[actionID]['updateBtnY']
                real_px = int(float(px) * float(self.__real_width) / float(self.__width))
                real_py = int(float(py) * float(self.__real_height) / float(self.__height))
                LOG.debug("press down real_px:{0}, real_py:{1}, contact:{2}".format(px, py, contact))
                self.PressDown(real_px, real_py, contact=contact, frameSeq=frameSeq)
                return
            px = self.__get_real_x(actionContext)
            py = self.__get_real_y(actionContext)

            duration_ms = actionContext.get('durationMS')
            if duration_ms is not None:
                LOG.debug("click px:{0}, py:{1},contact:{2}, frameSeq:{3}, durationMS:{4}".format(px, py, contact,
                                                                                                  frameSeq,
                                                                                                  duration_ms))
                self.Click(px, py, contact=contact, frameSeq=frameSeq, durationMS=duration_ms)
            else:
                LOG.debug("click px:{0}, py:{1},contact:{2}, frameSeq:{3}".format(px, py, contact, frameSeq))
                self.Click(px, py, contact=contact, frameSeq=frameSeq)

        elif actionType == ACTION_TYPE_KEY:
            px = self.__get_real_x(actionContext)
            py = self.__get_real_y(actionContext)
            contact = actionContext.get('contact')
            alphabet = actionContext.get('actionRegion').get('alphabet')
            action_type = actionContext.get('actionRegion').get('actionType')
            action_text = actionContext.get('actionRegion').get('text')
            LOG.debug("key action px:{0}, py:{1},contact:{2}, frameSeq:{3}, alphabet:{4}, action_type:{5}".format(
                px, py, contact, frameSeq, alphabet, action_type))

            self.SimulatorKeyAction(px, py, contact=contact, alphabet=alphabet, action_type=action_type,
                                    action_text=action_text)

        elif actionType == ACTION_TYPE_SWIPE_ONCE:
            sx = actionContext.get('actionRegion').get('region').get('startX')
            sy = actionContext.get('actionRegion').get('region').get('startY')
            ex = actionContext.get('actionRegion').get('region').get('endX')
            ey = actionContext.get('actionRegion').get('region').get('endY')
            contact = actionContext.get('contact')
            duration_ms = actionContext.get('durationMS')
            if duration_ms is not None:
                self.SwipeOnce(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq, durationMS=duration_ms)
            else:
                self.SwipeOnce(sx, sy, ex, ey, contact=contact, frameSeq=frameSeq)

    def __get_real_x(self, action_context):
        px = action_context.get('actionRegion').get('region').get('x')
        real_px = int(float(px) * float(self.__real_width) / float(self.__width))
        return real_px

    def __get_real_y(self, action_context):
        py = action_context.get('actionRegion').get('region').get('y')
        real_py = int(float(py) * float(self.__real_height) / float(self.__height))
        return real_py

    def GetActionNum(self):
        """
        Get the number of actions defined in config file
        :return: the number of actions
        """
        return self.__actionsNum

    @staticmethod
    def DoNothing(frameSeq=-1):
        """
        Do nothing
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        LOG.debug('DoNothing on frameSeq[{0}]'.format(frameSeq))

    def SetSolution(self, width, height):
        self.__real_height = height
        self.__real_width = width

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

    def SimulatorKeyAction(self, px, py, contact=0, frameSeq=-1, alphabet="", action_type="", action_text=""):
        self.__actionMgr.SimulatorKeyAction(px, py, contact, frameSeq, alphabet, action_type, action_text)
        LOG.debug('SimulatorKeyAction ({0}, {1}) on frameSeq[{2}]'.format(px, py, frameSeq))


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
            self.__width = data['screenWidth']
            self.__height = data['screenHeight']

            for item in data['actions']:
                self.__actionsDict[item['id']] = item

            LOG.info("the actionDict is %s, width: %d, height: %d", str(self.__actionsDict),
                     self.__width, self.__height)

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

    def get_action_dict(self):
        return self.__actionsDict
