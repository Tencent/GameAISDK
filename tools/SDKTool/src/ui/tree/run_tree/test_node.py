# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import traceback
import os
import sys
import threading
import logging

import cv2
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox

from ....common.tool_timer import ToolTimer
from ....communicate.agent_api_mgr import AgentAPIMgr
from ....context.app_context import g_app_context
from ...canvas.data_source import g_data_source
from ....project.project_manager import g_project_manager
from ...canvas.ui_canvas import canvas
from ...dialog.tip_dialog import show_warning_tips
from ...utils import ExecResult, ui, cvimg_to_qtimg, qtpixmap_to_cvimg, create_tree_item, set_log_text, \
    filter_info_log, filter_debug_log, filter_error_log, filter_warn_log
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ....common.define import START_TEST, STOP_TEST, TEST_NAME, PROCESS_NAMES, LOG_LEVEL, IO_PROCESS_NAME, \
    AI_PROCESS_NAME, MC_PROCESS_AI_MODE_NAME, GAMEREG_PROCESS_NAME, UI_PROCESS_NAME, RunType, \
    MC_PROCESS_UI_AI_MODE_NAME, PHONE_CLIENT_PROCESS_NAME, PHONE_CLIENT_PATH, MAX_LOG_LINE_NUM, BIN_PATH, TASK_PATH, \
    REFER_PATH, TBUS_PATH
from ....common.utils import backend_service_monitor
from ....ui.tree.project_data_manager import g_project_data_mgr

logger = logging.getLogger("sdktool")


class TestNode(QObject):
    SERVICE_NAME = 'test_node'

    clear_right_tree_signal = pyqtSignal(ExecResult)
    log_signal = pyqtSignal(str)
    run_signal = pyqtSignal(str, str, bool)

    def __init__(self):
        super().__init__()
        self.__test_node = None
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__show_log_over = False

        '''timer 设置'''
        self.timer = ToolTimer()
        self.timer.set_fps(10)
        self.timer.time_signal.signal[str].connect(self._show_result)
        self.__agent_api_mgr = AgentAPIMgr()
        self.__sdk_running = False

    def recv_result(self):
        return self.__agent_api_mgr.recv_agent()

    @staticmethod
    def _parser_agent_image(agent_info):
        # 帧序号画在界面上
        frameSeq = agent_info['uFrameSeq']
        frame = agent_info.get('image')
        frame = cv2.putText(frame, str(frameSeq), (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (255, 0, 255), 2, cv2.LINE_AA)

        height, width = frame.shape[:2]
        logger.debug("recv a frame######, height %s width %s ########", height, width)
        logger.info("frame dim is %s", frame.ndim)

        # 加载图像，并显示在画布上
        pixmap = cvimg_to_qtimg(frame)
        canvas.load_pixmap(pixmap)
        canvas.mouse_flag = False
        canvas.setEnabled(True)
        canvas.update()

    @staticmethod
    def _parser_agent_action(agent_info):
        """解析动作坐标点

        """
        points = []
        if 'px' in agent_info.keys():
            px = agent_info['px']
            py = agent_info['py']
            points.append([px, py])
        else:
            if 'start_x' not in agent_info.keys():
                return

            start_x = agent_info['start_x']
            start_y = agent_info['start_y']
            points.append([start_x, start_y])
            end_x = agent_info['end_x']
            end_y = agent_info['end_y']
            points.append([end_x, end_y])

        # 动作坐标点画到画布上
        pixmap = canvas.get_pixmap()
        if pixmap is None:
            logger.error("pixmap is none")
            return
        if 0 in [pixmap.width(), pixmap.height()]:
            logger.error("the width or height of pix map invalid")
            return

        cv_image = qtpixmap_to_cvimg(pixmap)

        color = (0, 0, 255)
        thickness = 3
        if len(points) == 1:
            cv2.circle(cv_image, (points[0][0], points[0][1]), 5, color, thickness)
        elif len(points) == 2:
            cv2.line(cv_image, (points[0][0], points[0][1]), (points[1][0], points[1][1]), color, thickness)

        action_name = agent_info['action_name']
        cv2.putText(cv_image, "action: {}".format(action_name), (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    color, thickness, cv2.LINE_AA)
        qt_image = cvimg_to_qtimg(cv_image)
        canvas.load_pixmap(qt_image)
        canvas.mouse_flag = False
        canvas.setEnabled(True)
        canvas.update()

    def _show_result(self):
        """ 展示图像结果，与timer绑定，定时刷新

        :return:
        """
        agent_info = self.recv_result()
        if agent_info is None:
            # logger.debug("frame is None")
            return

        frame = agent_info.get('image')
        # 收到图像包
        if frame is not None:
            self._parser_agent_image(agent_info)
        # 收到动作包
        else:
            self._parser_agent_action(agent_info)

    def create_node(self, run_node):
        if run_node is None:
            logger.error("run node is none, create test node failed")
            return

        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()

        if self.__test_node is None:
            self.__test_node = create_tree_item(key=TEST_NAME, edit=False)
            run_node.addChild(self.__test_node)
            run_node.setExpanded(True)
        else:
            for _ in range(self.__test_node.childCount()):
                self.__test_node.takeChild(0)

        # sub_names = [TEST_CONFIG, START_TEST, STOP_TEST]
        sub_names = [START_TEST, STOP_TEST]
        for sub_name in sub_names:
            self.__test_node.addChild(create_tree_item(key=sub_name, node_type=sub_name, edit=False))
        self.__test_node.setExpanded(True)

    def _combobox_text_changed(self, text):
        current_item = self.__right_tree.currentItem()
        current_item.setText(1, text)

    def _log_level_changed(self, text):
        node = self.__right_tree.currentItem()
        log_level = g_project_data_mgr.get_log_level()
        node_key = node.text(0)
        # text: "ERROR",  "WARN", "INFO",  "DEBUG"
        # node key:  "UI", "GameReg", "Agent"
        if node_key in log_level.keys():
            log_level[node_key] = text
        else:
            logger.error("node key %s not in %s", node_key, log_level.keys())

    def config(self):
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        self.__right_tree.clear()

        # 'log'配置节点的创建
        show_log_node = QTreeWidgetItem(self.__right_tree)
        show_log_node.setText(0, "log")
        log_level = g_project_data_mgr.get_log_level()
        for name in PROCESS_NAMES:
            sub_item = create_tree_item(key=name, edit=False)
            sub_item.setCheckState(0, Qt.Unchecked)
            sub_item.setText(1, log_level.get(name))
            show_log_node.addChild(sub_item)

            combobox = QComboBox()
            combobox.addItems(LOG_LEVEL)
            combobox.setCurrentText(log_level.get(name))
            # combobox.setCurrentIndex(-1)
            combobox.currentTextChanged.connect(self._log_level_changed)
            self.__right_tree.setItemWidget(sub_item, 1, combobox)

        show_log_node.setExpanded(True)

    def finish(self):
        self.stop_test()

    def _start_multi_process(self):
        text = ''
        run_programs = []
        # io
        run_programs.append(IO_PROCESS_NAME)
        # process_param_type.append()

        project_property_file = g_project_manager.get_project_property_file()
        # agent
        run_program = "%s --mode=test --cfgpath=%s" % (AI_PROCESS_NAME, project_property_file)
        run_programs.append(run_program)

        # game_reg
        run_program = "%s cfgpath %s" % (GAMEREG_PROCESS_NAME, project_property_file)
        run_programs.append(run_program)

        # ui or mc
        run_type = g_project_data_mgr.get_run_type()
        logger.info("run type is %s", run_type)

        run_program = MC_PROCESS_AI_MODE_NAME
        if run_type.value == RunType.UI_AI.value:
            # ui
            run_program = "%s cfgpath %s" % (UI_PROCESS_NAME, project_property_file)
            run_programs.append(run_program)
            run_program = MC_PROCESS_UI_AI_MODE_NAME
        run_programs.append(run_program)

        is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                        run_programs=run_programs,
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=backend_service_monitor)

        if not is_ok:
            msg = "start service {} failed, {}".format(self.SERVICE_NAME, desc)
            text += msg
            logger.error(msg)
            set_log_text(text + "\n")
            return False
        msg = "start service {} success".format(self.SERVICE_NAME)
        text += msg
        logger.info(msg)

        # start aiclient
        os.chdir(PHONE_CLIENT_PATH)
        # 结束之前的手机通信模块
        if g_app_context.get_info('phone', False):
            logger.info('close data source')
            g_app_context.set_info('phone', False)
            g_data_source.finish()

        try:
            # 启动 phone client，在SDKTool中启动失败
            logger.info('start phone client: %s', PHONE_CLIENT_PROCESS_NAME)
            is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                            run_programs=PHONE_CLIENT_PROCESS_NAME,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=backend_service_monitor)
            text += desc
            time.sleep(1)
            if not is_ok:
                logger.error("phone_client_process failed, %s", desc)
                text += "phone_client_process failed \n"
                raise RuntimeError('start aiclient failed, will try again')
            else:
                text += "******please wait minutes to start******"
        except RuntimeError:
            # 第一次启动失败，尝试再启动一次
            is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                            run_programs=PHONE_CLIENT_PROCESS_NAME,
                                            process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                            callback_func=backend_service_monitor)
            time.sleep(1)
            if not is_ok:
                set_log_text(text)
                return False

        set_log_text(text)
        return True

    @staticmethod
    def _filter_process_log(line, level):
        """ 根据日志级别过滤日志

        :param self:
        :param line:
        :param level:
        :return:
        """
        if line is None:
            return ''

        if level == 'ERROR':
            return filter_error_log(line)
        if level == 'WARN':
            return filter_warn_log(line)
        if level == 'INFO':
            return filter_info_log(line)
        if level == 'DEBUG':
            return filter_debug_log(line)
        return ''

    def _parser_process_log(self, process, log_level):
        """
        解析各个进程的日志
        :param process:
        :param log_level:
        :return:
        """
        if process is None:
            return ''

        if log_level not in LOG_LEVEL:
            return ''

        # 读取进程日志
        process.stdout.flush()
        line = process.stdout.readline()
        str_line = line.decode('utf-8')
        # 根据日志级别，过滤日志
        return self._filter_process_log(str_line, log_level)

    def _parser_sdk_logs(self):
        # 解析 "UI", 'GameReg', 'Agent'的日志
        str_logger_text = ''
        log_level = g_project_data_mgr.get_log_level()

        for key, _ in log_level.items():
            process = None
            if key == 'UI':
                process = self.__ui_process
            elif key == 'GameReg':
                process = self.__gameReg_process
            elif key == 'Agent':
                process = self.__agent_process

            str_log_level = log_level.get(key)
            str_process_log = self._parser_process_log(process, str_log_level)
            str_process_log = key + str_process_log
            str_logger_text += str_process_log

        return str_logger_text

    def show_sdk_log(self):
        self.__show_log_over = False
        def _show_log():
            sdk_log_text = ''
            line_num = 0
            while not self.__show_log_over:
                cur_text = self._parser_sdk_logs()
                sdk_log_text += cur_text
                line_num += 1
                self.log_signal.emit(sdk_log_text)
                if line_num > MAX_LOG_LINE_NUM:
                    sdk_log_text = ''
                    line_num = 0

        paint_log_thread = threading.Thread(target=_show_log, args=())
        paint_log_thread.start()

    @staticmethod
    def _stop_service(service_name):
        is_ok, desc = bsa.stop_service(service_name=service_name)
        if not is_ok:
            logger.error('stop service %s failed, desc: %s', service_name, desc)
            return False
        logger.info('stop service success')
        return True

    def start_test(self):
        if bsa.exist_service(self.SERVICE_NAME):
            show_warning_tips("service(%s) has already start, please stop it first" % self.SERVICE_NAME)
            return False
        try:
            # 清除共享内存
            self.clear_shm()

            # 初始化tbus
            project_path = g_project_manager.get_project_path()
            task_path = os.path.join(project_path, TASK_PATH)
            refer_path = os.path.join(project_path, REFER_PATH)
            self.__agent_api_mgr.initialize(task_path, refer_path, self_addr="SDKToolAddr", cfg_path=TBUS_PATH)

            # 进入bin目录
            current_path = os.getcwd()
            os.chdir(BIN_PATH)

            # 启动进程
            logger.info('start multi processes')
            success = self._start_multi_process()
            os.chdir(current_path)
            if not success:
                self._stop_service(self.SERVICE_NAME)
                return False

            self.run_signal.emit("test", STOP_TEST, True)

            self.__sdk_running = True

            # 所有的ai子进程启动成功后， 启动接收agent图像帧线程
            logger.info('start timer')
            self.timer.start()
            return success

        except RuntimeError as err:
            set_log_text("{}".format(err))
            logger.error("%s", err)
            return False

    def stop_test(self):
        """
        停止测试
        :return:
        """
        logger.info("*********************stop test**********************")

        current_path = os.getcwd()
        os.chdir(BIN_PATH)
        try:
            bsa.stop_service(self.SERVICE_NAME)
            self.run_signal.emit("test", '', False)
            self.__sdk_running = False

        except RuntimeError:
            exp = traceback.format_exc()
            logger.error(exp)
            set_log_text(exp)
        finally:
            self.__show_log_over = True

        os.chdir(current_path)
        set_log_text("stop process")
        self.timer.stop()

    @staticmethod
    def clear_shm():
        if sys.platform == 'win32':
            return
        os.system('ipcs | awk \'{if($6==0) printf "ipcrm shm %d\n",$2}\'| sh')

    def is_testing(self):
        return self.__sdk_running
