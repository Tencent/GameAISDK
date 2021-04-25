# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets

from ..tree.scene_tree.scene_tree import SceneTree
from ...common.define import DEFAULT_MENU_WIDTH


class MenuScene(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Scene")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_new = QtWidgets.QAction()
        self.action_new.setText("New")
        self.action_new.setShortcut('Ctrl+Shift+S')

        self.action_new_task = QtWidgets.QAction()
        self.action_new_task.setText("Add Task")
        self.action_new_task.setShortcut('Ctrl+Shift+A')

        self.action_del_task = QtWidgets.QAction()
        self.action_del_task.setText("Delete Task")
        self.action_del_task.setShortcut('Ctrl+Shift+D')

        self.__tree = SceneTree()

    def define_action(self):
        self.__menu.addAction(self.action_new)
        self.__menu.addAction(self.action_new_task)
        self.__menu.addAction(self.action_del_task)

    def set_slot(self, left_root=None, right_root=None):
        self.action_new.triggered.connect(self.__tree.new_scene)
        self.action_del_task.triggered.connect(self.__tree.del_task)
        self.action_new_task.triggered.connect(self.__tree.new_task)

    def set_sub_menu(self):
        pass
