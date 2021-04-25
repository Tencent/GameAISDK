# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import configparser
import logging
import os

import tbus
from util.config_path_mgr import SYS_CONFIG_DIR

from protocol import common_pb2

# BUS_CFG_FILE = '../cfg/platform/bus.ini'
TBUS_CFG_PATH = 'cfg/platform/bus.ini'

class BusConnect(object):
    """
    Tbus connect manage class module
    """

    PEER_NODE_MC = 1
    PEER_NODE_GAMEREG = 2
    PEER_NODE_SDKTOOL = 3

    __instance = None
    __init = False

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if not self.__init:
            self.__selfAddr = None
            self.__mcAddr = None
            self.__gameRegAddr = None
            self.__sdkToolAddr = None
            self.__connectOk = False
            self.__logger = logging.getLogger('agent')
            self.__init = True

    def Connect(self):
        """
        Create connection to all related channel
        """
        if self._LoadBusConnectCfg() is not True:
            return False

        if self.__connectOk is True:
            return True

        tbus_cfg_path = os.path.join(SYS_CONFIG_DIR, TBUS_CFG_PATH)
        ret = tbus.Init(self.__selfAddr, tbus_cfg_path)
        if ret != 0:
            self.__logger.error('Tbus init failed, err = {}'.format(ret))
            return False

        self.__connectOk = True

        return True

    def Close(self):
        """
        Close all connection
        """
        tbus.Exit(self.__selfAddr)
        self.__connectOk = False

    def RecvMsg(self, peerNode):
        """
        Recive and unserialize msg from MC channel
        """
        peerNodeAddr = self._GetPeerNodeAddr(peerNode)
        if peerNodeAddr is None:
            self.__logger.error('Recv error: peer node {} address is None!'.format(peerNode))
            return None

        self.__logger.debug("receive the message from the address:{}".format(peerNodeAddr))

        msgBuff = tbus.RecvFrom(peerNodeAddr)
        if msgBuff is not None:
            msg = common_pb2.tagMessage()
            msg.ParseFromString(msgBuff)
            #msg = msgpack.unpackb(msgBuff, encoding='utf-8')
            return msg

        return None

    def SendMsg(self, msg, peerNode):
        """
        Serialize and send a msg to MC channel
        """
        peerNodeAddr = self._GetPeerNodeAddr(peerNode)
        if peerNodeAddr is None:
            self.__logger.error('Seed error: peer node {} address is None!'.format(peerNode))
            return -1

        msgBuff = msg.SerializeToString()
        return tbus.SendTo(peerNodeAddr, msgBuff)

    def _GetPeerNodeAddr(self, peerNode):
        peerAddr = None

        if peerNode == self.PEER_NODE_MC:
            peerAddr = self.__mcAddr
        elif peerNode == self.PEER_NODE_GAMEREG:
            peerAddr = self.__gameRegAddr
        elif peerNode == self.PEER_NODE_SDKTOOL:
            peerAddr = self.__sdkToolAddr
        else:
            pass

        return peerAddr

    def _LoadBusConnectCfg(self):
        ret = True
        tbus_cfg_path = os.path.join(SYS_CONFIG_DIR, TBUS_CFG_PATH)
        if os.path.exists(tbus_cfg_path):
            config = configparser.ConfigParser(strict=False)
            config.read(tbus_cfg_path)

            selfAddrStr = config.get('BusConf', 'Agent1Addr')
            mcAddrStr = config.get('BusConf', 'MCAddr')
            gameRegAddrStr = config.get('BusConf', 'GameReg1Addr')
            sdkToolAddrStr = config.get('BusConf', 'SDKToolAddr')

            self.__selfAddr = tbus.GetAddress(selfAddrStr)
            self.__mcAddr = tbus.GetAddress(mcAddrStr)
            self.__gameRegAddr = tbus.GetAddress(gameRegAddrStr)
            self.__sdkToolAddr = tbus.GetAddress(sdkToolAddrStr)

            if self.__selfAddr is None or self.__mcAddr is None or self.__gameRegAddr is None:
                self.__logger.error('Wrong bus address!')
                ret = False
        else:
            self.__logger.error('Bus cfg file not exists!')
            ret = False

        return ret
