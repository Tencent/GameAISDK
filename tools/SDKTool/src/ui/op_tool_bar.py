# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from PyQt5 import QtWidgets, QtGui

from ..context.app_context import g_app_context
from .tree.applications_tree.ui_explore_tree.ui_explore_tree import UIExploreTree
from .tree.project_node import ProjectNode
from .main_window.tool_window import ui
from ..project.project_manager import g_project_manager

logger = logging.getLogger("sdktool")


class OpToolBar(object):
    def __init__(self, tool_bar=None):
        self.tool_bar = tool_bar
        self.action_open_folder = None
        self.action_save_folder = None
        self.action_begin_debug = None
        self.action_stop_debug = None
        self.action_previous = None
        self.action_next = None
        self.action_phone = None

    def define_action(self):
        self.action_open_folder = QtWidgets.QAction()
        self.action_open_folder.setCheckable(False)
        self.action_open_folder.setChecked(False)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/menu/open_folder.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_open_folder.setIcon(icon1)
        self.action_open_folder.setObjectName("action_open_folder")
        self.tool_bar.addAction(self.action_open_folder)

        self.action_save_folder = QtWidgets.QAction()
        self.action_open_folder.setCheckable(False)
        self.action_open_folder.setChecked(False)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/menu/save.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_save_folder.setIcon(icon2)
        self.action_save_folder.setObjectName("action_save_folder")
        self.tool_bar.addAction(self.action_save_folder)

        self.action_begin_debug = QtWidgets.QAction()
        self.action_begin_debug.setCheckable(False)
        self.action_begin_debug.setEnabled(True)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/menu/debug.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_begin_debug.setIcon(icon4)
        self.action_begin_debug.setObjectName("action_begin_debug")
        self.tool_bar.addAction(self.action_begin_debug)

        self.action_stop_debug = QtWidgets.QAction()
        self.action_stop_debug.setCheckable(False)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/menu/stop.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_stop_debug.setIcon(icon5)
        self.action_stop_debug.setObjectName("action_stop_debug")
        self.tool_bar.addAction(self.action_stop_debug)

        self.action_phone = QtWidgets.QAction()
        # setCheckable 设置为True和False的区别
        # self.action_phone.setCheckable(True)
        self.action_phone.setCheckable(True)
        # self.action_phone.setEnabled(True)
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/menu/app.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_phone.setIcon(icon6)
        self.tool_bar.addAction(self.action_phone)

        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/menu/left_arrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_previous = QtWidgets.QAction()
        self.action_previous.setIcon(icon7)
        self.action_previous.setObjectName("previous")
        self.tool_bar.addAction(self.action_previous)

        icon8 = QtGui.QIcon()
        icon8.addPixmap(QtGui.QPixmap(":/menu/right_arrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.action_next = QtWidgets.QAction()
        self.action_next.setIcon(icon8)
        self.action_next.setObjectName("next")
        self.tool_bar.addAction(self.action_next)

    def set_slot(self):
        project_node = ProjectNode()
        self.action_open_folder.triggered.connect(lambda: project_node.load_project(ui.tree_widget_left,
                                                                                    ui.tree_widget_right))
        self.action_save_folder.triggered.connect(project_node.save_project)
        self.action_phone.triggered.connect(self.click_phone)
        project_node.set_phone_tool(self.action_phone)

        # 上一张和下一张的槽函数
        self.action_previous.triggered.connect(lambda: self.change_label_image(False))
        self.action_next.triggered.connect(lambda: self.change_label_image(True))

    def click_phone(self):
        self.action_phone.setChecked(True)
        g_app_context.set_info("phone", True)

    @staticmethod
    def change_label_image(next_flag):
        """改变样本

        """
        project_path = g_project_manager.get_project_path()
        if not project_path:
            return

        node_name = g_project_manager.get_left_tree_node_name()
        if 'UIExplore' not in node_name:
            return

        ui_explore = UIExploreTree()
        ui_explore.save_label_file()                 # 保存当前图像的标签

        # 判断是点击prev还是next，对应labelImageIndex自加或自减
        if next_flag is True:
            ui_explore.acc_image_index()
        else:
            ui_explore.dec_image_index()
        ui_explore.load_label_image()                  # 显示下一张图像
