# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import configparser
import json
import logging
import os

import msgpack
import msgpack_numpy as mn

from protocol import common_pb2
from connect.BusConnect import BusConnect

MSG_ID_AI_ACTION = 2000

LOG = logging.getLogger('agent')
LOG_REGACTION = logging.getLogger('regaction')

class ActionMgr(object):
    """
    ActionMgr implement for remote action
    """
    def __init__(self):
        self.__initialized = False
        self.__connect = BusConnect()

    def Initialize(self):
        """
        Initialize this module, init bus connection
        :return:
        """
        self.__initialized = True
        return self.__connect.Connect()

    def Finish(self):
        """
        Finish this module, tbus disconnect
        :return:
        """
        if self.__initialized:
            LOG.info('Close connection...')
            self.__connect.Close()
            self.__initialized = False

    def SendAction(self, actionID, actionData, frameSeq=-1):
        """
        Send action to remote(client)
        :param actionID: the self-defined action ID
        :param actionData: the context data of the action ID
        :param frameSeq: the frame sequence, default is -1
        :return:
        """
        if not self.__initialized:
            LOG.warning('Call Initialize first!')
            return False

        actionData['msg_id'] = MSG_ID_AI_ACTION
        actionData['action_id'] = actionID
        actionBuff = msgpack.packb(actionData, default=mn.encode, use_bin_type=True)

        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_AI_ACTION
        msg.stAIAction.nFrameSeq = frameSeq
        msg.stAIAction.byAIActionBuff = actionBuff
        #msgBuff = msg.SerializeToString()

        if LOG_REGACTION.level <= logging.DEBUG:
            actionStr = json.dumps(actionData)
            LOG_REGACTION.debug('{}||action||{}'.format(frameSeq, actionStr))

        ret = self.__connect.SendMsg(msg)
        if ret != 0:
            LOG.warning('TBus Send To MC return code[{0}]'.format(ret))
            return False
        return True
