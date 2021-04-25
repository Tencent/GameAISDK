# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from .menu_debug import MenuDebug
from .menu_plugin import MenuPlugin
from .menu_scene import MenuScene
from .menu_project import MenuProject
from .menu_ui import MenuUI
from .menu_ai import MenuAI
from .menu_run import MenuRun
from .menu_applications import MenuApplications
from .menu_utils import MenuPackLog


class OpMenu(object):
    def __init__(self, menu):
        self.__menu = menu
        self.__menu_list = []
        self.__menu_list.append(MenuProject(menu))
        self.__menu_list.append(MenuUI(menu))
        self.__menu_list.append(MenuScene(menu))
        self.__menu_list.append(MenuAI(menu))
        self.__menu_list.append(MenuRun(menu))
        self.__menu_list.append(MenuPlugin(menu))
        self.__menu_list.append(MenuDebug(menu))
        self.__menu_list.append(MenuApplications(menu))
        self.__menu_list.append(MenuPackLog(menu))

    def define_action(self):
        for sub_menu in self.__menu_list:
            sub_menu.define_action()

    def set_slot(self, left_tree=None, right_tree=None):
        for sub_menu in self.__menu_list:
            sub_menu.set_slot(left_tree, right_tree)
