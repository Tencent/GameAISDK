# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets
from ...common.define import DEFAULT_MENU_WIDTH


class MenuPlugin(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Plugin")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

    def define_action(self):
        pass

    def set_slot(self, left_root=None, right_root=None):
        pass

    def set_sub_menu(self):
        pass
