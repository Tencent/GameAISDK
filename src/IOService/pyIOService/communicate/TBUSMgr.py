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

LOG = logging.getLogger('IOService')


class TBUSMgr(object):
    """
    tbus Communication implement class
    """
    def __init__(self):
        self.__selfAddr = None
        self.__MCAddr = None

    def Initialize(self, cfgFile):
        """
        Initialize this module, read the conifg from cfgFile and call tbus.Init
        """
        tbusArgs = self._LoadTbusConfig(cfgFile)

        self.__selfAddr = tbus.GetAddress(tbusArgs['IOServiceAddr'])
        self.__MCAddr = tbus.GetAddress(tbusArgs['MCAddr'])

        # if any address is None, then error
        if None in [self.__selfAddr, self.__MCAddr]:
            LOG.error('TBus get address failed')
            return False

        ret = tbus.Init(self.__selfAddr, cfgFile)
        if ret != 0:
            LOG.error('TBus Init failed with return code[{0}]'.format(ret))
            return False
        return True

    def SendToMC(self, buff):
        """
        Send the buff to MC
        """
        ret = tbus.SendTo(self.__MCAddr, buff)
        if ret != 0:
            LOG.debug('TBus Send To MC return code[{0}]'.format(ret))
            return False
        return True

    def RecvMsg(self):
        """
        Recv Msgs from MC
        """
        msgBuffList = []

        msgBuff = tbus.RecvFrom(self.__MCAddr)
        while msgBuff is not None:
            msgBuffList.append(msgBuff)
            # LOG.debug('Recv {0} bytes from MC'.format(len(msgBuff)))
            msgBuff = tbus.RecvFrom(self.__MCAddr)

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
        else:
            LOG.error('Tbus Config File not exist in {0}'.format(cfgPath))

        return tbusArgs
