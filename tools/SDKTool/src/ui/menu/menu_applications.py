# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets

from ..tree.applications_tree.apps_tree import AppTree
from ...common.define import DEFAULT_MENU_WIDTH


class MenuApplications(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Applications")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_ui_explore = QtWidgets.QAction("UIAutoExplore")
        self.action_ui_explore.setText("UIAutoExplore")
        self.__apps_tree = AppTree()

    def define_action(self):
        self.__menu.addAction(self.action_ui_explore)

    def set_slot(self, left_root=None, right_root=None):
        self.action_ui_explore.triggered.connect(self.__apps_tree.new_ui_explore_node)

    def set_sub_menu(self):
        pass
