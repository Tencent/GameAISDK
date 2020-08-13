# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import time
import logging
import tbus
import configparser
from protocol import common_pb2
#import msgpack

BUS_CFG_FILE = '/cfg/bus.ini'

class BusConnect(object):

    __connectOk = False

    def __init__(self):
        self.__selfAddr = None
        self.__mcAddr = None
        self.__logger = logging.getLogger('agent')

    def Connect(self):
        if self._LoadBusConnectCfg() is not True:
            return False

        if self.__connectOk is True:
            return True

        ret = tbus.Init(self.__selfAddr, BUS_CFG_FILE)
        if ret != 0:
            self.__logger.error('Tbus init failed, err = {}'.format(ret))
            return False

        self.__connectOk = True

        return True

    def Close(self):
        tbus.Exit(self.__selfAddr)

    def RecvMsg(self):
        msgBuff = tbus.RecvFrom(self.__mcAddr)
        if msgBuff is not None:
            msg = common_pb2.tagMessage()
            msg.ParseFromString(msgBuff)
            #msg = msgpack.unpackb(msgBuff, encoding='utf-8')
            return msg

        return None

    def SendMsg(self, msg):
        #msgBuff = msgpack.packb(msg)
        msgBuff = msg.SerializeToString()
        return tbus.SendTo(self.__mcAddr, msgBuff)

    def _LoadBusConnectCfg(self):
        ret = True

        if os.path.exists(BUS_CFG_FILE):
            config = configparser.ConfigParser(strict=False)
            config.read(BUS_CFG_FILE)

            selfAddrStr = config.get('BusConf', 'Agent1Addr')
            mcAddrStr = config.get('BusConf', 'MCAddr')

            self.__selfAddr = tbus.GetAddress(selfAddrStr)
            self.__mcAddr = tbus.GetAddress(mcAddrStr)

            if self.__selfAddr is None or self.__mcAddr is None:
                self.__logger.error('Wrong bus address!')
                ret = False
        else:
            self.__logger.error('Bus cfg file not exists!')
            ret = False

        return ret