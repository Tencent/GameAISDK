# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import QObject, pyqtSignal, Qt

from ...utils import get_tree_top_nodes, create_tree_item, get_ai_node_by_type, ExecResult
from ...main_window.tool_window import ui
from ....config_manager.ai.ai_manager import AIManager
from ....common.define import AI_RESOLUTION

logger = logging.getLogger("sdktool")


class ResolutionNode(QObject):
    clear_right_tree_signal = pyqtSignal(ExecResult)

    def __init__(self):
        super().__init__()
        self.__root_node = None
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__resolution = None

    def create_node(self):
        # 左树设置
        self.update_left_tree()

    def update_left_tree(self):
        # 查找 AI 节点
        self.__root_node, ai_node = get_ai_node_by_type(self.__left_tree, AI_RESOLUTION)
        if self.__root_node is None:
            self.__root_node = create_tree_item(key=AI_RESOLUTION, node_type=AI_RESOLUTION, edit=False)
            ai_node.addChild(self.__root_node)
            ai_node.setExpanded(True)
        return True

    def __get_solution(self):
        ai_mgr = AIManager()
        self.__resolution = ai_mgr.get_resolution(ai_mgr.get_ai_type())
        return self.__resolution

    def save_resolution(self):
        top_nodes = get_tree_top_nodes(self.__right_tree)
        for node in top_nodes:
            key = node.text(0)
            value = int(node.text(1))
            if key == 'screenWidth':
                self.__get_solution().set_screen_width(value)
            elif key == 'screenHeight':
                self.__get_solution().set_screen_height(value)

    def load_resolution(self):
        # result = ExecResult()
        # self.clear_right_tree_signal.emit(result)
        # if not result:
        #     logger.error("update failed")
        #     return False

        self.__right_tree.clear()
        screen_width_node = QTreeWidgetItem(self.__right_tree)
        screen_height_node = QTreeWidgetItem(self.__right_tree)
        screen_width = 0
        screen_height = 0
        resolution = self.__get_solution()
        if resolution.get_screen_width() is not None:
            screen_width = resolution.get_screen_width()
        if resolution.get_screen_height() is not None:
            screen_height = resolution.get_screen_height()

        screen_width_node.setText(0, 'screenWidth')
        screen_width_node.setText(1, str(screen_width))
        screen_width_node.setFlags(screen_width_node.flags() | Qt.ItemIsEditable)
        screen_height_node.setText(0, 'screenHeight')
        screen_height_node.setText(1, str(screen_height))
        screen_height_node.setFlags(screen_height_node.flags() | Qt.ItemIsEditable)
