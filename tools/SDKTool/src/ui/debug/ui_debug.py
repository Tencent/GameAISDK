# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import os
import time
import cv2

from .abstract_debug import AbstractDebug
from ..canvas.data_source import DataSource
from ..tree.project_data_manager import ProjectDataManager
from ...project.project_manager import g_project_manager
from ..utils import set_log_text
from ...common.define import DEBUG_UI_CMD, TASK_PATH, REFER_PATH, SDK_BIN_PATH, TBUS_PATH
from ...communicate.agent_api_mgr import AgentAPIMgr
from ...communicate.protocol import common_pb2
from ...context.app_context import AppContext
from ...subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ..dialog.tip_dialog import show_warning_tips
from ...common.utils import backend_service_monitor
from ..tree.tree_manager import save_current_data

logger = logging.getLogger('sdktool')


class UIDebug(AbstractDebug):
    SERVICE_NAME = 'ui_debug'

    def __init__(self):
        AbstractDebug.__init__(self)
        self.program = DEBUG_UI_CMD
        self.api = None
        self._last_fps = 10
        self.data_source = None

    def initialize(self):
        """ Initialize
        重写基类的initialize函数，初始化tbus
        :return:
        """
        self.data_source = DataSource()
        data_mgr = ProjectDataManager()
        if not data_mgr.is_ready():
            show_warning_tips('please config project first')
            return False

        project_config_path = self.get_project_path()
        task_path = os.path.join(project_config_path, TASK_PATH)
        refer_path = os.path.join(project_config_path, REFER_PATH)
        if not os.path.exists(refer_path):
            refer_path = None

        self.api = AgentAPIMgr()
        self.api.initialize(task_path, refer_path, self_addr="SDKToolAddr", cfg_path=TBUS_PATH)

        self.set_enabled(True)
        return True

    def send_frame(self, frame=None):
        """ SendFrame
            重写基类的send_frame函数，输入为图像帧，将其发送给UIRecognize进程
        :param frame:
        :return:
        """

        src_img_dict = self._generate_img_dict(frame)
        ret = self.api.send_ui_src_image(src_img_dict)

        if ret is False:
            logging.error('send frame failed')
            return False
        return True

    def recv_result(self):
        """ RecvResult
        重写基类的recv_result函数，从UIRecognize进程接收识别结果，并返回对应的结果图像
        :return:
        """
        ui_result = self.api.recv_ui_result()

        if ui_result is None:
            logger.debug("get UI result failed")
            return None, False
        return self._proc_ui_result(ui_result)

    def start_test(self):
        """开始测试，与测试按钮绑定，点击测试按钮则执行此函数

        """
        # 每次点击测试按钮时，都要执行各个初始化模块的逻辑
        if not self.initialize():
            logger.error("initialize failed, please check")
            return False
        try:
            if not save_current_data():
                show_warning_tips('保存数据失败，无法启动功能')
                return

            current_path = os.getcwd()
            os.chdir(SDK_BIN_PATH)
            time.sleep(1)
            prj_file_path = g_project_manager.get_project_property_file()
            run_program = "%s/%s cfgpath %s" % (SDK_BIN_PATH, self.program, prj_file_path)
            is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME, run_programs=run_program,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=backend_service_monitor)
            if not is_ok:
                logger.error(desc)
                return False

            os.chdir(current_path)

            self._last_fps = self.timer.get_fps()
            self.timer.set_fps(1)
            self.timer.start()

            self.set_enabled(True)
            app_ctx = AppContext()
            app_ctx.set_info("phone", False)

        except RuntimeError as err:
            logger.error("start test failed:%s", err)
            set_log_text("start test failed:{}".format(err))
            return False

        return True

    def stop_test(self):
        """ 停止测试

        :return:
        """
        super(UIDebug, self).stop_test()
        self.timer.set_fps(self._last_fps)
        logger.info('stop service:%s', self.SERVICE_NAME)
        is_ok, desc = bsa.stop_service(service_name=self.SERVICE_NAME)
        if is_ok:
            logger.info('stop service %s success', self.SERVICE_NAME)
        else:
            logger.error('stop service %s failed, %s', self.SERVICE_NAME, desc)

    @staticmethod
    def _proc_ui_result(ui_result):
        """ ProcUIResult
        将UIRecognize返回的结果画在图像上'''
        :param ui_result:
        :return:
        """
        ret = False
        if ui_result is None:
            logger.error('ui_result is None')
            return None, ret

        frame = ui_result['image']
        if frame is None:
            logger.error('image is None')
            return None, ret
        # logger.debug("proc ui result #############frame is {}#############".format(frame))

        for action in ui_result['actions']:
            ui_type = action.get('type')
            logger.info('UI type: %s', ui_type)
            if ui_type == common_pb2.PB_UI_ACTION_CLICK:
                cv2.putText(frame, "click", (action['points'][0]['x'], action['points'][0]['y']),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                cv2.circle(frame, (action['points'][0]['x'], action['points'][0]['y']), 8, (0, 0, 255), -1)
                logger.info('action: click (%s, %s)', action['points'][0]['x'], action['points'][0]['y'])
                ret = True
            elif ui_type == common_pb2.PB_UI_ACTION_DRAG:
                cv2.putText(frame, "drag", (action['points'][0]['x'], action['points'][0]['y']),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                cv2.line(frame, (action['points'][0]['x'], action['points'][0]['y']),
                         (action['points'][1]['x'], action['points'][1]['y']), (0, 0, 255), 3)
                logger.info('action: drag (%s, %s)-->(%s, %s)', action['points'][0]['x'],
                            action['points'][0]['y'], action['points'][1]['x'], action['points'][1]['y'])
                ret = True
        return frame, ret

    def _generate_img_dict(self, src_img):
        """ GenerateImgDict
            返回发送图像的结构体
        :param src_img:
        :return:
        """
        src_img_dict = dict()
        src_img_dict['frameSeq'] = self.frame_seq
        self.frame_seq += 1
        src_img_dict['image'] = src_img
        src_img_dict['width'] = src_img.shape[1]
        src_img_dict['height'] = src_img.shape[0]
        src_img_dict['deviceIndex'] = 1

        return src_img_dict
