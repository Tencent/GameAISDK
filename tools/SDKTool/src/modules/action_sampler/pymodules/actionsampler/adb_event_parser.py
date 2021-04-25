# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from abc import ABCMeta
import numpy as np

ABS_MT_TRACKING_ID = b'ABS_MT_TRACKING_ID'
ABS_MT_POSITION_X = b'ABS_MT_POSITION_X'
ABS_MT_POSITION_Y = b'ABS_MT_POSITION_Y'
ABS_MT_PRESSURE = b'ABS_MT_PRESSURE'
ABS_MT_TOUCH_MAJOR = b'ABS_MT_TOUCH_MAJOR'
ABS_MT_WIDTH_MAJOR = b'ABS_MT_WIDTH_MAJOR'
SYN_REPORT = b'SYN_REPORT'
ABS_MT_SLOT = b'ABS_MT_SLOT'
BTN_TOUCH = b'BTN_TOUCH'
SYN_MT_REPORT = b'SYN_MT_REPORT'

BTN_TOUCH_VALUE_UP = b'UP'
INVALID_TRACKING_ID = b'ffffffff'

MULTI_TOUCH_NUM_MAX = 10

LOG = logging.getLogger('action_sampler')


class TouchPoint(object):
    """
    数据结构，存放触点信息，包含(x, y)坐标，trackingid跟踪的唯一ID
    """

    def __init__(self, trackingId, x=None, y=None):
        self.trackingId = trackingId
        self.x = x
        self.y = y

    def __repr__(self):
        return 'Point[({0}, {1})@{2}]'.format(self.x, self.y, self.trackingId)

    def __sub__(self, other):  # minus method
        return np.array([self.x - other.x, self.y - other.y])


class ADBEventItem(object):
    """
    数据结构，存放ADB shell getevent返回的事件解析出来的结果
    """

    def __init__(self, timestamp, deviceID, eventType, eventCode, eventValue):
        self.timestamp = timestamp
        self.deviceID = deviceID
        self.eventType = eventType
        self.eventCode = eventCode
        self.eventValue = eventValue

    def __repr__(self):
        return '{0} {1} {2}'.format(self.eventType, self.eventCode, self.eventValue)


class ADBEventParser(object):
    __metaclass__ = ABCMeta

    def __init__(self, multiTouchNumMax=MULTI_TOUCH_NUM_MAX):
        self._mtNumMax = multiTouchNumMax
        self._trackedPoints = [None] * self._mtNumMax  # 返回的触点结果列表，里面有mtNumMax个元素，对应mtNumMax个触点的TouchPoint对象

    def get_touch_points(self):
        return self._trackedPoints

    def parse(self, line):
        raise NotImplementedError()


class ADBEventParserTypeA(ADBEventParser):
    """
    实现TypeA设备的解析
    """

    def __init__(self, multiTouchNumMax):
        ADBEventParser.__init__(self, multiTouchNumMax)
        self.__trackingId = None
        self.__trackedMTPoints = [None] * self._mtNumMax
        self.__x = 0
        self.__y = 0

    def parse(self, line):
        line = line.split()
        if len(line) != 4:
            return
        eventItem = ADBEventItem(None, line[0], line[1], line[2], line[3])
        self._do_parse_item(eventItem)

    def _do_parse_item(self, eventItem):
        eventCode = eventItem.eventCode
        eventValue = eventItem.eventValue
        LOG.debug('eventCode[{0}], eventValue[{1}]'.format(eventCode, eventValue))

        if eventCode == ABS_MT_TRACKING_ID:
            trackingId = int(eventValue, 16)
            self.__trackingId = trackingId
        elif eventCode == ABS_MT_POSITION_X:
            x = int(eventValue, 16)
            self.__x = x
        elif eventCode == ABS_MT_POSITION_Y:
            y = int(eventValue, 16)
            self.__y = y
        elif eventCode == ABS_MT_PRESSURE:
            pass
        elif eventCode == ABS_MT_TOUCH_MAJOR:
            pass
        elif eventCode == ABS_MT_WIDTH_MAJOR:
            pass
        elif eventCode == SYN_REPORT:
            self._handle_syn_report()
        elif eventCode == SYN_MT_REPORT:
            self._handle_syn_mtreport()
        elif eventCode == BTN_TOUCH:
            self.__btnTouch = eventValue
        else:
            LOG.debug('Unknown event code[{0}]'.format(eventCode))

    def _handle_syn_report(self):
        self._trackedPoints = self.__trackedMTPoints
        self.__trackedMTPoints = [None] * self._mtNumMax
        self.__trackingId = None

    def _handle_syn_mtreport(self):
        if self.__trackingId is not None:
            self.__trackedMTPoints[self.__trackingId] = TouchPoint(self.__trackingId, self.__x, self.__y)


class ADBEventParserTypeB(ADBEventParser):
    """
    实现TypeB设备的解析
    """

    def __init__(self, multiTouchNumMax):
        ADBEventParser.__init__(self, multiTouchNumMax)
        self.__slot = 0
        self.__firstEventFound = False
        self.__x = 0
        self.__y = 0

    def parse(self, line):
        line = line.split()
        if len(line) != 4:
            return
        eventItem = ADBEventItem(None, line[0], line[1], line[2], line[3])
        self._do_parse_item(eventItem)

    def _do_parse_item(self, eventItem):
        eventCode = eventItem.eventCode
        eventValue = eventItem.eventValue

        if self.__firstEventFound:
            if eventCode == ABS_MT_TRACKING_ID:
                self._handle_tracking_id(eventValue)
            elif eventCode == ABS_MT_POSITION_X:
                x = int(eventValue, 16)
                self._trackedPoints[self.__slot].x = x
                self.__x = x
            elif eventCode == ABS_MT_POSITION_Y:
                y = int(eventValue, 16)
                self._trackedPoints[self.__slot].y = y
                self.__y = y
            elif eventCode == ABS_MT_PRESSURE:
                pass
            elif eventCode == ABS_MT_TOUCH_MAJOR:
                pass
            elif eventCode == ABS_MT_WIDTH_MAJOR:
                pass
            elif eventCode == SYN_REPORT:
                pass
            elif eventCode == ABS_MT_SLOT:
                slot = int(eventValue, 16)
                self.__slot = slot
            elif eventCode == BTN_TOUCH:
                if eventValue == BTN_TOUCH_VALUE_UP:
                    self._trackedPoints[self.__slot] = None
            else:
                LOG.debug('Unknown event code[{0}]'.format(eventCode))
        else:
            if eventCode == ABS_MT_SLOT:
                slot = int(eventValue, 16)
                self.__slot = slot
            elif eventCode == ABS_MT_TRACKING_ID and eventValue != INVALID_TRACKING_ID:
                self._handle_tracking_id(eventValue)
                self.__firstEventFound = True

    def _handle_tracking_id(self, trackingId):
        if trackingId == INVALID_TRACKING_ID:
            self._trackedPoints[self.__slot] = None
        else:
            self._trackedPoints[self.__slot] = TouchPoint(trackingId, self.__x, self.__y)
