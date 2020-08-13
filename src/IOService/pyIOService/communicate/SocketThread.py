# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import threading
import time

import msgpack
import msgpack_numpy as mn

LOG = logging.getLogger('IOService')


class RecvThread(threading.Thread):
    """
    Recv Thread implementation
    """
    def __init__(self, recvSocket, recvQueue):
        threading.Thread.__init__(self)
        self.__recvSocket = recvSocket
        self.__recvQueue = recvQueue
        self.__runningFlag = threading.Event()
        self.__runningFlag.set()

    def run(self):
        while self.__runningFlag.isSet():
            buff = self.__recvSocket.Recv()
            if buff is None or len(buff) == 0:
                LOG.error('Recv buff is None')
                time.sleep(0.001)
                continue

            data = msgpack.unpackb(buff, object_hook=mn.decode, encoding='utf-8')
            self.__recvQueue.put_nowait(data)
            time.sleep(0.001)

    def finish(self):
        """
        Finish this thread
        :return:
        """
        self.__runningFlag.clear()


class SendThread(threading.Thread):
    """
    Send Thread implementation
    """
    def __init__(self, sendSocket, sendQueue):
        threading.Thread.__init__(self)
        self.__sendSocket = sendSocket
        self.__sendQueue = sendQueue
        self.__runningFlag = threading.Event()
        self.__runningFlag.set()

    def run(self):
        while self.__runningFlag.isSet():
            if not self.__sendQueue.empty():
                data = self.__sendQueue.get_nowait()
                if data is not None:
                    if not isinstance(data, bytes):
                        buff = msgpack.packb(data, default=mn.encode, use_bin_type=True)
                    else:
                        buff = data
                    self.__sendSocket.Send(buff)
                    time.sleep(0.001)
                    continue
                LOG.error('Send data is None')

            time.sleep(0.001)
            continue

    def finish(self):
        """
        Finish this thread
        :return:
        """
        self.__runningFlag.clear()
