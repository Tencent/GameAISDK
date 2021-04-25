# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import logging
import os

from ..dialog.tip_dialog import show_warning_tips
from .abstract_debug import AbstractDebug
from ..canvas.data_source import DataSource
from ..tree.project_data_manager import ProjectDataManager
from ..utils import set_log_text
from ...project.project_manager import g_project_manager
from ...common.define import DEBUG_GAME_REG_CMD, TASK_PATH, TBUS_PATH, REFER_PATH, SDK_BIN_PATH
from ...communicate.agent_api_mgr import AgentAPIMgr, MSG_SEND_GROUP_ID, GAME_RESULT_INFO
from ...context.app_context import AppContext
from ...subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ...common.utils import backend_service_monitor
from ..tree.tree_manager import save_current_data

logger = logging.getLogger('sdktool')


class GameRegDebug(AbstractDebug):
    SERVICE_NAME = 'game_reg_debug'

    def __init__(self):
        AbstractDebug.__init__(self)
        self.program = DEBUG_GAME_REG_CMD
        self.api = None
        self._last_fps = 10
        self.data_source = None

    def initialize(self):
        """重写基类的initialize函数，初始化tbus以及发送任务消息
        """
        self.data_source = DataSource()

        data_mgr = ProjectDataManager()
        if not data_mgr.is_ready():
            show_warning_tips('please config project first')
            return False

        # 设置环境变量
        project_config_path = self.get_project_path()
        task_path = os.path.join(project_config_path, TASK_PATH)
        if not os.path.exists(task_path):
            logger.error("task file %s is not exist, please check", task_path)
            set_log_text("task file {} is not exist, please check".format(task_path))
            return False

        refer_path = os.path.join(project_config_path, REFER_PATH)
        if not os.path.exists(refer_path):
            refer_path = None

        self.api = AgentAPIMgr()
        res = self.api.initialize(task_path,
                                  refer_path,
                                  self_addr="SDKToolAddr",
                                  cfg_path=TBUS_PATH)

        if res is False:
            logger.error("Agent API init failed")
            set_log_text("Agent API init failed")
            return False

        # 发送任务的消息给GameReg进程
        res = self.api.send_cmd(MSG_SEND_GROUP_ID, 1)
        if res is False:
            logger.error("send task failed")
            set_log_text("send task failed")
            return False
        return True

    def send_frame(self, frame=None):
        """ 重写基类的send_frame函数，输入为图像帧，将其发送给GameReg进程

        :param frame:
        :return:
        """
        src_img_dict = self._generate_img_dict(frame)
        ret = self.api.send_src_image(src_img_dict)
        if ret is False:
            logger.error('send frame failed')
            return False

        return True

    def recv_result(self):
        """ 重写基类的recv_result函数，从GameReg进程接收识别结果，并返回对应的结果图像

        :return:
        """
        game_result = self.api.get_info(GAME_RESULT_INFO)
        if game_result is None:
            return None, False

        return game_result['image'], False

    def start_test(self):
        """ 开始测试，与测试按钮绑定，点击测试按钮则执行此函数

        :return:
        """
        # 每次点击测试按钮时，都要执行各个初始化模块的逻辑
        if not self.initialize():
            logger.error("initialize failed")
            set_log_text("initialize failed")
            return False
        try:
            if not save_current_data():
                show_warning_tips('保存数据失败，无法启动功能')
                return

            current_path = os.getcwd()
            os.chdir(SDK_BIN_PATH)
            prj_file_path = g_project_manager.get_project_property_file()
            run_program = "%s/%s cfgpath %s" % (SDK_BIN_PATH, self.program, prj_file_path)
            logger.info(run_program)
            bsa.start_service(service_name=self.SERVICE_NAME, run_programs=run_program,
                              process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                              callback_func=backend_service_monitor)
            os.chdir(current_path)

            time.sleep(1)
            self._last_fps = self.timer.get_fps()
            self.timer.set_fps(1)
            self.timer.start()
            set_log_text("start test success")

            self.set_enabled(True)
            app_ctx = AppContext()
            app_ctx.set_info("phone", False)

        except RuntimeError as err:
            logger.error("start test failed: %s", err)
            set_log_text("start test failed:{}".format(err))
            return False
        return True

    def stop_test(self):
        """ 停止测试

        :return:
        """
        super(GameRegDebug, self).stop_test()
        self.timer.set_fps(self._last_fps)
        is_ok, desc = bsa.stop_service(service_name=self.SERVICE_NAME)
        if is_ok:
            logger.info('stop service %s success', self.SERVICE_NAME)
        else:
            logger.error('stop service %s failed, %s', self.SERVICE_NAME, desc)

    def _generate_img_dict(self, src_img):
        """ 返回发送图像的结构体

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
