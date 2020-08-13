# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import math

from .ActionMgr import ActionMgr

MAX_CONTACTS = 10
ACTION_ID_RESET = 0
ACTION_ID_DOWN = 1
ACTION_ID_UP = 2
ACTION_ID_MOVE = 3
ACTION_ID_CLICK = 4
ACTION_ID_SWIPE = 5
ACTION_ID_SWIPEDOWN = 6
ACTION_ID_SWIPEMOVE = 7

LOG = logging.getLogger('agent')

class MobileActionMgrExt(object):
    """
    ActionMgr Extension implement for common use, based on ActionMgr
    """
    def __init__(self):
        self.__actionMgr = ActionMgr()
        self.__contactPoints = [None] * MAX_CONTACTS

        self.__movingRadius = None
        self.__movingContact = None
        self.__movingCx = None
        self.__movingCy = None
        self.__movingFlag = False

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

    def Reset(self, frameSeq=-1):
        """
        Call Reset action to reset all contacts to up and clear all the actions in the queue.
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        actionData = dict()
        actionData['img_id'] = frameSeq
        LOG.debug('send frame data, frameIndex={0} Reset'.format(frameSeq))
        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_RESET, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints = [None] * MAX_CONTACTS
            return True
        return False

    def SendAction(self, actionID, actionData, frameSeq=-1):
        """
        Send action to remote(client)
        :param actionID: the self-defined action ID
        :param actionData: the context data of the action ID
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        return self.__actionMgr.SendAction(actionID=actionID, actionData=actionData,
                                           frameSeq=frameSeq)

    def MovingInit(self, centerX, centerY, radius, contact=0, frameSeq=-1, waitTime=1000):
        """
        Initialize the center point, radius and contact of the moving control panel. Just Down the
        center point and wait some time.
        :param centerX: x of center point
        :param centerY: y of center point
        :param radius: radius of the moving control panel
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        LOG.debug('MovingInit c({0}, {1}) r={2} contact={3} Wait {4}ms'.format(centerX,
                                                                               centerY,
                                                                               radius,
                                                                               contact,
                                                                               waitTime))
        ret = self.Down(centerX, centerY, contact=contact, frameSeq=frameSeq, waitTime=waitTime)
        if ret:
            self.__movingRadius = radius
            self.__movingContact = contact
            self.__movingCx = centerX
            self.__movingCy = centerY
            self.__movingFlag = True
            return True
        return False

    def MovingFinish(self, frameSeq=-1):
        """
        Finsih the the moving control panel. Just Up the contact.
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        LOG.debug('MovingFinish')
        if self.__movingFlag:
            ret = self.Up(contact=self.__movingContact, frameSeq=frameSeq)
            if ret:
                self.__movingFlag = False
                return True
        return False

    def Moving(self, dirAngle, frameSeq=-1, durationMS=50):
        """
        Move the contact in MovingInit() to the dirAngle point which is computed by center
        point, radius and dirAngle(0:forward, 90:right, 180:backward, 270:left).
        :param dirAngle: the angle([0, 360)) of moving direction
        :param frameSeq: the frame sequence, default is -1
        :param durationMS: the duration time(ms) in this process
        :return:
        """
        LOG.debug('Moving {0}'.format(dirAngle))
        if not self.__movingFlag:
            return False

        if 0 <= dirAngle < 360:
            dx = self.__movingRadius * math.sin(math.radians(dirAngle))
            dy = self.__movingRadius * math.cos(math.radians(dirAngle))
        else:
            dx = 0
            dy = 0

        px = int(self.__movingCx + dx)
        py = int(self.__movingCy - dy)
        ret = self.SwipeMove(px, py, contact=self.__movingContact, frameSeq=frameSeq,
                             durationMS=durationMS)
        if ret:
            return True
        return False

    def Move(self, px, py, contact=0, frameSeq=-1, waitTime=0):
        """
        Move the contact to the target point(px, py) immediately. No make up points in the process.
        :param px: x of target point
        :param py: y of target point
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={3} Move ({0}, {1}) contact={2}'
                  ' Wait {4}ms'.format(px, py, contact, frameSeq, waitTime))

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_MOVE, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = (px, py)
            return True
        return False

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
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, during_time=durationMS)
        actionData['img_id'] = frameSeq

        if durationMS < 0:
            LOG.debug('send frame data, frameIndex={3}'
                      ' Click ({0}, {1}) contact={2}'.format(px, py,
                                                             contact,
                                                             frameSeq))
        else:
            LOG.debug('send frame data, frameIndex={3}'
                      ' Click ({0}, {1}) {4}ms contact={2}'.format(px, py,
                                                                   contact,
                                                                   frameSeq,
                                                                   durationMS))
        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_CLICK, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = None
            return True
        return False

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
        actionData = self._SinglePointOp(px=px, py=py, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={3} Down ({0}, {1}) contact={2}'
                  ' Wait {4}ms'.format(px, py, contact, frameSeq, waitTime))

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_DOWN, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = (px, py)
            return True
        return False

    def Up(self, contact=0, frameSeq=-1, waitTime=0):
        """
        Up the contact.
        :param contact: contact index(0, 1, ..., 9)
        :param frameSeq: the frame sequence, default is -1
        :param waitTime: wait how long(ms) until next action
        :return:
        """
        actionData = self._SinglePointOp(px=0, py=0, contact=contact, wait_time=waitTime)
        actionData['img_id'] = frameSeq

        LOG.debug('send frame data, frameIndex={1} Up contact={0}'
                  ' Wait {2}ms'.format(contact, frameSeq, waitTime))

        ret = self.__actionMgr.SendAction(actionID=ACTION_ID_UP, actionData=actionData,
                                          frameSeq=frameSeq)
        if ret:
            self.__contactPoints[contact] = None
            return True
        return False

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
        if needUp:
            actionData = self._DoublePointOp(start_x=sx, start_y=sy, end_x=ex, end_y=ey,
                                             contact=contact,
                                             during_time=durationMS)
            actionData['img_id'] = frameSeq

            LOG.debug('send frame data, frameIndex={5}'
                      ' Swipe({0}, {1})->({2}, {3}) contact={4}'.format(sx, sy,
                                                                        ex, ey,
                                                                        contact,
                                                                        frameSeq))

            ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPE, actionData=actionData,
                                              frameSeq=frameSeq)
            if ret:
                self.__contactPoints[contact] = None
                return True
            return False
        else:
            actionData = self._DoublePointOp(start_x=sx, start_y=sy, end_x=ex, end_y=ey,
                                             contact=contact,
                                             during_time=durationMS)
            actionData['img_id'] = frameSeq

            LOG.debug('send frame data, frameIndex={5}'
                      ' SwipeDown({0}, {1})->({2}, {3}) contact={4}'.format(sx, sy,
                                                                            ex, ey,
                                                                            contact,
                                                                            frameSeq))

            ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPEDOWN, actionData=actionData,
                                              frameSeq=frameSeq)

            if ret:
                self.__contactPoints[contact] = (ex, ey)
                return True
            return False

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
        if self.__contactPoints[contact] is not None:
            actionData = self._SinglePointOp(px=px, py=py,
                                             contact=contact,
                                             during_time=durationMS)
            actionData['img_id'] = frameSeq

            LOG.debug('send frame data, frameIndex={3}'
                      ' SwipeMove({0}, {1})) contact={2}'.format(px, py,
                                                                 contact,
                                                                 frameSeq))

            ret = self.__actionMgr.SendAction(actionID=ACTION_ID_SWIPEMOVE, actionData=actionData,
                                              frameSeq=frameSeq)
            if ret:
                self.__contactPoints[contact] = (px, py)
                return True
            return False
        else:
            LOG.warning('SwipeMove needs previous Points on contact({})'.format(contact))
            return False

    @staticmethod
    def _SinglePointOp(px, py, contact, during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['px'] = int(px)
        msg_data['py'] = int(py)
        msg_data['contact'] = contact
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data

    @staticmethod
    def _DoublePointOp(start_x, start_y, end_x, end_y, contact,
                       during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['start_x'] = int(start_x)
        msg_data['start_y'] = int(start_y)
        msg_data['end_x'] = int(end_x)
        msg_data['end_y'] = int(end_y)
        msg_data['contact'] = contact
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data
