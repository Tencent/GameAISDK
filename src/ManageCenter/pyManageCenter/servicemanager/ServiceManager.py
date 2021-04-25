# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import subprocess

from common.Define import *
from actionstrategy.EmptyActionStrategy import EmptyActionStrategy

LOG = logging.getLogger('ManageCenter')


class ServiceContext(object):
    """
    ServiceContext data structure
    """
    def __init__(self, serviceType, addr):
        self.type = serviceType
        self.addr = addr
        self.status = TASK_STATUS_NONE


class ServiceManager(object):
    """
    ServiceManager, manage the agentai, GameReg and UI Services
    """
    def __init__(self, runType):
        self.__runType = runType

        self.__uiServiceContextDict = dict()
        self.__agentServiceContextDict = dict()
        self.__regServiceContextDict = dict()

        self.__uiActionStrategy = EmptyActionStrategy()
        self.__agentActionStrategy = EmptyActionStrategy()

        self.__isTaskReady = False
        self.__isServiceReady = False

    def Initialize(self):
        """
        Initialize this module
        :return: True
        """
        self.__uiActionStrategy.Initialize()
        self.__agentActionStrategy.Initialize()
        return True

    def Finish(self):
        """
        Finish this module
        :return:
        """
        self.__uiActionStrategy.Finish()
        self.__agentActionStrategy.Finish()

    def Reset(self):
        """
        Reset this module
        :return:
        """
        self.__uiServiceContextDict.clear()
        self.__agentServiceContextDict.clear()
        self.__regServiceContextDict.clear()

        self.__uiActionStrategy.Reset()
        self.__agentActionStrategy.Reset()

        self.__isTaskReady = False
        self.__isServiceReady = False

    def AddService(self, serviceType, addr):
        """
        Add some service into manage list
        :param serviceType: service type
        :param addr: service address
        :return: True or false
        """
        ret, _ = self.IsServiceAlreadyRegistered(addr)
        if ret:
            LOG.warning('Add Service addr[{0}] already registered!'.format(addr))
            return False
        else:
            if serviceType == SERVICE_TYPE_UI:
                LOG.info('Add UIRecogn Service addr[{0}]!'.format(addr))
                self.__uiServiceContextDict[addr] = ServiceContext(SERVICE_TYPE_UI, addr)
            elif serviceType == SERVICE_TYPE_AGENT:
                LOG.info('Add AgentAI Service addr[{0}]!'.format(addr))
                self.__agentServiceContextDict[addr] = ServiceContext(SERVICE_TYPE_AGENT, addr)
            elif serviceType == SERVICE_TYPE_REG:
                LOG.info('Add GameReg Service addr[{0}]!'.format(addr))
                self.__regServiceContextDict[addr] = ServiceContext(SERVICE_TYPE_REG, addr)

            self._CheckServiceReady()
            self._CheckTaskReady()
            return True

    def DelService(self, serviceType, addr):
        """
        Delete some service from manage list
        :param serviceType: service type
        :param addr: service address
        :return: True or false
        """
        ret, serviceType = self.IsServiceAlreadyRegistered(addr)
        if not ret:
            LOG.warning('Del Service addr[{0}] not registered!'.format(addr))
            return False
        else:
            if serviceType == SERVICE_TYPE_UI:
                self.__uiServiceContextDict.pop(addr)
            elif serviceType == SERVICE_TYPE_AGENT:
                self.__agentServiceContextDict.pop(addr)
            elif serviceType == SERVICE_TYPE_REG:
                self.__regServiceContextDict.pop(addr)

            self._CheckServiceReady()
            self._CheckTaskReady()
            return True

    def GetAllServiceAddr(self, serviceType):
        """
        Get addresses of all services in serviceType type
        :param serviceType: service type
        :return: a set of addresses
        """
        if serviceType == SERVICE_TYPE_UI:
            return set(self.__uiServiceContextDict.keys())
        elif serviceType == SERVICE_TYPE_AGENT:
            return set(self.__agentServiceContextDict.keys())
        elif serviceType == SERVICE_TYPE_REG:
            return set(self.__regServiceContextDict.keys())

    def ChangeServiceStatus(self, addr, status):
        """
        Change the specific addr service's status
        :param addr: the specific addr
        :param status: service's new status
        :return: True or false
        """
        ret, serviceType = self.IsServiceAlreadyRegistered(addr)
        if not ret:
            LOG.warning('Change Service addr[{0}] not registered!'.format(addr))
            return False
        else:
            if serviceType == SERVICE_TYPE_UI:
                self.__uiServiceContextDict[addr].status = status
            elif serviceType == SERVICE_TYPE_AGENT:
                self.__agentServiceContextDict[addr].status = status
            elif serviceType == SERVICE_TYPE_REG:
                self.__regServiceContextDict[addr].status = status

            self._CheckTaskReady()
            return True

    def IsServiceReady(self):
        """
        Check whether all services are ready
        :return: True or false
        """
        return self.__isServiceReady

    def IsTaskReady(self):
        """
        Check whether all tasks are ready
        :return:
        """
        return self.__isTaskReady

    def PauseAgent(self):
        """
        Pause agentai process via signal SIGUSR1
        :return:
        """
        LOG.info('Pause Agent')
        return subprocess.call(['pkill', '-SIGUSR1', '-f', 'agentai.py'])

    def RestoreAgent(self):
        """
        Restore agentai process via signal SIGUSR2
        :return:
        """
        LOG.info('Restore Agent')
        return subprocess.call(['pkill', '-SIGUSR2', '-f', 'agentai.py'])

    def RestartService(self):
        """
        Restart agentai, GameReg or UI process
        :return: True or false
        """
        self.Reset()
        if self.__runType == RUN_TYPE_UI_AI:
            LOG.info('Restart UI+AI Service')
            return subprocess.call(['./restart_service.sh', 'UI+AI'])
        elif self.__runType == RUN_TYPE_AI:
            LOG.info('Restart AI Service')
            return subprocess.call(['./restart_service.sh', 'AI'])
        elif self.__runType == RUN_TYPE_UI:
            LOG.info('Restart UI Service')
            return subprocess.call(['./restart_service.sh', 'UI'])
        else:
            LOG.error('Invalid run type [{}]'.format(self.__runType))
            return False

    def _CheckServiceReady(self):
        if self.__runType == RUN_TYPE_UI_AI:
            self.__isServiceReady = len(self.__uiServiceContextDict) > 0 \
                                    and len(self.__agentServiceContextDict) > 0 \
                                    and len(self.__regServiceContextDict) > 0
        elif self.__runType == RUN_TYPE_AI:
            self.__isServiceReady = len(self.__agentServiceContextDict) > 0 \
                                    and len(self.__regServiceContextDict) > 0
        elif self.__runType == RUN_TYPE_UI:
            self.__isServiceReady = len(self.__uiServiceContextDict) > 0

        if not self.__isServiceReady:
            LOG.info('Services not ready! '
                     'U({})A({})R({})'.format(len(self.__uiServiceContextDict),
                                              len(self.__agentServiceContextDict),
                                              len(self.__regServiceContextDict)))
        else:
            LOG.info('All Services ready! '
                     'U({})A({})R({})'.format(len(self.__uiServiceContextDict),
                                              len(self.__agentServiceContextDict),
                                              len(self.__regServiceContextDict)))

    def _CheckTaskReady(self):
        if not self.__isServiceReady:
            self.__isTaskReady = False
            return

        for addr in self.__uiServiceContextDict:
            if self.__uiServiceContextDict[addr].status != TASK_STATUS_INIT_SUCCESS:
                LOG.info('UI Service[{0}] task status not ready!'.format(addr))
                self.__isTaskReady = False
                return

        for addr in self.__agentServiceContextDict:
            if self.__agentServiceContextDict[addr].status != TASK_STATUS_INIT_SUCCESS:
                LOG.info('AI Service[{0}] task status not ready!'.format(addr))
                self.__isTaskReady = False
                return

        for addr in self.__regServiceContextDict:
            if self.__regServiceContextDict[addr].status != TASK_STATUS_INIT_SUCCESS:
                LOG.info('Reg Service[{0}] task status not ready!'.format(addr))
                self.__isTaskReady = False
                return

        self.__isTaskReady = True
        return

    def IsServiceAlreadyRegistered(self, addr, serviceType=None):
        """
        Check whether a specific addr already registered
        :param addr: the specific addr
        :param serviceType: the specific addr's service type, optional
        :return: (True of False, serviceType)
        """
        ret = (False, None)

        if serviceType is not None:
            if serviceType == SERVICE_TYPE_UI:
                if addr in self.__uiServiceContextDict.keys():
                    ret = (True, serviceType)
            elif serviceType == SERVICE_TYPE_AGENT:
                if addr in self.__agentServiceContextDict.keys():
                    ret = (True, serviceType)
            elif serviceType == SERVICE_TYPE_REG:
                if addr in self.__regServiceContextDict.keys():
                    ret = (True, serviceType)
            else:
                LOG.debug('Service addr[{0}] not registerd!'.format(addr))
                ret = (False, serviceType)
        else:
            if addr in self.__uiServiceContextDict.keys():
                ret = (True, SERVICE_TYPE_UI)
            elif addr in self.__agentServiceContextDict.keys():
                ret = (True, SERVICE_TYPE_AGENT)
            elif addr in self.__regServiceContextDict.keys():
                ret = (True, SERVICE_TYPE_REG)
            else:
                LOG.debug('Service addr[{0}] not registerd!'.format(addr))

        return ret

    def PerformUIActionStrategy(self, addr, action):
        """
        Perform UI Action Strategy on UI action
        :param addr: the addr of the UI service
        :param action: UI action
        :return: UI action after strategy
        """
        return self.__uiActionStrategy.Perform(action)

    def PerformAIActionStrategy(self, addr, action):
        """
        Perform AI Action Strategy on AI action
        :param addr: the addr of the AI service
        :param action: AI action
        :return: AI action after strategy
        """
        return self.__agentActionStrategy.Perform(action)
