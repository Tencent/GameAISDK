# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5 import QtWidgets

from ..tree.project_node import ProjectNode
from ...common.define import DEFAULT_MENU_WIDTH

logger = logging.getLogger("sdktool")


class MenuProject(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Project")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())
        self.action_new = None
        self.action_save = None
        self.action_load = None
        self.action_delete = None
        self.__project_node = ProjectNode()

    def define_action(self):
        self.action_new = QtWidgets.QAction()
        self.action_new.setObjectName("project_new")
        self.action_new.setText("New")
        self.action_new.setShortcut('Ctrl+N')
        self.action_new.setStatusTip("new project")
        self.__menu.addAction(self.action_new)

        self.action_save = QtWidgets.QAction()
        self.action_save.setObjectName("project_save")
        self.action_save.setText("Save")
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.setStatusTip("save project")
        self.__menu.addAction(self.action_save)

        self.action_load = QtWidgets.QAction()
        self.action_load.setObjectName("project_load")
        self.action_load.setText("Load")
        self.action_load.setShortcut("Ctrl+L")
        self.action_load.setStatusTip("load project")
        self.__menu.addAction(self.action_load)

    def set_slot(self, left_tree=None, right_tree=None):
        self.action_new.triggered.connect(lambda: self.__project_node.new_project(left_tree, right_tree))
        self.action_load.triggered.connect(lambda: self.__project_node.load_project(left_tree, right_tree))
        self.action_save.triggered.connect(self.__project_node.save_project)

    def set_sub_menu(self):
        pass
