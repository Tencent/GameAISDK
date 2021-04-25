# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets

from ..tree.run_tree.run_tree import RunTree
from ...common.define import DEFAULT_MENU_WIDTH


class MenuRun(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Run")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_train = QtWidgets.QAction()
        self.action_train.setText("Train")

        self.action_test = QtWidgets.QAction()
        self.action_test.setText("Test")

        self.__run_tree = RunTree()

    def define_action(self):
        self.__menu.addAction(self.action_train)
        self.__menu.addAction(self.action_test)

    def set_slot(self, left_root=None, right_root=None):

        self.action_train.triggered.connect(self.__run_tree.new_train_node)
        self.action_test.triggered.connect(self.__run_tree.new_test_node)

    def set_sub_menu(self):
        pass
