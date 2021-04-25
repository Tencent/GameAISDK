# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging
import os
import queue
import tarfile
import time
import threading
from urllib import request

import cv2
import msgpack
import msgpack_numpy as mn

from common.Define import *

LOG = logging.getLogger('ManageCenter')
LOG_RESULT = logging.getLogger('Result')

LOG_FILE_PATH = '../log'


class ResultManager(object):
    """
    ResultManager, manage the result generation, including game video and log
    """
    def __init__(self):
        self.__enable = False
        self.__frameQueue = queue.Queue(maxsize=100)
        self.__actionQueue = queue.Queue()
        self.__resultThread = ResultThread(self.__frameQueue, self.__actionQueue)

    def Initialize(self, taskID, resultOutputPath, context):
        """
        Initialize this module
        :param taskID: the taskID of this service from ASM
        :param resultOutputPath: the path to output directory for result
        :param context: other context data
        :return:
        """
        self.__resultThread.Initialize(taskID, resultOutputPath, context)
        self.__enable = context['enable']
        self.__resultThread.setDaemon(True)
        if self.__enable:
            self.__resultThread.start()
        return True

    def Finish(self):
        """
        Finish this module
        :return:
        """
        if self.__enable:
            self.__resultThread.Finish()
            self.__resultThread.join(5)

    def UpdateContext(self, testID=None, taskID=None, gameID=None, gameVersion=None):
        """
        Interface for update the context data
        :param testID: testID from aitest
        :param taskID: taskID from ASM
        :param gameID: gameID from aitest
        :param gameVersion: gameVersion from aitest
        :return:
        """
        return self.__resultThread.UpdateContext(testID, taskID, gameID, gameVersion)

    def SavingVideo(self, frame, frameSeq, AIFlag=False):
        """
        Save one frame into the video
        :param frame: GameFrame
        :param frameSeq: Frame Sequence
        :param AIFlag: Flag indicates whether in AI or UI
        :return:
        """
        if not self.__enable:
            return True

        try:
            self.__frameQueue.put_nowait((frame, frameSeq, AIFlag))
            return True
        except queue.Full:
            LOG.warning('Result saving video failed, frameQueue Full')
            return False

    def SavingActionLog(self, actionBuff, frameSeq):
        """
        Save one action into the log
        :param actionBuff: action data buff
        :param frameSeq: Frame Sequence
        :return:
        """
        if not self.__enable:
            return True

        try:
            self.__actionQueue.put_nowait((actionBuff, frameSeq))
            return True
        except queue.Full:
            LOG.warning('Result saving action log failed, actionQueue Full')
            return False


class ResultThread(threading.Thread):
    """
    ResultManager Thread implementation
    """
    def __init__(self, frameQueue, actionQueue):
        threading.Thread.__init__(self)
        self.__exited = False
        self.__frameQueue = frameQueue
        self.__actionQueue = actionQueue
        self.__resultTimestamp = time.time()
        self.__resultTimout = 3600
        self.__AIFlag = False
        self.__reportData = None

        self.__resultOutputPath = None
        self.__frameFPS = 10

        self.__testID = str(int(time.time()*1000))
        self.__taskID = 'default'
        self.__gameID = 0
        self.__gameVersion = 'default'

        self.__frameSeqList = list()
        self.__videoWriter = None

        self.__roundCount = 0

        self.__token = None

        self.__resultHTTPUrl = None
        self.__stateHTTPUrl = None
        self.__HTTPHeader = {}
        self.__apiUser = None
        self.__rtxUser = None
        self.__videoFileAbsPath = None
        self.__videoTmpFileAbsPath = None

    def run(self):
        while not self.__exited:
            now = time.time()
            if now - self.__resultTimestamp > self.__resultTimout:
                self.RoundOver()

            self.SavingVideo()
            self.SavingActionLog()

            time.sleep(0.002)
        self.RoundOver()

    def Initialize(self, taskID, resultOutputPath, context):
        """
        Initialize the context data
        :param taskID: the taskID of this service from ASM
        :param resultOutputPath: the path to output directory for result
        :param context: other context data
        :return:
        """
        self.__resultOutputPath = resultOutputPath
        self.__frameFPS = context['fps']
        self.__taskID = taskID

        self.__resultHTTPUrl = context['result_url']
        self.__stateHTTPUrl = context['state_url']
        self.__HTTPHeader = {
            'Content-Type': 'application/json',
            'Connection': 'close',
            'Authorization': 'Token {}'.format(context['token'])
        }

        LOG.info('Result HTTP URL [{}]'.format(self.__resultHTTPUrl))
        LOG.info('State HTTP URL [{}]'.format(self.__stateHTTPUrl))
        LOG.info('HTTP Header [{}]'.format(self.__HTTPHeader))

        self.__apiUser = context['api_user']
        self.__rtxUser = context['rtx_user']

        self.__resultTimout = context['timeout']

        return True

    def Finish(self):
        """
        Exit the thread
        :return:
        """
        self.__exited = True

    def UpdateContext(self, testID=None, taskID=None, gameID=None, gameVersion=None):
        """
        Interface for update the context data
        :param testID: testID from aitest
        :param taskID: taskID from ASM
        :param gameID: gameID from aitest
        :param gameVersion: gameVersion from aitest
        :return:
        """
        if testID is not None:
            self.__testID = testID
        if taskID is not None:
            self.__taskID = taskID
        if gameID is not None:
            self.__gameID = gameID
        if gameVersion is not None:
            self.__gameVersion = gameVersion

    def RoundOver(self):
        """
        When a round over, call this
        :return: True or false
        """
        if self.__videoWriter is None:
            return False

        self.__frameSeqList.clear()
        self._FinishVideo()
        self._FinishLog()
        self._ReportResult()

        self.__roundCount += 1
        return True

    def SavingVideo(self):
        """
        Save one frame into the video
        :return:
        """
        try:
            frame, frameSeq, AIFlag = self.__frameQueue.get_nowait()
        except queue.Empty:
            return False

        if self.__AIFlag != AIFlag:
            self.RoundOver()
            self.__AIFlag = AIFlag

        if self.__videoWriter is None:
            self.__resultTimestamp = time.time()
            if not self._CreateVideo(width=frame.shape[1], height=frame.shape[0]):
                return False

        self._WritingVideo(frame)
        self.__frameSeqList.append(frameSeq)
        return True

    def SavingActionLog(self):
        """
        Save one action into the log
        :return:
        """
        try:
            actionBuff, frameSeq = self.__actionQueue.get_nowait()
        except queue.Empty:
            return False

        try:
            actionData = msgpack.unpackb(actionBuff, object_hook=mn.decode, encoding='utf-8')
            actionData['video_frame_seq'] = self.__frameSeqList.index(frameSeq)
        except ValueError:
            LOG.error('Wrong action frameSeq[{}]'.format(frameSeq))
            return False

        actionStr = json.dumps(actionData)
        LOG_RESULT.debug('{}'.format(actionStr))
        return True

    def _ReportResult(self):
        self._PostJsonData(url=self.__resultHTTPUrl, header=self.__HTTPHeader,
                           data=self.__reportData)

    def _CreateVideo(self, width, height):
        resultDirPath = os.path.join(self.__resultOutputPath, self.__testID, self.__taskID,
                                     str(self.__roundCount))
        os.makedirs(resultDirPath, exist_ok=True)

        if self.__AIFlag:
            videoFileName = '{ts}_ai.avi'.format(ts=int(self.__resultTimestamp))
        else:
            videoFileName = '{ts}_ui.avi'.format(ts=int(self.__resultTimestamp))
        self.__videoFileAbsPath = os.path.join(resultDirPath, videoFileName)
        self.__videoFilePath = os.path.join(self.__testID, self.__taskID, str(self.__roundCount),
                                            videoFileName)

        logTarFileName = '{ts}.tar.gz'.format(ts=int(self.__resultTimestamp))
        self.__logTarFileAbsPath = os.path.join(resultDirPath, logTarFileName)
        self.__logTarFilePath = os.path.join(self.__testID, self.__taskID, str(self.__roundCount),
                                             logTarFileName)

        self.__reportData = self._CreateReportResultData()

        fourcc = cv2.VideoWriter_fourcc(*'DIVX')
        self.__videoWriter = cv2.VideoWriter(self.__videoFileAbsPath, fourcc,
                                             self.__frameFPS, (width, height))
        if self.__videoWriter is not None:
            return True
        else:
            LOG.error('Create videoWriter failed!')
            return False

    def _WritingVideo(self, frame):
        if self.__videoWriter is None:
            LOG.error('Call RoundStart first!')
            return

        self.__videoWriter.write(frame)

    def _FinishVideo(self):
        if self.__videoWriter is not None:
            self.__videoWriter.release()
            self.__videoWriter = None

    def _FinishLog(self):
        with tarfile.open(self.__logTarFileAbsPath, "w:gz") as tar:
            tar.add(LOG_FILE_PATH, arcname=os.path.basename(LOG_FILE_PATH))

    def _CreateReportResultData(self):
        data = dict()
        data['test_id'] = self.__testID
        data['task_id'] = self.__taskID
        data['game_id'] = self.__gameID
        data['game_version'] = self.__gameVersion
        data['video_path'] = self.__videoFilePath
        data['log_path'] = self.__logTarFilePath
        data['source'] = 1
        return data

    def _CreateReportAgentStateData(self, agentStateStr):
        data = dict()
        data['game_id'] = self.__gameID
        data['itest_project_id'] = 0
        data['bz_project_id'] = 0
        data['state'] = agentStateStr
        data['version_name'] = self.__gameVersion
        data['api_user'] = self.__apiUser
        data['rtx_user'] = self.__rtxUser
        data['url'] = 0
        data['md5'] = 0
        data['source'] = 1
        return data

    def _PostJsonData(self, url, header, data):
        if data is None:
            return

        jsonData = json.dumps(data)
        jsonData = bytes(jsonData, 'utf-8')
        LOG.info('POST data [{}]'.format(jsonData))
        try:
            result = self._RequestInfo(url, header, jsonData)
        except Exception as e:
            LOG.error('Send POST to AITEST failed err[{}], if you run AI SDK locally, please ignore'.format(e))
            return

        LOG.info('POST ret [{}]'.format(json.loads(result)))
        return

    def _RequestInfo(self, url, header, data):
        req = request.Request(url, data, header)
        response = request.urlopen(req)
        result = response.read().decode('utf-8')
        return result
