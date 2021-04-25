# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox

from ....common.define import AI_ALGORITHM
from ....config_manager.ai.ai_manager import AIManager, AIType
from ...utils import create_tree_item, get_ai_node_by_type, ExecResult
from ...main_window.tool_window import ui

logger = logging.getLogger("sdktool")


algorithms = ['IM', 'DQN', 'RAINBOW']


class AlgorithmNode(QObject):
    clear_right_tree_signal = pyqtSignal(ExecResult)

    def __init__(self, action_node):
        super().__init__()
        self.__root_node = None
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        # 为了保证切换菜单算法的时候，对应的action Node数据发生变化
        self.__action_node = action_node

    def create_node(self):
        # 左树设置
        self.update_left_tree()

    def update_left_tree(self):
        # 查找 AI 节点
        self.__root_node, ai_node = get_ai_node_by_type(self.__left_tree, AI_ALGORITHM)
        if self.__root_node is None:
            self.__root_node = create_tree_item(key=AI_ALGORITHM, node_type=AI_ALGORITHM, edit=False)
            ai_node.addChild(self.__root_node)
            ai_node.setExpanded(True)
        return True

    def update_right_tree(self, algorithm_text=None):
        # 清空右树
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        if not result:
            logger.error("update failed")
            return False
        self.__right_tree.clear()
        node = QTreeWidgetItem(self.__right_tree)
        node.setText(0, AI_ALGORITHM)

        # 创建右树节点
        combobox = QComboBox()
        combobox.addItems(algorithms)
        if algorithm_text is None:
            combobox.setCurrentIndex(-1)
        else:
            combobox.setCurrentText(algorithm_text)

        combobox.currentTextChanged.connect(self._select_algorithm_text)
        self.__right_tree.setItemWidget(node, 1, combobox)
        return True

    def load(self, node):
        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()
        logger.debug("ai type is %s, node: %s", ai_type, node)
        if ai_type == AIType.IMITATION_AI.value:
            self.update_right_tree('IM')
        elif ai_type == AIType.DQN_AI.value:
            self.update_right_tree('DQN')
        elif ai_type == AIType.RAIN_BOW_AI.value:
            self.update_right_tree('RAINBOW')

    def _select_algorithm_text(self, text):
        current_node = self.__right_tree.currentItem()
        current_node.setText(1, text)
        ai_mgr = AIManager()

        # 优化：
        if text == 'IM':
            ai_mgr.set_ai_type(AIType.IMITATION_AI.value)
        elif text == 'DQN':
            ai_mgr.set_ai_type(AIType.DQN_AI.value)
        elif text == 'RAINBOW':
            ai_mgr.set_ai_type(AIType.RAIN_BOW_AI.value)

        self.__action_node.clear()
        self.__action_node.create_node()
