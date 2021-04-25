# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMenu

from ..debug.debug_factory import DebugFactory
from ..utils import set_log_text
from ...common.define import DEFAULT_MENU_WIDTH, DebugType


class MenuDebug(object):
    def __init__(self, menu_bar):
        self.__menu = QtWidgets.QMenu(menu_bar)
        self.__menu.setTitle("Debug")
        self.__menu.setMinimumWidth(DEFAULT_MENU_WIDTH)
        menu_bar.addAction(self.__menu.menuAction())

        self.menu_debug_scene = None
        self.menu_debug_UI = None
        self.action_scene_start = None
        self.action_scene_stop = None
        self.action_UI_start = None
        self.action_UI_stop = None

    def define_action(self):
        self.menu_debug_scene = QMenu()
        self.menu_debug_scene.setTitle("GameReg")
        self.menu_debug_scene.setMinimumWidth(DEFAULT_MENU_WIDTH)
        self.__menu.addMenu(self.menu_debug_scene)

        self.action_scene_start = QtWidgets.QAction()
        self.action_scene_start.setText("Start")
        self.menu_debug_scene.addAction(self.action_scene_start)

        self.action_scene_stop = QtWidgets.QAction()
        self.action_scene_stop.setText("Stop")
        self.menu_debug_scene.addAction(self.action_scene_stop)

        self.menu_debug_UI = QMenu()
        self.menu_debug_UI.setTitle("UI")
        self.menu_debug_UI.setMinimumWidth(DEFAULT_MENU_WIDTH)
        self.__menu.addMenu(self.menu_debug_UI)

        self.action_UI_start = QtWidgets.QAction()
        self.action_UI_start.setText("start")
        self.menu_debug_UI.addAction(self.action_UI_start)

        self.action_UI_stop = QtWidgets.QAction()
        self.action_UI_stop.setText("stop")
        self.menu_debug_UI.addAction(self.action_UI_stop)

    def set_slot(self, left_root=None, right_root=None):
        self.action_scene_start.triggered.connect(self.start_debug_game_reg)
        self.action_scene_stop.triggered.connect(self.stop_debug_game_reg)
        self.action_UI_start.triggered.connect(self.start_debug_ui)
        self.action_UI_stop.triggered.connect(self.stop_debug_ui)

    @staticmethod
    def start_debug_game_reg():
        factory = DebugFactory()
        debug_type = factory.get_debug_type()
        if debug_type is None:
            factory.initialize(DebugType.GameReg)
            instance = factory.get_product_instance()

            if instance.start_test():
                set_log_text("running debug gameReg module")
            else:
                instance.stop_test()
                factory.set_debug_type(None)

        elif debug_type == DebugType.UI:
            set_log_text("please stop debug UI module first")

    @staticmethod
    def stop_debug_game_reg():
        factory = DebugFactory()
        debug_type = factory.get_debug_type()
        if debug_type != DebugType.GameReg:
            set_log_text("not start debug GameReg module")
            return

        set_log_text("stop debug GameReg module")
        instance = factory.get_product_instance()
        instance.stop_test()
        factory.set_debug_type(None)

    @staticmethod
    def start_debug_ui():
        factory = DebugFactory()
        debug_type = factory.get_debug_type()
        if debug_type is None:
            factory.initialize(DebugType.UI)
            instance = factory.get_product_instance()
            if instance.start_test():
                set_log_text("running debug UI")
            else:
                instance.stop_test()
                factory.set_debug_type(None)

        elif debug_type == DebugType.GameReg:
            set_log_text("please stop debug GameReg  first")

    @staticmethod
    def stop_debug_ui():
        factory = DebugFactory()
        debug_type = factory.get_debug_type()
        if debug_type != DebugType.UI:
            set_log_text("not start debug UI")
            return

        set_log_text("stop debug UI")
        instance = factory.get_product_instance()
        instance.stop_test()
        factory.set_debug_type(None)
