# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets

from ..tree.ai_tree.ai_tree import AITree
from ...common.define import DEFAULT_MENU_WIDTH


class MenuAI(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("AI")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_new = QtWidgets.QAction()
        self.action_new.setText("New")
        self.action_new.setShortcut('Ctrl+Shift+E')

        self.__ai_tree = AITree()

    def define_action(self):
        self.__menu.addAction(self.action_new)

    def set_slot(self, left_root=None, right_root=None):
        self.action_new.triggered.connect(self.__ai_tree.new_node)

    def set_sub_menu(self):
        pass
