# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

import msgpack
import zmq

from common.CommonContext import IO_SERVICE_CONTEXT

LOG = logging.getLogger('IOService')


class ZMQSocket(object):
    """
    Socket implementation based on ZMQ
    """
    def __init__(self, port, pattern, ip='*', sendLastMsg=False):
        self.__context = zmq.Context()
        self.__zmqSocket = self.__context.socket(pattern)
        if sendLastMsg:
            self.__zmqSocket.setsockopt(zmq.CONFLATE, 1)
        self.__port = port
        self.__ip = ip

    def Initialize(self, isServer=True):
        """
        Initialize this socket
        :param isServer: wheter run as a Server
        :return: True or false
        """
        try:
            if isServer:
                addr = 'tcp://%s:%d' % (self.__ip, self.__port)
                LOG.info('ZMQSocket bind [{0}]'.format(addr))
                self.__zmqSocket.bind(addr)
            else:
                self.__zmqSocket.setsockopt(zmq.IDENTITY,
                                            msgpack.packb(IO_SERVICE_CONTEXT['source_server_id'],
                                                          encoding='utf-8'))
                addr = 'tcp://%s:%d' % (self.__ip, self.__port)
                LOG.info('ZMQSocket connect [{0}]'.format(addr))
                self.__zmqSocket.connect(addr)
            return True
        except Exception as e:
            LOG.error('ZMQ Error [{0}]'.format(e))
            return False

    def Recv(self):
        """
        Recv data on this socket
        :return: the received data
        """
        try:
            data = self.__zmqSocket.recv()
        except Exception as err:
            LOG.error('Recv data exception in zmq:{}'.format(err))
            return None

        if data is None:
            LOG.error('Recv data is None in zmq')
        return data

    def Send(self, data=None):
        """
        Send data on this socket
        :param data: the data to be sent
        :return: True or false
        """
        if data is None:
            LOG.error('Send data is None')
            return False
        try:
            self.__zmqSocket.send(data)
        except Exception as err:
            LOG.error('Send data exception in zmq:{}'.format(err))
            return False

        return True

    def Finish(self):
        """
        Finish this socket
        :return:
        """
        self.__zmqSocket.close()
