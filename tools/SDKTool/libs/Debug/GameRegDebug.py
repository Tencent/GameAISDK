# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from libs.AgentAPI.AgentAPIMgr import *
from .AbstractDebug import *


# 与GameReg的调试类
class GameRegDebug(AbstractDebug):
    def __init__(self, canvas=None, ui=None):
        AbstractDebug.__init__(self, canvas, ui)
        self.testPrograme += "/GameReg SDKTool"

    def initialize(self):
        '''重写基类的initialize函数，初始化tbus以及发送任务消息'''
        self.gameRegAPI = AgentAPIMgr()
        env_dist = os.environ
        sdkPath = env_dist['AI_SDK_PATH']
        if sdkPath is None:
            self.logger.error('there is no AI_SDK_PATH')
            return False

        # 初始化AgentAPI，建立tbus通道，以及读取task的配置文件
        res = self.gameRegAPI.Initialize(sdkPath + "/cfg/task/gameReg/task_SDKTool.json",
                                         sdkPath + "/cfg/task/gameReg/refer_SDKTool.json",
                                         selfAddr="SDKToolAddr",
                                         cfgPath=TBUS_PATH)
        if res is False:
            self.logger.error("Agent API init failed")
            return False

        # 发送任务的消息给GameReg进程
        res = self.gameRegAPI.SendCmd(MSG_SEND_GROUP_ID, 1)
        if res is False:
            self.logger.error("send task failed")
            return False

        return True

    def send_frame(self, frame=None):
        '''重写基类的send_frame函数，输入为图像帧，将其发送给GameReg进程'''
        srcImgDict = self._generate_img_dict(frame)
        ret = self.gameRegAPI.SendSrcImage(srcImgDict)
        if ret is False:
            self.logger.error('send frame failed')
            return False

        return True

    def recv_result(self):
        '''重写基类的recv_result函数，从GameReg进程接收识别结果，并返回对应的结果图像'''
        GameResult = self.gameRegAPI.GetInfo(GAME_RESULT_INFO)
        if GameResult is None:
            return

        return GameResult['image']

    def _generate_img_dict(self, srcImg):
        '''返回发送图像的结构体'''
        srcImgDict = dict()
        srcImgDict['frameSeq'] = self.frameSeq
        self.frameSeq += 1
        srcImgDict['image'] = srcImg
        srcImgDict['width'] = srcImg.shape[1]
        srcImgDict['height'] = srcImg.shape[0]
        srcImgDict['deviceIndex'] = 1

        return srcImgDict