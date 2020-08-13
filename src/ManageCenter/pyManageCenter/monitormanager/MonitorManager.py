# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import queue
import threading
import time

import psutil

from common.Define import *

LOG = logging.getLogger('IOService')


class MonitorManager(object):
    """
    Services Monitor Manager, used for check whether the agentai, GameReg or UIReg processes exited
    """
    def __init__(self, runType):
        self.__runType = runType
        self.__resultQueue = queue.Queue()

    def Initialize(self):
        """
        Initialize this module
        :return:
        """
        self.__monitorThread = MonitorThread(self.__resultQueue, self.__runType)
        self.__monitorThread.setDaemon(True)
        self.__monitorThread.start()
        return True

    def GetResult(self):
        """
        Get monitor results
        :return:
        """
        result = None
        while not self.__resultQueue.empty():
            result = self.__resultQueue.get_nowait()

        return result


class MonitorItemContext(object):
    """
    MonitorItemContext data structure
    """
    def __init__(self, name, keywords, serviceType):
        self.name = name
        self.keywords = keywords
        self.type = serviceType
        self.pid = None
        self.updated = False

    def __repr__(self):
        return '{} [{}] ({})'.format(self.name, self.keywords, self.pid)


class MonitorThread(threading.Thread):
    """
    Services Monitor Manager thread implementation
    """
    def __init__(self, resultQueue, runType):
        threading.Thread.__init__(self)
        self.__resultQueue = resultQueue

        self.__procList = []

        if runType == RUN_TYPE_AI:
            self.__procList.append(MonitorItemContext('GameReg', None, SERVICE_TYPE_REG))
            self.__procList.append(MonitorItemContext('python', 'agentai.py', SERVICE_TYPE_AGENT))
        elif runType == RUN_TYPE_UI_AI:
            self.__procList.append(MonitorItemContext('UIRecognize', None, SERVICE_TYPE_UI))
            self.__procList.append(MonitorItemContext('python', 'agentai.py', SERVICE_TYPE_AGENT))
            self.__procList.append(MonitorItemContext('GameReg', None, SERVICE_TYPE_REG))
        elif runType == RUN_TYPE_UI:
            self.__procList.append(MonitorItemContext('UIRecognize', None, SERVICE_TYPE_UI))

    def run(self):
        while True:
            for proc in psutil.process_iter():
                try:
                    procName = proc.name()
                    cmdLine = proc.cmdline()
                    pid = proc.pid
                except Exception:
                    continue

                for serviceProc in self.__procList:
                    if serviceProc.name not in procName:
                        continue

                    if serviceProc.keywords is not None:
                        if serviceProc.keywords in cmdLine:
                            serviceProc.pid = pid
                            serviceProc.updated = True
                    else:
                        serviceProc.pid = pid
                        serviceProc.updated = True

            result = ALL_NORMAL
            for serviceProc in self.__procList:
                if not serviceProc.updated:
                    if serviceProc.type == SERVICE_TYPE_AGENT:
                        result |= AGENT_EXIT
                    elif serviceProc.type == SERVICE_TYPE_UI:
                        result |= UI_EXIT
                    elif serviceProc.type == SERVICE_TYPE_REG:
                        result |= REG_EXIT
                else:
                    serviceProc.updated = False

            self.__resultQueue.put_nowait(result)
            time.sleep(1)
