# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time

import cv2

from agentenv.GameEnv import GameEnv
from AgentAPI import AgentAPIMgr
from ActionAPI import ActionAPIMgr
from util import util

TASK_CFG_FILE = 'cfg/task/gameReg/EmptyTask.json'
REFER_CFG_FILE = 'cfg/task/gameReg/EmptyRefer.json'
STANDARD_LONG_SIDE = 1280


class Env(GameEnv):
    def __init__(self):
        GameEnv.__init__(self)
        self.__agentAPI = AgentAPIMgr.AgentAPIMgr()
        self.__actionAPI = ActionAPIMgr.ActionAPIMgr()
        self.__state = dict()
        self.__ratio = 1.0
        self.start = True
        self.over = False

        return

    def Init(self):
        taskCfgFile = util.ConvertToSDKFilePath(TASK_CFG_FILE)
        referCfgFile = util.ConvertToSDKFilePath(REFER_CFG_FILE)
        ret = self.__agentAPI.Initialize(taskCfgFile, referCfgFile)
        if not ret:
            self.logger.error('agent API init failed')
            return False

        ret = self.__agentAPI.SendCmd(AgentAPIMgr.MSG_SEND_GROUP_ID, 1)
        if not ret:
            self.logger.error('send message failed')
            return False

        ret = self.__actionAPI.Initialize()
        if not ret:
            self.logger.error('action API init failed')
            return False

        return True

    def Finish(self):
        self.__agentAPI.Release()
        self.__actionAPI.Finish()

        return True

    def GetState(self):
        while True:
            info = self.__agentAPI.GetInfo(AgentAPIMgr.GAME_RESULT_INFO)
            if info is None:
                time.sleep(0.002)
                continue

            if info.get('result') is None:
                time.sleep(0.002)
                continue

            self.__state['frameSeq'] = info['frameSeq']

            self.__ratio = max(info['image'].shape[0], info['image'].shape[1]) / STANDARD_LONG_SIDE
            if self.__ratio == 1.0:
                self.__state['image'] = info['image']
            else:
                height = int(info['image'].shape[0] / self.__ratio)
                width = int(info['image'].shape[1] / self.__ratio)
                self.__state['image'] = cv2.resize(info['image'], (width, height))

            break

        return self.__state

    def IsEpisodeStart(self):
        return self.start

    def IsEpisodeOver(self):
        return self.over

    def DoAction(self, action):
        if action is None:
            return False

        if action['type'] == 'click':
            self._Click(action['x'], action['y'], self.__state['frameSeq'])

        return True

    def _Click(self, px, py, frameSeq):
        if self.__ratio == 1.0:
            self.__actionAPI.Click(px, py, contact=0, frameSeq=frameSeq, durationMS=100)
        else:
            px = int(px * self.__ratio)
            py = int(py * self.__ratio)
            self.__actionAPI.Click(px, py, contact=0, frameSeq=frameSeq, durationMS=100)

        # time.sleep(2.0)

        return True

    # def _Swipe(self, sx, sy, ex, ey, frameSeq):
    #     self.__actionAPI.Swipe(sx, sy, ex, ey, contact=0, frameSeq=frameSeq, durationMS=600, needUp=True)
    #     # time.sleep(2.0)
    #
    #     return True
