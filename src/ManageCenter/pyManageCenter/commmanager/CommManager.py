# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import configparser
import logging
import os

import tbus

from common.Define import *

LOG = logging.getLogger('ManageCenter')


class CommManager(object):
    """
    tbus Communication implement class
    """
    def __init__(self, runType):
        self.__runType = runType

        self.__selfAddr = None
        self.__Reg1Addr = None
        self.__Reg2Addr = None
        self.__UI1Addr = None
        self.__UI2Addr = None
        self.__Agent1Addr = None
        self.__Agent2Addr = None
        self.__IOAddr = None
        self.__recvAddrsSet = set()
        self.__recvAgentAddrsSet = set()

    def Initialize(self, configFile):
        """
        Initialize this module, read the conifg from cfgFile and call tbus.Init
        """
        tbusArgs = self._LoadTbusConfig(configFile)

        self.__selfAddr = tbus.GetAddress(tbusArgs['MCAddr'])
        self.__IOAddr = tbus.GetAddress(tbusArgs['IOServiceAddr'])
        self.__Reg1Addr = tbus.GetAddress(tbusArgs['GameReg1Addr'])
        self.__Reg2Addr = tbus.GetAddress(tbusArgs['GameReg1Addr'])
        self.__UI1Addr = tbus.GetAddress(tbusArgs['UI1Addr'])
        self.__UI2Addr = tbus.GetAddress(tbusArgs['UI2Addr'])
        self.__Agent1Addr = tbus.GetAddress(tbusArgs['Agent1Addr'])
        self.__Agent2Addr = tbus.GetAddress(tbusArgs['Agent2Addr'])

        # if any address is None, then error
        if None in [self.__selfAddr, self.__IOAddr,
                    self.__Reg1Addr, self.__Reg2Addr,
                    self.__UI1Addr, self.__UI2Addr,
                    self.__Agent1Addr, self.__Agent2Addr]:
            LOG.error('TBus get address failed')
            return False

        ret = tbus.Init(self.__selfAddr, configFile)
        if ret != 0:
            LOG.error('TBus Init failed with return code[{0}]'.format(ret))
            return False

        if self.__runType == RUN_TYPE_UI_AI:
            self.__recvAddrsSet = (self.__IOAddr, self.__Reg1Addr, self.__Reg2Addr,
                                   self.__UI1Addr, self.__UI2Addr)
            self.__recvAgentAddrsSet = (self.__Agent1Addr, self.__Agent2Addr)
        elif self.__runType == RUN_TYPE_AI:
            self.__recvAddrsSet = (self.__IOAddr, self.__Reg1Addr, self.__Reg2Addr)
            self.__recvAgentAddrsSet = (self.__Agent1Addr, self.__Agent2Addr)
        elif self.__runType == RUN_TYPE_UI:
            self.__recvAddrsSet = (self.__IOAddr, self.__UI1Addr, self.__UI2Addr)

        return True

    def SendTo(self, addr, buff):
        """
        Send the buff to addr
        """
        ret = tbus.SendTo(addr, buff)
        if ret != 0:
            LOG.debug('TBus Send To {0} return code[{1}]'.format(addr, ret))
            return False
        return True

    def SendMsgToIOService(self, buff):
        """
        Send the buff to IOService
        """
        ret = tbus.SendTo(self.__IOAddr, buff)
        if ret != 0:
            LOG.debug('TBus Send To IOService return code[{0}]'.format(ret))
            return False
        return True

    def RecvMsg(self):
        """
        Recv Msgs from all connected addrs
        """
        msgBuffList = []

        for addr in self.__recvAddrsSet:
            msgBuff = tbus.RecvFrom(addr)
            if msgBuff is not None:
                msgBuffList.append((addr, msgBuff))

        for addr in self.__recvAgentAddrsSet:
            msgBuff = tbus.RecvFrom(addr)
            while msgBuff is not None:
                msgBuffList.append((addr, msgBuff))
                msgBuff = tbus.RecvFrom(addr)

        return msgBuffList

    def Finish(self):
        """
        Finish this module
        """
        if self.__selfAddr:
            tbus.Exit(self.__selfAddr)

    def _LoadTbusConfig(self, cfgPath):
        tbusArgs = {}

        if os.path.exists(cfgPath):
            config = configparser.ConfigParser(strict=False)
            config.read(cfgPath)

            tbusArgs['IOServiceAddr'] = config.get('BusConf', 'IOServiceAddr')
            tbusArgs['MCAddr'] = config.get('BusConf', 'MCAddr')
            tbusArgs['GameReg1Addr'] = config.get('BusConf', 'GameReg1Addr')
            tbusArgs['GameReg2Addr'] = config.get('BusConf', 'GameReg2Addr')
            tbusArgs['UI1Addr'] = config.get('BusConf', 'UI1Addr')
            tbusArgs['UI2Addr'] = config.get('BusConf', 'UI2Addr')
            tbusArgs['Agent1Addr'] = config.get('BusConf', 'Agent1Addr')
            tbusArgs['Agent2Addr'] = config.get('BusConf', 'Agent2Addr')
        else:
            LOG.error('Tbus Config File not exist in {0}'.format(cfgPath))

        return tbusArgs
