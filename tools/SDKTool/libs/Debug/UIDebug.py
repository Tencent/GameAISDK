# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from libs.AgentAPI.AgentAPIMgr import *
from .AbstractDebug import *

# 与UIRecognize的调试类
class UIDebug(AbstractDebug):
    def __init__(self, canvas=None, ui=None):
        AbstractDebug.__init__(self, canvas, ui)
        self.testPrograme += "/UIRecognize"

    def initialize(self):
        '''重写基类的initialize函数，初始化tbus'''
        self.UIAPI = AgentAPIMgr()
        env_dist = os.environ
        sdkPath = env_dist['AI_SDK_PATH']
        if sdkPath is None:
            logging.error('there is no AI_SDK_PATH')
            return False

        # 初始化AgentAPI，建立tbus通道
        res = self.UIAPI.Initialize(sdkPath + "/cfg/task/gameReg/task_SDKTool.json",
                                    sdkPath + "/cfg/task/gameReg/refer_SDKTool.json",
                                    selfAddr="SDKToolAddr",
                                    cfgPath=TBUS_PATH)
        if res is False:
            self.logger.error("Agent API init failed")
            return False

        return True

    def send_frame(self, frame=None):
        '''重写基类的send_frame函数，输入为图像帧，将其发送给UIRecognize进程'''
        srcImgDict = self._generate_img_dict(frame)
        ret = self.UIAPI.SendUISrcImage(srcImgDict)
        if ret is False:
            logging.error('send frame failed')
            return False

        return True

    def recv_result(self):
        '''重写基类的recv_result函数，从UIRecognize进程接收识别结果，并返回对应的结果图像'''
        UIResult = self.UIAPI.RecvUIResult()
        if UIResult is None:
            self.logger.debug("get UI result failed")
            return
        return self._proc_UI_result(UIResult)

    def _proc_UI_result(self, UIResult):
        '''将UIRecognize返回的结果画在图像上'''
        if UIResult is None:
            self.logger.error('UIResult is None')
            return None

        frame = UIResult['image']
        if frame is None:
            self.logger.error('image is None')
            return None

        for action in UIResult['actions']:
            UIType = action.get('type')
            self.logger.info('UI type: {}'.format(UIType))
            if UIType == common_pb2.PB_UI_ACTION_CLICK:
                cv2.putText(frame, "click", (action['points'][0]['x'], action['points'][0]['y']),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                cv2.circle(frame, (action['points'][0]['x'], action['points'][0]['y']), 8, (0, 0, 255), -1)
            elif UIType == common_pb2.PB_UI_ACTION_DRAG:
                cv2.putText(frame, "drag", (action['points'][0]['x'], action['points'][0]['y']),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                cv2.line(frame, (action['points'][0]['x'], action['points'][0]['y']),
                         (action['points'][1]['x'], action['points'][1]['y']), (0, 0, 255), 3)

        return frame

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