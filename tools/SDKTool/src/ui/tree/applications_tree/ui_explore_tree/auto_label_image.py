# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import time
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox

from ....dialog.tip_dialog import show_warning_tips, show_question_tips
from ....utils import get_files_count, clear_files
from .....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from .....subprocess_service.process_timer import ProcessTimer

platform = sys.platform


class AutoLabelImage(object):
    SERVICE_NAME = 'auto_label'

    def __init__(self, canvas):
        self.__logger = logging.getLogger('sdktool')
        self.__canvas = canvas
        self.__auto_label_path = None

        self._auto_label_process_running = False
        # path to RefineDet
        file_fir = os.path.dirname(os.path.abspath(__file__))
        self.__refine_det_path = os.path.join(file_fir, "../../../../../../../Modules/RefineDet/")

    def set_path(self, path):
        self.__auto_label_path = path

    def _auto_label_callback(self, service_state, desc, *args, **kwargs):
        self.__logger.info("service state(%s), desc(%s), args: %s, kwargs: %s", service_state, desc, args, kwargs)
        if service_state != ProcessTimer.SERVICE_STATE_RUNING:
            self._auto_label_process_running = False

    def judge_over(self, image_count):
        json_count = get_files_count(self.__auto_label_path, [".json"])
        if json_count >= image_count:
            self.__logger.info("task done")
            return True, json_count
        return False, json_count

    def label(self):
        image_count = get_files_count(self.__auto_label_path)
        if image_count <= 0:
            text = "failed, no image in {}, please check".format(self.__auto_label_path)
            show_warning_tips(text)
            return

        if not show_question_tips('是否启动自动标注功能，选择是，将清空上次自动标注的结果'):
            return

        # 清空上次自动标注的结果
        clear_files(self.__auto_label_path, ['.json'])

        # ...................Auto label subprocess begin..................
        current_path = os.getcwd()
        if not os.path.exists(self.__refine_det_path):
            raise Exception("RefineDet Path {} is not exist".format(self.__refine_det_path))

        self._auto_label_process_running = True

        os.chdir(self.__refine_det_path)

        run_program = "python detect_mutilple_images.py --test_images {}".format(self.__auto_label_path)
        is_ok, desc = bsa.start_service(service_name=self.SERVICE_NAME,
                                        run_programs=run_program,
                                        process_param_type=bsa.SUBPROCESS_SHELL_TYPE,
                                        callback_func=self._auto_label_callback)
        os.chdir(current_path)

        if not is_ok:
            msg = "start auto label failed, {}".format(desc)
            self.__logger.error(msg)
            return
        msg = "start auto label success, pid: {}".format(bsa.get_pids(service_name=self.SERVICE_NAME))
        self.__logger.info(msg)

        # ...................Auto label subprocess end..................
        self.__canvas.create_process_bar("自动标签", "处理中", 0, image_count)

        while self._auto_label_process_running:
            task_done, json_count = self.judge_over(image_count)
            if task_done:
                break
            self.__logger.debug("josn count is %s", json_count)
            self.__canvas.set_bar_cur_value(json_count)
            QApplication.processEvents()
            time.sleep(0.5)

        self.__canvas.close_bar()
        task_done, _ = self.judge_over(image_count)
        if task_done:
            QMessageBox.information(self.__canvas, "提示", "处理完成")
        else:
            show_warning_tips('自动标注进程异常退出')

        is_ok, desc = bsa.stop_service(service_name=self.SERVICE_NAME)
        if not is_ok:
            self.__logger.error("stop service %s failed", self.SERVICE_NAME)
        else:
            self.__logger.info("stop service %s success", self.SERVICE_NAME)
