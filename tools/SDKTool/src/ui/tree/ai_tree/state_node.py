# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem

from ....common.define import AI_NAME, AI_GAME_STATE, AI_GAME_BEGIN, AI_GAME_OVER
from ....config_manager.ai.ai_manager import AIManager
from ....config_manager.task.task_manager import TaskManager
from ...dialog.tip_dialog import show_warning_tips
from ...utils import get_tree_top_nodes, get_sub_nodes, create_tree_item, ExecResult
from ...main_window.tool_window import ui


logger = logging.getLogger("sdktool")


class StateNode(QObject):
    clear_right_tree_signal = pyqtSignal(ExecResult)

    def __init__(self):
        super().__init__()
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__game_begin_node = None
        self.__game_over_node = None

    def create_node(self):
        # 查找 AI 节点
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        if not result.flag:
            logger.error("create node failed")
            return

        project_node = self.__left_tree.topLevelItem(0)
        if len(project_node.text(0)) == 0:
            show_warning_tips("please new project first")
            return

        ai_node = None
        nodes = get_sub_nodes(project_node)
        for node in nodes:
            if node.text(0) == AI_NAME:
                ai_node = node
                break

        if ai_node is None:
            ai_node = create_tree_item(key='AI', edit=False)
            project_node.addChild(ai_node)
            project_node.setExpanded(True)

        sub_nodes = get_sub_nodes(ai_node)
        # 查找AI_STATE节点
        state_node = None
        for node in sub_nodes:
            if node.text(0) == AI_GAME_STATE:
                state_node = node
                break

        if state_node is None:
            state_node = create_tree_item(key=AI_GAME_STATE, edit=False)
            ai_node.addChild(state_node)
            ai_node.setExpanded(True)

        sub_nodes = get_sub_nodes(state_node)
        for sub_node in sub_nodes:
            if None not in [self.__game_begin_node, self.__game_over_node]:
                break

            if sub_node.text(0) == AI_GAME_BEGIN:
                self.__game_begin_node = sub_node

            if sub_node.text(0) == AI_GAME_OVER:
                self.__game_over_node = sub_node

        if self.__game_begin_node is None:
            self.__game_begin_node = create_tree_item(key=AI_GAME_BEGIN, node_type=AI_GAME_BEGIN, edit=False)
            state_node.addChild(self.__game_begin_node)
            state_node.setExpanded(True)
        if self.__game_over_node is None:
            self.__game_over_node = create_tree_item(key=AI_GAME_OVER, node_type=AI_GAME_OVER, edit=False)
            state_node.addChild(self.__game_over_node)
            state_node.setExpanded(True)

    def update_left_tree(self):
        pass

    def update_right_tree(self, task_ids):
        """ 根据task_ids更新右树的task是否勾选

        :param task_ids:
        :return:
        """
        self.__right_tree.clear()
        task_manager = TaskManager()
        task = task_manager.get_task()
        all_task = task.get_all()
        for sub_task in all_task:
            item = QTreeWidgetItem(self.__right_tree)
            item.setText(0, sub_task[1])
            item.setText(1, str(sub_task[0]))
            if sub_task[0] in task_ids:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)

    def load_game_begin(self):
        task_ids = self._get_game_state().get_begin_task_id()
        self.update_right_tree(task_ids)

    def load_game_over(self):
        task_ids = self._get_game_state().get_over_task_id()
        self.update_right_tree(task_ids)

    def save_game_begin(self):
        top_level_nodes = get_tree_top_nodes(self.__right_tree)
        task_ids = []
        for node in top_level_nodes:
            # 记录被选中的task id
            if node.checkState(0) == Qt.Checked:
                action_id = int(node.text(1))
                task_ids.append(action_id)
        self._get_game_state().set_begin_task_id(task_ids)

    def save_game_over(self):
        top_level_nodes = get_tree_top_nodes(self.__right_tree)
        task_ids = []
        for node in top_level_nodes:
            # 记录被选中的task id
            if node.checkState(0) == Qt.Checked:
                action_id = int(node.text(1))
                task_ids.append(action_id)
        self._get_game_state().set_over_task_id(task_ids)

    @staticmethod
    def _get_game_state():
        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()
        return ai_mgr.get_game_state(ai_type)
