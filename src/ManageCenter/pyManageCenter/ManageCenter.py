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
import time
import cv2

from common.Define import RUN_TYPE_UI_AI, RESULT_TYPE_AI, SERVICE_UNREGISTER, SERVICE_TYPE_REG, SERVICE_TYPE_UI, \
    ALL_NORMAL, AGENT_EXIT, UI_EXIT, REG_EXIT, RESULT_TYPE_UI, RUN_TYPE_AI, RUN_TYPE_UI
from commmanager.CommManager import CommManager
from msghandler.MsgHandler import MsgHandler
from gamemanager.GameManager import GameManager
from gamemanager.ResultManager import ResultManager
from servicemanager.ServiceManager import ServiceManager
from monitormanager.MonitorManager import MonitorManager
from util.config_path_mgr import SYS_CONFIG_DIR, DEFAULT_USER_CONFIG_DIR

MAIN_LOOP_RATE = 60
MAIN_LOOP_SLEEP_TIME = 1. / MAIN_LOOP_RATE
OTHERS_LOOP_RATE = 1
OTHERS_LOOP_COUNT = int(MAIN_LOOP_RATE / OTHERS_LOOP_RATE)

TBUS_CFG_PATH = 'cfg/platform/bus.ini'

LOG = logging.getLogger('ManageCenter')


class ManageCenter(object):
    """
    ManageCenter Main class
    """
    def __init__(self, taskCfgPath, platformCfgPath):
        self.__exited = False
        self.__loopCount = 0
        self.__debugShowFrame = False
        self.__initTimestamp = time.time()

        self.__taskCfgPath = taskCfgPath
        self.__platformCfgPath = platformCfgPath

        self.__runType = RUN_TYPE_UI_AI
        self.__resultType = RESULT_TYPE_AI

        self.__commMgr = None
        self.__gameMgr = None
        self.__resultMgr = None
        self.__msgHandler = None
        self.__serviceMgr = None
        self.__monitorMgr = None
        self.__lastFrameSeq = 0
        self.__lastMonitorResult = None

        self.__resultPath = None
        self.__resultCfg = None
        self.__taskID = time.strftime("%Y%m%d_%H%M%S")

    def Initialize(self, runType='AI'):
        """
        Initialize this module
        :param runType: run type enum: UI+AI or AI or UI
        :return: True or false
        """
        # Load config file
        ret = self._LoadConfig(runType)
        if not ret:
            LOG.error('Load Config failed!')
            return False

        # Construct sub modules
        self.__commMgr = CommManager(self.__runType)
        self.__serviceMgr = ServiceManager(self.__runType)
        self.__gameMgr = GameManager()
        self.__resultMgr = ResultManager()
        self.__msgHandler = MsgHandler(self.__commMgr, self.__gameMgr, self.__serviceMgr,
                                       self.__resultMgr, self.__resultType, self.__runType)
        self.__monitorMgr = MonitorManager(self.__runType)

        # Initialize sub modules
        if not self.__serviceMgr.Initialize():
            LOG.error('ServiceManager Initialize failed!')
            return False

        tbus_cfg_path = os.path.join(SYS_CONFIG_DIR, TBUS_CFG_PATH)
        if not self.__commMgr.Initialize(tbus_cfg_path):
            LOG.error('CommMgr Initialize failed!')
            return False

        if not self.__msgHandler.Initialize() or not self.__monitorMgr.Initialize():
            LOG.error('MsgHandler Initialize failed! or MonitorManager Initialize failed!')
            return False

        if not self.__resultMgr.Initialize(taskID=self.__taskID,
                                           resultOutputPath=self.__resultPath,
                                           context=self.__resultCfg):
            LOG.error('ResultManager Initialize failed!')
            return False

        self.__initTimestamp = time.time()
        return True

    def Run(self):
        """
        Loop run funtion
        :return:
        """
        while not self.__exited:
            beginTime = time.time()
            self._UpdateMsgHandler()  # Update Message handler
            updateMsgTime = time.time()
            self._UpdateFrame()  # Update frame
            updateFrameTime = time.time()
            self._UpdateOthers()
            endTime = time.time()
            sleepTime = MAIN_LOOP_SLEEP_TIME - (endTime - beginTime)
            if sleepTime > 0:
                time.sleep(sleepTime)
            elif endTime - beginTime > 0.05:
                overMS = int(-1000 * sleepTime)
                totalMS = int(1000 * MAIN_LOOP_SLEEP_TIME) + overMS
                msgMS = int(1000 * (updateMsgTime - beginTime))
                frameMS = int(1000 * (updateFrameTime - updateMsgTime))
                othersMS = int(1000 * (endTime - updateFrameTime))
                LOG.warning('MainLoop overschedule %sms: %s=%s+%s+%s', overMS, totalMS, msgMS, frameMS, othersMS)
            self.__loopCount += 1

        self.__msgHandler.SendServiceRegisterMsgToIO(SERVICE_UNREGISTER)

        LOG.info('Exit mainloop!')

    def Finish(self):
        """
        Finish this module
        :return:
        """
        self.__resultMgr.Finish()
        self.__commMgr.Finish()
        self.__serviceMgr.Finish()

    def SetExited(self):
        """
        This module will exit when called
        :return:
        """
        self.__exited = True

    def _UpdateMsgHandler(self):
        self.__msgHandler.Update()

    def _UpdateFrame(self):
        if not self.__serviceMgr.IsTaskReady():
            return

        frame = self.__gameMgr.GetGameFrame()
        if frame is None:
            return

        frameSeq = self.__gameMgr.GetFrameSeq()
        if self.__lastFrameSeq == frameSeq:
            return

        data = self.__gameMgr.GetGameData()

        if self.__debugShowFrame:
            cv2.imshow('MC', frame)
            cv2.waitKey(1)

        if self.__gameMgr.GameStarted():
            addrList = self.__serviceMgr.GetAllServiceAddr(serviceType=SERVICE_TYPE_REG)
            for addr in addrList:
                self.__msgHandler.SendGameFrameMsgTo(addr=addr, gameFrame=frame, gameData=data,
                                                     frameSeq=frameSeq)

        addrList = self.__serviceMgr.GetAllServiceAddr(serviceType=SERVICE_TYPE_UI)
        for addr in addrList:
            self.__msgHandler.SendUIAPIStateMsgTo(addr=addr, gameFrame=frame, frameSeq=frameSeq)

        self.__lastFrameSeq = frameSeq

    def _UpdateOthers(self):
        now = time.time()
        if now - self.__initTimestamp < 30:
            return

        if self.__loopCount % OTHERS_LOOP_COUNT == 0:
            self._UpdateMonitor()

    def _UpdateMonitor(self):
        result = self.__monitorMgr.GetResult()

        if result is None:
            return

        if self.__lastMonitorResult == result:
            return

        if result == ALL_NORMAL:
            LOG.info('All services process is running!')
        else:
            if result & AGENT_EXIT:
                LOG.warning('Agent service process exit!')
            if result & UI_EXIT:
                LOG.warning('UI service process exit!')
            if result & REG_EXIT:
                LOG.warning('Reg service process exit!')

        self.__msgHandler.SendAIServiceStateToIO(result)
        self.__lastMonitorResult = result

    def _LoadConfig(self, runType):
        if runType == 'UI+AI':
            self.__runType = RUN_TYPE_UI_AI
            self.__resultType = RESULT_TYPE_UI
        elif runType == 'AI':
            self.__runType = RUN_TYPE_AI
            self.__resultType = RESULT_TYPE_AI
        elif runType == 'UI':
            self.__runType = RUN_TYPE_UI
            self.__resultType = RESULT_TYPE_UI
        else:
            LOG.error('Invalid RunType %s', runType)
            return False

        LOG.info('RunType is %s', self.__runType)

        if not self._LoadPlatformConfig():
            return False

        self._LoadTaskConfig()

        self.__resultPath = os.path.join(os.getenv('AI_SDK_PROJECT_PATH',
                                                   os.path.join(DEFAULT_USER_CONFIG_DIR)), 'result')
        return True

    def _LoadPlatformConfig(self):
        if os.path.exists(self.__platformCfgPath):
            iniCfg = configparser.ConfigParser()
            iniCfg.read(self.__platformCfgPath)
        else:
            LOG.error('Config File not exist in %s', self.__platformCfgPath)
            return False

        try:
            self.__debugShowFrame = iniCfg.getboolean('DEBUG', 'ShowFrame', fallback=False)

            self.__resultCfg = dict()
            self.__resultCfg['enable'] = iniCfg.getboolean('RESULT', 'Enable', fallback=False)
            self.__resultCfg['fps'] = iniCfg.getint('RESULT', 'FPS', fallback=10)
            self.__resultCfg['result_url'] = iniCfg.get('RESULT', 'ResultURL')
            self.__resultCfg['state_url'] = iniCfg.get('RESULT', 'StateURL')
            self.__resultCfg['token'] = iniCfg.get('RESULT', 'Token')
            self.__resultCfg['api_user'] = iniCfg.get('RESULT', 'APIUser', fallback='ai_sdk')
            self.__resultCfg['rtx_user'] = iniCfg.get('RESULT', 'RTXUser', fallback='ai_sdk')
            self.__resultCfg['timeout'] = iniCfg.getint('RESULT', 'Timeout', fallback=3600)

            self.__resultType = iniCfg.get('RESULT', 'Type', fallback=self.__resultType)
        except KeyError as e:
            LOG.error('Load Config File[%s] failed, err: %s', self.__platformCfgPath, e)
            return False
        return True

    def _LoadTaskConfig(self):
        if os.path.exists(self.__taskCfgPath):
            pass
            # with open(self.__taskCfgPath) as fd:
            #     taskCfg = json.load(fd)
        else:
            # LOG.error('Config File not exist in {0}'.format(self.__taskCfgPath))
            return False

        return True
