# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import traceback
import logging

from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QPoint, QSize

from .resource_rc import q_init_resources
from ...ui.canvas.data_source import DataSource
from ...ui.canvas.ui_canvas import canvas
from ...ui.debug.debug_factory import DebugFactory
from ...ui.op_tool_bar import OpToolBar
from ...ui.op_tree import OpTree
from ...ui.menu.op_menu import OpMenu
from ...ui.tree.run_tree.run_tree import RunTree
from ...ui.tree.ui_tree.ui_tree import UITree
from ...ui.tree.scene_tree.scene_tree import SceneTree
from ..tree.project_node import ProjectNode
from ...subprocess_service.subprocess_service_manager import backend_service_manager


class SDKMainWindow(QMainWindow):

    def __init__(self, ui=None):
        super(SDKMainWindow, self).__init__()
        q_init_resources()
        self.__ui = ui
        self.__logger = logging.getLogger('sdktool')
        self.__op_tool_bar = None
        self.__op_menu = None
        self.__op_tree = None

    def reset_window(self):
        desktop = QApplication.desktop()
        desktop_width = desktop.width()
        desktop_height = desktop.height()

        self.__logger.info("desktop width %s, height %s", desktop_width, desktop_height)
        self.move(QPoint(0, 0))

        self.resize(QSize(desktop_width, int(desktop_height*0.95)))

    def init(self):
        self.reset_window()
        left_tree = self.__ui.tree_widget_left
        right_tree = self.__ui.tree_widget_right
        min_width = int(self.geometry().width() / 5)
        right_tree.setMinimumSize(QSize(min_width, 16777215))

        ui_tree = UITree()
        ui_tree.init(self.__ui.tree_widget_left, self.__ui.tree_widget_right)

        scene_tree = SceneTree()
        scene_tree.init(self.__ui.tree_widget_left, self.__ui.tree_widget_right)

        self.__op_menu = OpMenu(self.__ui.menu_bar)
        self.__op_menu.define_action()
        self.__op_menu.set_slot(left_tree=left_tree, right_tree=right_tree)

        self.__op_tree = OpTree()
        self.__op_tree.define_action()
        self.__op_tree.set_slot(left_tree=left_tree, right_tree=right_tree)

        self.__op_tool_bar = OpToolBar(self.__ui.tool_bar)
        self.__op_tool_bar.define_action()
        self.__op_tool_bar.set_slot()

        self.__ui.set_ui_canvas(canvas)

    def finish(self):
        # 如果连接了设备，在退出前，需先中止timer，否则会出现crash
        self.__logger.info("end ProjectNode")
        ProjectNode().finish()

        self.__logger.info("end DebugFactory")
        factory = DebugFactory()
        factory.finish()

        self.__logger.info("end DataSource")
        data_source = DataSource()
        data_source.finish()

        self.__logger.info("end RunTree")
        run_tree = RunTree()
        run_tree.finish()

    def closeEvent(self, evt):
        try:
            self.__logger.info('ready to close window')
            self.finish()
        except RuntimeError:
            exp = traceback.format_exc()
            self.__logger.error(exp)
        finally:
            backend_service_manager.exit_all_service()
        return super(SDKMainWindow, self).closeEvent(evt)
