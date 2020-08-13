# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import configparser
import logging
import os
import time

import cv2

from common.Define import *
from common.CommonContext import IO_SERVICE_CONTEXT
from communicate.HTTPClient import HTTPClient
from communicate.SocketServer import SocketServer
from communicate.HttpServer import HttpServer
from communicate.TBUSMgr import TBUSMgr
from msghandler.MsgHandler import MsgHandler
from tools.ImgDecode import ImgDecode

MAIN_LOOP_RATE = 60
MAIN_LOOP_SLEEP_TIME = 1. / MAIN_LOOP_RATE
OTHERS_LOOP_RATE = 1
OTHERS_LOOP_COUNT = int(MAIN_LOOP_RATE / OTHERS_LOOP_RATE)

DEFAULT_TBUS_CFG_PATH = '../cfg/platform/bus.ini'

LOG = logging.getLogger('IOService')


class IOService(object):
    """
    IOService Main class
    """
    def __init__(self, taskCfgPath, platformCfgPath):
        self.__exited = False
        self.__loopCount = 0
        self.__debugShowFrame = False
        self.__debugTestMode = False

        self.__taskCfgPath = taskCfgPath
        self.__platformCfgPath = platformCfgPath

        self.__clientCfg = {}
        self.__controlCfg = {}

        self.__clientSocket = None
        self.__controlSocket = None
        self.__commMgr = None
        self.__msgHandler = None

        self.__lastFrameSeq = 0

    def Initialize(self):
        """
        Initialize this module
        :return: True or false
        """
        # Load config file
        ret = self._LoadConfig()
        if not ret:
            LOG.error('Load Config failed!')
            return False

        IO_SERVICE_CONTEXT['test_mode'] = self.__debugTestMode

        # Construct sub modules
        self.__clientSocket = SocketServer()
        self.__httpServer = HttpServer()
        self.__controlSocket = HTTPClient()
        self.__commMgr = TBUSMgr()
        self.__msgHandler = MsgHandler(self.__commMgr,
                                       self.__clientSocket,
                                       self.__httpServer,
                                       self.__controlSocket)

        # Initialize sub modules
        if not self.__commMgr.Initialize(DEFAULT_TBUS_CFG_PATH):
            LOG.error('TBUSMgr Initialize failed.')
            return False

        if IO_SERVICE_CONTEXT['io_service_type'] == 'HTTP':
            if not self.__httpServer.Initialize(self.__clientCfg):
                LOG.error('Http Server Initialize failed!')
                return False
        else:
            if not self.__clientSocket.Initialize(self.__clientCfg):
                LOG.error('Client Socket Initialize failed!')
                return False

        if not self.__controlSocket.Initialize(self.__controlCfg):
            LOG.error('Control Socket Initialize failed!')
            return False

        if not self.__msgHandler.Initialize():
            LOG.error('MsgHandler Initialize failed!')
            return False

        return True

    def Run(self):
        """
        Run this module
        :return:
        """
        while not self.__exited:
            beginTime = time.time()
            self._UpdateMsgHandler()  # Update Message handler
            updateMsgHandlerTime = time.time()
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
                msgHandlerMS = int(1000 * (updateMsgHandlerTime - beginTime))
                frameMS = int(1000 * (updateFrameTime - updateMsgHandlerTime))
                othersMS = int(1000 * (endTime - updateFrameTime))
                LOG.warning('MainLoop overschedule {0}ms: {1}={2}+{3}+{4}'.format(overMS, totalMS,
                                                                                  msgHandlerMS,
                                                                                  frameMS,
                                                                                  othersMS))
            self.__loopCount += 1

        self.__msgHandler.SendUnregisterToAIControl()

        LOG.info('Exit mainloop!')

    def Finish(self):
        """
        Finish this module
        :return:
        """
        self.__commMgr.Finish()
        self.__clientSocket.Finish()
        self.__httpServer.Finish()
        self.__controlSocket.Finish()

    def SetExited(self):
        """
        This module will exit when called
        :return:
        """
        self.__exited = True

    def _UpdateMsgHandler(self):
        self.__msgHandler.Update()

    def _UpdateFrame(self):
        if IO_SERVICE_CONTEXT['task_state'] != TASK_STATUS_INIT_SUCCESS:
            return

        frameBuff = IO_SERVICE_CONTEXT['frame']
        if frameBuff is None:
            return

        frameType = IO_SERVICE_CONTEXT['frame_type']
        extend = IO_SERVICE_CONTEXT['extend']
        frame = ImgDecode(frameBuff, frameType)
        frameSeq = IO_SERVICE_CONTEXT['frame_seq']

        if frame is None:
            LOG.error('Decode image error, check the image encode.')
            return

        if self.__lastFrameSeq == frameSeq:
            return

        if self.__debugShowFrame:
            cv2.imshow('IO', frame)
            cv2.waitKey(1)

        self.__msgHandler.SendFrameMsgToMC(frameSeq, frame, extend)
        self.__lastFrameSeq = frameSeq

    def _UpdateOthers(self):
        if self.__loopCount % (OTHERS_LOOP_COUNT * 10) == 0:
            if IO_SERVICE_CONTEXT['task_id'] is None:
                self.__msgHandler.SendRegisterToAIControl()

    def _LoadConfig(self):
        if os.path.exists(self.__platformCfgPath):
            iniCfg = configparser.ConfigParser()
            iniCfg.read(self.__platformCfgPath)
        else:
            LOG.error('Config File not exist in {0}'.format(self.__platformCfgPath))
            return False

        try:
            self.__debugShowFrame = iniCfg.getboolean('DEBUG', 'ShowFrame', fallback=False)
            self.__debugTestMode = iniCfg.getboolean('DEBUG', 'TestMode', fallback=False)

            self.__clientCfg = dict()
            self.__clientCfg['send_port'] = iniCfg.getint('CLIENT_COMMUNICATION', 'SendPort')
            self.__clientCfg['send_pattern'] = iniCfg.getint('CLIENT_COMMUNICATION', 'SendPattern')
            self.__clientCfg['recv_port'] = iniCfg.getint('CLIENT_COMMUNICATION', 'RecvPort')
            self.__clientCfg['recv_pattern'] = iniCfg.getint('CLIENT_COMMUNICATION', 'RecvPattern')
            self.__clientCfg['send_last_action'] = iniCfg.getint('CLIENT_COMMUNICATION',
                                                                 'SendLastAction')

            self.__controlCfg = dict()
            evASMIP = os.getenv('ASM_IP')
            if evASMIP is None:
                self.__controlCfg['ip'] = iniCfg.get('CONTROL_COMMUNICATION', 'IP')
            else:
                self.__controlCfg['ip'] = evASMIP

            evASMPort = os.getenv('ASM_PORT')
            if evASMPort is None:
                self.__controlCfg['port'] = iniCfg.getint('CONTROL_COMMUNICATION', 'Port')
            else:
                self.__controlCfg['port'] = int(evASMPort)

            self.__controlCfg['STAFFNAME'] = iniCfg.get('CONTROL_COMMUNICATION', 'StaffName')
            self.__controlCfg['pattern'] = iniCfg.getint('CONTROL_COMMUNICATION', 'Pattern')
        except Exception as e:
            LOG.error('Load Config File[{}] failed, err: {}'.format(self.__platformCfgPath, e))
            return False

        return True
