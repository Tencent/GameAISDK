# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets

from ..tree.ui_tree.ui_tree import UITree
from ...common.define import DEFAULT_MENU_WIDTH


class MenuUI(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("UI")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.action_new = QtWidgets.QAction()
        self.action_new.setText("New")
        self.action_new.setShortcut('Ctrl+Shift+N')

        self.action_add_element = QtWidgets.QAction()
        self.action_add_element.setText("Add Element")
        self.action_add_element.setShortcut('Ctrl+A')

        self.action_del_element = QtWidgets.QAction()
        self.action_del_element.setText("Delete Element")
        self.action_del_element.setShortcut('Ctrl+D')

        self.ui_tree = UITree()

    def define_action(self):
        self.__menu.addAction(self.action_new)
        self.__menu.addAction(self.action_add_element)
        self.__menu.addAction(self.action_del_element)

    def set_slot(self, left_tree=None, right_tree=None):
        self.action_new.triggered.connect(self.ui_tree.new_ui)
        self.action_add_element.triggered.connect(self.ui_tree.check_add_element)
        self.action_del_element.triggered.connect(lambda: self.ui_tree.delete_element(left_tree))

    def set_sub_menu(self):
        pass
