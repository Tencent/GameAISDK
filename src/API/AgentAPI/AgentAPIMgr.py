# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import argparse
import json
import traceback
import logging
import os
import sys

from util.config_path_mgr import SYS_CONFIG_DIR

from .AgentMsgMgr import MsgMgr, MSG_SEND_TASK_CONF, MSG_SEND_GROUP_ID, MSG_SEND_TASK_FLAG, MSG_SEND_ADD_TASK, \
    MSG_SEND_DEL_TASK, MSG_SEND_CHG_TASK

LOG = logging.getLogger('agent')

GAME_STATE_INVALID = -1
GAME_STATE_START = 0
GAME_STATE_RUN = 1
GAME_STATE_LOSE = 2
GAME_STATE_WIN = 3
GAME_STATE_MAX = 4

GAME_STATE = 0


# GameReg---->Agent
RECV_MSG_ID_START = 45000
MSG_RECV_RESULT = RECV_MSG_ID_START + 1

# param 'type' of func GetInfo
CUR_GROUP_TASK_INFO = 11
CUR_GROUP_INFO = 12
GAME_RESULT_INFO = 13
ALL_GROUP_INFO = 14

TBUS_CFG_PATH = 'cfg/platform/bus.ini'


class AgentAPIMgr(object):
    """
    AgentAPIMgr implement for communication between Agent and GameRecognize
    """
    def __init__(self):
        self.__msgMgr = None
        self.__paramDict = dict()
        self.__gameTaskConfig = None
        self.__referTaskConfig = None
        self.__groupDict = None
        self.__taskList = []
        self.__msgHandler = dict()
        self.__debug = False

    def Initialize(self, confFile, referFile=None, index=1, selfAddr=None,
                   cfgPath=None):
        """
        Initialize:
        Initialize MsgMgr object,
        load and send task configure file,
        refer configure file
        """
        if cfgPath is None:
            cfgPath = os.path.join(SYS_CONFIG_DIR, TBUS_CFG_PATH)
        self.__msgMgr = MsgMgr(cfgPath, index)
        self._Register()
        self._ParseArg()

        try:
            if not self.__msgMgr.Initialize(selfAddr):
                LOG.error(traceback.format_exc())
                LOG.error('msgMgr init failed')
                return False
        except RuntimeError as e:
            LOG.error(e)
            return False

        try:
            LOG.info("****************task file %s ******************", confFile)
            with open(confFile) as fd:
                self.__gameTaskConfig = json.load(fd)
                return self.__msgMgr.ProcMsg(MSG_SEND_TASK_CONF, [confFile, referFile])

        except IOError:
            LOG.error('open file [%s] failed', confFile)
            return False

    def SendCmd(self, cmdID, cmdValue):
        """
        pack message and send message to GameRecognize
        """
        try:
            msgSet = {
                MSG_SEND_GROUP_ID,
                MSG_SEND_TASK_FLAG,
                MSG_SEND_ADD_TASK,
                MSG_SEND_DEL_TASK,
                MSG_SEND_CHG_TASK
            }
            if cmdID not in msgSet:
                LOG.error('input cmdID [%s] wrong, please check ', cmdID)
                return False

            if cmdValue is None:
                LOG.error('input cmd value is None, please check')
                return False

            cmdValue = self.__msgHandler[cmdID](cmdValue)
            if cmdValue is None:
                return False

            return self.__msgMgr.ProcMsg(cmdID, cmdValue)
        except RuntimeError as e:
            LOG.error(traceback.format_exc())
            LOG.error(e)
            return False

    def SendSrcImage(self, srcImgDict):
        """
        SDKTool send source image to GameRecognize.
        """
        return self.__msgMgr.ProcSrcImgMsg(srcImgDict)

    def GetInfo(self, msgtype):
        """
        Get information(source image, recognize results, etc.).
        """
        if msgtype not in [CUR_GROUP_TASK_INFO, CUR_GROUP_INFO, GAME_RESULT_INFO, ALL_GROUP_INFO]:
            LOG.error('input type [%s] invalid, please check', msgtype)
            return False

        if CUR_GROUP_TASK_INFO == msgtype:
            return self.__taskList

        if ALL_GROUP_INFO == msgtype:
            taskList = self.__gameTaskConfig.get('alltask') or self.__gameTaskConfig.get('allTask')
            return taskList

        if CUR_GROUP_INFO == msgtype:
            return self.__groupDict

        if GAME_RESULT_INFO == msgtype:
            msgResult = self.__msgMgr.Recv()
            if msgResult:
                gameRets = msgResult['value']
                self._Check(gameRets)
                if self.__debug:
                    self.SendImageToTool(gameRets)
                return gameRets

    def SendImageToTool(self, result):
        image = result.get("image")
        if image is None:
            return

        srcImgDict = dict()
        srcImgDict['frameSeq'] = result.get('frameSeq')
        srcImgDict['image'] = image
        srcImgDict['width'] = image.shape[1]
        srcImgDict['height'] = image.shape[0]
        srcImgDict['deviceIndex'] = 1
        return self.__msgMgr.SendImageToTool(srcImgDict)

    def Release(self):
        """
        exit tbus
        """
        self.__msgMgr.Release()

    def _Check(self, gameRets):
        groupID = gameRets['groupID']
        result = gameRets['result']
        popTaskID = []
        for taskID, _ in result.items():
            find = False
            for task in self.__taskList:
                if task['taskID'] == taskID:
                    find = True
                    break

            if not find:
                popTaskID.append(taskID)
                # result.pop(taskID)
                LOG.warning('get taskID [%s] in reg results not find in taskList, please check', taskID)

        for taskID in popTaskID:
            result.pop(taskID)

        if self.__groupDict['groupID'] != groupID:
            selfGroupID = self.__groupDict['groupID']
            LOG.error('recv group ID [%s] in reg results not match self group ID [%s], '
                      'please check', groupID, selfGroupID)

    def _Register(self):
        self.__msgHandler[MSG_SEND_GROUP_ID] = self._ProcSendGroupID
        self.__msgHandler[MSG_SEND_TASK_FLAG] = self._ProcSendTaskFlag
        self.__msgHandler[MSG_SEND_ADD_TASK] = self._ProcSendAddTask
        self.__msgHandler[MSG_SEND_DEL_TASK] = self._ProcSendDelTask
        self.__msgHandler[MSG_SEND_CHG_TASK] = self._ProcSendChgTask

    def _ProcSendGroupID(self, cmdValue):
        groupDict = None
        groupList = self.__gameTaskConfig.get('alltask') or \
                    self.__gameTaskConfig.get('allTask') or []
        for group in groupList:

            if cmdValue == group.get('groupID'):
                groupDict = group
                break

        if groupDict:
            self.__groupDict = groupDict
            self.__taskList = groupDict['task']

        else:
            LOG.error('input group id [%s] invalid, please check ', cmdValue)
        return groupDict

    def _ProcSendTaskFlag(self, cmdValue):

        delkeys = []
        for key, _ in cmdValue.items():
            find = False

            for task in self.__taskList:
                if key == task['taskID']:
                    find = True
                    break

            if not find:
                LOG.error("input task [%s] not in taskList, please check", key)
                delkeys.append(key)

        for key in delkeys:
            cmdValue.pop(key)

        return cmdValue

    def _ProcSendAddTask(self, cmdValue):
        for item in cmdValue:
            if item in self.__taskList:
                LOG.error('input task [%s] already in taskList, please check', item)
                cmdValue.remove(item)
            else:
                self.__taskList.append(item)

        self.__groupDict['task'] = self.__taskList

        return cmdValue

    def _ProcSendDelTask(self, cmdValue):
        taskIDList = []
        for item in self.__taskList:
            taskID = item.get('taskID')
            taskIDList.append(taskID)

        for taskID in cmdValue:
            find = False
            for item in self.__taskList:
                if taskID == item['taskID']:
                    self.__taskList.remove(item)
                    find = True
                    break

            if not find:
                LOG.error('input task [%s] not in taskList, please check', item)
                cmdValue.remove(taskID)

        self.__groupDict['task'] = self.__taskList

        return cmdValue

    def _ProcSendChgTask(self, cmdValue):
        for item in cmdValue:
            find = False
            for taskInfo in self.__taskList:
                if taskInfo['taskID'] == item['taskID']:
                    self.__taskList.remove(taskInfo)
                    self.__taskList.append(item)
                    find = True
                    break
            if not find:
                LOG.error('input task [%s]not in taskList, please check', item)
                cmdValue.remove(item)

        self.__groupDict['task'] = self.__taskList
        return cmdValue

    def _ParseArg(self):
        parser = argparse.ArgumentParser(description='')
        parser.add_argument('--mode', type=str, default='test', choices=['test', 'train', 'SDKTool'],
                            help='set run mode')
        parser.add_argument('--loglevel', type=str, default='default',
                            choices=['default', 'debug', 'info', 'warnning', 'error'], help='set log level')
        parser.add_argument('--debug', type=bool, default=False, help='debug with sdktool (True/False)')
        parser.add_argument('--cfgpath', type=str, default='../', help='config path')
        args = parser.parse_args()
        self.__debug = args.debug

        LOG.info("argv is %s, debug is %s,type is %s", sys.argv, self.__debug, type(self.__debug))
