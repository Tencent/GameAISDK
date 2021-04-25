# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import logging
import sys
from abc import ABCMeta, abstractmethod

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QStyle
import cv2

from ...common.tool_timer import ToolTimer
from ..canvas.ui_canvas import canvas
from ..main_window.tool_window import ui
from ...project.project_manager import ProjectManager

platform = sys.platform


logger = logging.getLogger("sdktool")


# 调试的基类，实现大部分调试的功能，通过定义几个虚函数给子类来实现模块的扩展
class AbstractDebug(object):
    __metaclass__ = ABCMeta

    VIDEO_TYPE_OFFLINE = 0       # 在线视频
    VIDEO_TYPE_REAL_TIME = 1     # 离线示频

    # 播放的三个状态
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    video_url = ""

    def __init__(self):
        # self.canvas = canvas
        # self.ui = ui
        self.frame_count = 0
        self.video_time = 0.
        self.preslider_value = 0
        self.is_change_slider = False
        self.frame_seq = 1
        self.sub_program = None

        self.api = None
        """创建暂停按钮，并连接对应的槽函数"""
        ui.video_button.clicked.connect(self._switch_video)
        self.status = AbstractDebug.STATUS_INIT

        """timer 设置"""
        self.timer = ToolTimer()
        self.timer.set_fps(10)
        self.timer.time_signal.signal[str].connect(self._next_frame)
        # self.timer.time_signal.signal[str].connect(self._show_result)
        self.program = None

        self.data_source = None
        # self.phoneInstance = IDeviceAPI('Android', 'PlatformWeTest')

        self.__image_list = []
        self.__image_index = 0

    @abstractmethod
    def initialize(self):
        # """初始化函数，可重写它来执行一些最开始的必要的逻辑"""
        raise NotImplementedError()

    @abstractmethod
    def send_frame(self, frame=None):
        """发送帧消息，包括但不限于图像，因此需要各个模块自己实现自己的发送消息逻辑"""
        raise NotImplementedError()

    @abstractmethod
    def recv_result(self):
        """接受返回的结果，需要各个模块自己实现"""
        raise NotImplementedError()

    @staticmethod
    def get_project_path():
        return ProjectManager().get_project_path()

    def _show_result(self):
        """展示图像结果，与timer绑定，定时刷新"""
        frame, ret = self.recv_result()
        if frame is None:
            logger.debug("frame is None")
            return

        # cv2.rectangle(frame, (100, 100), (600, 600), (0, 0, 255), 5)
        # height, width = frame.shape[:2]
        # logger.debug("recv a frame######, height {} width {}e########".format(height, width))
        rgb = None
        if frame.ndim == 3:
            height, width, depth = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        elif frame.ndim == 2:
            height, width = frame.shape
            depth = 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        if rgb is None:
            return
        image = QImage(rgb.data, width, height, width*depth, QImage.Format_RGB888)
        # image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)
        canvas.load_pixmap(pixmap)
        canvas.mouse_flag = False
        canvas.setEnabled(True)
        canvas.update()
        # show result and sleep 1 second
        if ret:
            time.sleep(1)

    def start_test(self):
        """开始测试，与测试按钮绑定，点击测试按钮则执行此函数"""
        raise NotImplementedError()

    def finish(self):
        self.stop_test()
        if self.data_source is not None:
            self.data_source.finish()

    def stop_test(self):
        """停止测试

        """
        self._stop()
        self.set_enabled(False)

    def _stop(self):
        """关闭视频，回收资源"""
        self.frame_seq = 1
        self.status = AbstractDebug.STATUS_PAUSE

        self.timer.stop()
        self.__image_index = 0

    def _switch_video(self):
        """与暂停/开始按钮绑定，点击按钮则切换状态"""
        if self.status is AbstractDebug.STATUS_INIT:
            self.timer.start()
            ui.video_button.setIcon(ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))
        elif self.status is AbstractDebug.STATUS_PLAYING:
            self.timer.stop()
            ui.video_button.setIcon(ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        elif self.status is AbstractDebug.STATUS_PAUSE:
            self.timer.start()
            ui.video_button.setIcon(ui.mainWindow.style().standardIcon(QStyle.SP_MediaPause))

        self.status = (AbstractDebug.STATUS_PLAYING,
                       AbstractDebug.STATUS_PAUSE,
                       AbstractDebug.STATUS_PLAYING)[self.status]

    def _reset(self):
        """视频播放完后释放资源"""
        self.timer.stop()
        self.status = AbstractDebug.STATUS_INIT
        ui.video_button.setIcon(ui.mainWindow.style().standardIcon(QStyle.SP_MediaPlay))
        self.__image_index = 0

    @staticmethod
    def set_enabled(flag):
        """将按钮状态设为enable"""
        ui.video_button.setEnabled(flag)
        ui.video_label.setEnabled(flag)

    @staticmethod
    def _ms2text(s):
        """毫秒转换为时间显示，比如04:13:32"""
        value = int(s / 60)
        text_second = str(int(s % 60)).zfill(2)
        text_minute = str(int(value % 60)).zfill(2)
        text_hour = str(int(value / 60)).zfill(2)
        text = text_hour + " : " + text_minute + " : " + text_second
        return text

    def _next_frame(self):
        """
            将下一帧的数据发送给对应进程，与其绑定的元素有两个：
            1： 快进按钮
            2： timer
        """
        # 从手机获取下一帧图片
        frame = self.data_source.get_frame()
        if frame is None:
            # if strError != "":
            # logger.error("get frame failed: {}".format(strError))
            return

        self.send_frame(frame)
        self._show_result()
