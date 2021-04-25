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
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QPushButton, QFrame, QInputDialog

from .data_source import DeviceActionParamName, DeviceActionType
from ...project.project_manager import g_project_manager
from ...WrappedDeviceAPI.deviceAPI.mobileDevice.android.APIDefine import DeviceKeys

logger = logging.getLogger("sdktool")


class DeviceOperationToolbar(QFrame):
    """ 设备操作工具栏，在canvas上展现

    """
    def __init__(self, parent, **kwargs):
        super(DeviceOperationToolbar, self).__init__(parent, **kwargs)
        self._parent = parent
        # self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShape(QFrame.Box)
        # self.setFrameShadow(QFrame.Raised)
        # self.setWindowOpacity(1)

        # 控件QPushButton的定义和设置
        self._btn_home = QPushButton(self)
        self._btn_home.setStyleSheet("QPushButton{border-image: url(Resource/home.png)}"
                                     "QPushButton:hover{border-image: url(Resource/home_hover.png)}")
        self._btn_home.setToolTip('HOME')

        self._btn_menu = QPushButton(self)
        self._btn_menu.setStyleSheet("QPushButton{border-image: url(Resource/menu.png)}"
                                     "QPushButton:hover{border-image: url(Resource/menu_hover.png)}")
        self._btn_menu.setToolTip('MENU')

        self._btn_back = QPushButton(self)
        self._btn_back.setStyleSheet("QPushButton{border-image: url(Resource/back.png)}"
                                     "QPushButton:hover{border-image: url(Resource/back_hover.png)}")
        self._btn_back.setToolTip('BACK')

        self._btn_input = QPushButton(self)
        self._btn_input.setStyleSheet("QPushButton{border-image: url(Resource/input.png)}"
                                      "QPushButton:hover{border-image: url(Resource/input_hover.png)}")
        self._btn_input.setToolTip('输入文本')

        self._btn_capture = QPushButton(self)
        self._btn_capture.setStyleSheet("QPushButton{border-image: url(Resource/capture.png)}"
                                        "QPushButton:hover{border-image: url(Resource/capture_hover.png)}")
        self._btn_capture.setToolTip('截屏')

        # 设置控件QPushButton的位置和大小
        btn_size = 16
        left = top = 10
        self._btn_back.setGeometry(left, top, btn_size, btn_size)
        left = left + btn_size + 5
        self._btn_home.setGeometry(left, top, btn_size, btn_size)
        left = left + btn_size + 5
        self._btn_menu.setGeometry(left, top, btn_size, btn_size)
        left = left + btn_size + 5
        self._btn_input.setGeometry(left, top, btn_size, btn_size)
        left = left + btn_size + 5
        self._btn_capture.setGeometry(left, top, btn_size, btn_size)

        self._btn_home.clicked.connect(self.on_btn_home_click)
        self._btn_menu.clicked.connect(self.on_btn_menu_click)
        self._btn_back.clicked.connect(self.on_btn_back_click)
        self._btn_input.clicked.connect(self.on_btn_input_click)
        self._btn_capture.clicked.connect(self.on_btn_capture_click)

        self._pressed_point = [0, 0]
        self._data_source = None

    def enable_android_buttons(self, enable=True):
        self._btn_home.setEnabled(enable)
        self._btn_menu.setEnabled(enable)
        self._btn_back.setEnabled(enable)

    def set_data_source(self, data_source):
        self._data_source = data_source

    def on_btn_home_click(self, checked):
        logger.info('on home click, checked: %s', checked)
        if self._data_source:
            kwargs = {}
            kwargs[DeviceActionParamName.KEY] = DeviceKeys.HOME
            self._data_source.do_action(DeviceActionType.INPUT_KEY, **kwargs)

    def on_btn_menu_click(self, checked):
        logger.info('on menu click, checked: %s', checked)
        if self._data_source:
            kwargs = {}
            kwargs[DeviceActionParamName.KEY] = DeviceKeys.MENU
            self._data_source.do_action(DeviceActionType.INPUT_KEY, **kwargs)

    def on_btn_back_click(self, checked):
        logger.info('on back click, checked: %s', checked)
        if self._data_source:
            kwargs = {}
            kwargs[DeviceActionParamName.KEY] = DeviceKeys.BACK
            self._data_source.do_action(DeviceActionType.INPUT_KEY, **kwargs)

    def on_btn_input_click(self, checked):
        logger.info('on input click, checked: %s', checked)
        if self._data_source:
            text, ok = QInputDialog.getText(self, '输入文本', '文本: ')
            if ok and text:
                kwargs = {}
                kwargs[DeviceActionParamName.KEY] = text
                self._data_source.do_action(DeviceActionType.INPUT_TEXT, **kwargs)

    def on_btn_capture_click(self, checked):
        logger.info('on capture click, checked: %s', checked)
        if self._data_source:
            img_data = self._data_source.get_frame()
            if img_data is not None:
                project_path = g_project_manager.get_project_path()
                project_name = os.path.split(project_path.strip(os.path.sep).strip('/'))[1]
                dst_dir = os.path.join(project_path, 'data', project_name)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                file_path = os.path.join(dst_dir, 'snapshot_%s.jpg' % int(time.time()))
                cv2.imwrite(file_path, img_data)

    def mousePressEvent(self, e):
        self._pressed_point = [e.x(), e.y()]

    def mouseMoveEvent(self, e):
        x = e.x() - self._pressed_point[0]
        y = e.y() - self._pressed_point[1]
        cor = QPoint(x, y)
        self.move(self.mapToParent(cor))
