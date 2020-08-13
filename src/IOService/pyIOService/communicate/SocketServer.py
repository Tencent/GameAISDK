# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import queue

from communicate.SocketThread import RecvThread
from communicate.SocketThread import SendThread
from communicate.ZMQSocket import ZMQSocket

LOG = logging.getLogger('IOService')


class SocketServer(object):
    """
    Socket Server implement for communication with AIClient
    """
    def __init__(self):
        self.__recvSocket = None
        self.__sendSocket = None
        self.__recvthread = None
        self.__sendthread = None
        self.__sendQueue = queue.Queue()
        self.__recvQueue = queue.Queue()

        self.__sendPort = None
        self.__sendPattern = None
        self.__recvPort = None
        self.__recvPattern = None
        self.__sendOnlyLastMsg = None

    def Initialize(self, cfg):
        """
        Initialize this module, load config from cfg
        :param cfg:
        :return: True or false
        """
        self.__sendPort = cfg['send_port']
        self.__sendPattern = cfg['send_pattern']
        self.__recvPort = cfg['recv_port']
        self.__recvPattern = cfg['recv_pattern']
        self.__sendOnlyLastMsg = cfg['send_last_action']

        return self._CreateSocket()

    def Finish(self):
        """
        Finish this module
        :return:
        """
        if self.__recvthread is not None:
            self.__recvthread.finish()

        if self.__sendthread is not None:
            self.__sendthread.finish()

    def Send(self, msgBuff):
        """
        Send the msgBuff to HTTP Server
        :param msgBuff: the msg buff to be sent
        :return:
        """
        self.__sendQueue.put_nowait(msgBuff)

    def Recv(self):
        """
        Receive the msg from HTTP Server
        :return: A list contains the msgs received
        """
        msgBuffList = []
        while not self.__recvQueue.empty():
            msgBuff = self.__recvQueue.get_nowait()
            msgBuffList.append(msgBuff)

        return msgBuffList

    def _CreateSocket(self):
        self.__recvSocket = ZMQSocket(port=self.__recvPort, pattern=self.__recvPattern)
        self.__sendSocket = ZMQSocket(port=self.__sendPort, pattern=self.__sendPattern,
                                      sendLastMsg=self.__sendOnlyLastMsg)

        if not self.__recvSocket.Initialize():
            LOG.error('SocketServer init recv socket failed!')
            return False

        if not self.__sendSocket.Initialize():
            LOG.error('SocketServer init send socket failed!')
            return False

        self.__recvthread = RecvThread(self.__recvSocket, self.__recvQueue)
        self.__sendthread = SendThread(self.__sendSocket, self.__sendQueue)
        self.__recvthread.setDaemon(True)
        self.__sendthread.setDaemon(True)
        self.__recvthread.start()
        self.__sendthread.start()
        LOG.info('Create SocketServer threads succeed')
        return True
