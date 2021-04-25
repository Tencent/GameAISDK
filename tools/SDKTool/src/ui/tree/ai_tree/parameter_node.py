# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox

from ....common.define import AI_NAME, AI_PARAMETER, AI_MODEL_PARAMETER, BOOL_FLAGS, VALID_RATIO
from ....config_manager.ai.ai_manager import AIManager, AIType
from ....config_manager.task.task_manager import TaskManager
from ...dialog.tip_dialog import show_warning_tips
from ...tree.ai_tree.im_parameter import IMParameter
from ...tree.ai_tree.dqn_parameter import DQNParameter
from ...tree.ai_tree.rain_bow_parameter import RainbowParameter
from ...utils import get_sub_nodes, create_tree_item, get_tree_top_nodes, save_action, ExecResult
from ...main_window.tool_window import ui


logger = logging.getLogger("sdktool")


class ParameterNode(QObject):
    clear_right_tree_signal = pyqtSignal(ExecResult)

    def __init__(self):
        super().__init__()
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__model_param_node = None
        self.__im_parameter = IMParameter()
        self.__dqn_parameter = DQNParameter()
        self.__rain_bow_parameter = RainbowParameter()
        self.__ai_tree = None

    def set_ai_tree(self, ai_tree):
        self.__ai_tree = ai_tree

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

        nodes = get_sub_nodes(project_node)
        ai_node = None
        for node in nodes:
            if node.text(0) == AI_NAME:
                ai_node = node
                break

        if ai_node is None:
            ai_node = create_tree_item(key='AI', edit=False)
            project_node.addChild(ai_node)
            project_node.setExpanded(True)

        sub_nodes = get_sub_nodes(ai_node)

        # 查找AI_PARAMETERS节点
        parameter_node = None
        for node in sub_nodes:
            if node.text(0) == AI_PARAMETER:
                parameter_node = node
                break

        if parameter_node is None:
            parameter_node = create_tree_item(key=AI_PARAMETER, edit=False)
            ai_node.addChild(parameter_node)
            ai_node.setExpanded(True)

        # 查找 AI_MODEL_PARAMETER
        sub_nodes = get_sub_nodes(parameter_node)
        for node in sub_nodes:
            if None not in [self.__model_param_node]:
                break

            if node.text(0) == AI_MODEL_PARAMETER:
                self.__model_param_node = node

        if self.__model_param_node is None:
            self.__model_param_node = create_tree_item(key=AI_MODEL_PARAMETER, node_type=AI_MODEL_PARAMETER, edit=False)
            parameter_node.addChild(self.__model_param_node)
            parameter_node.setExpanded(True)

    def create_im_parameter_item(self):
        if not self.__im_parameter.init():
            logger.error("im parameter init failed")
            return

        parameters = self.__im_parameter.get_parameters()
        self._create_parameter_items(parameters)

    def create_dqn_parameter_item(self):
        if not self.__dqn_parameter.init():
            logger.error("dqn parameter init failed")
            return

        parameters = self.__dqn_parameter.get_parameters()
        self._create_parameter_items(parameters)

    def create_rain_bow_parameter_item(self):
        if not self.__rain_bow_parameter.init():
            logger.error("rainbow parameter init failed")
            return

        parameters = self.__rain_bow_parameter.get_parameters()
        self._create_parameter_items(parameters)

    def _create_parameter_items(self, parameters):
        """ 在右树创建参数节点

        :param parameters:
        :return:
        """

        for key, value in parameters.items():
            self.create_complex_node(key=key, value=value)

        # 默认显示"roiRegion/path"对应的图片
        if self.__right_tree is None:
            return

        topLevelItemCount = self.__right_tree.topLevelItemCount()
        for k in range(topLevelItemCount):
            topLevelItem = self.__right_tree.topLevelItem(k)
            node_text = topLevelItem.text(0)
            if node_text == 'roiRegion':
                if self.__ai_tree:
                    self.__right_tree.setCurrentItem(topLevelItem)
                    self.__ai_tree.double_click_right_tree(topLevelItem, None)

    def create_complex_node(self, key, value, root=None):
        class NoWheelEventComboBox(QComboBox):
            def wheelEvent(self, evt):
                pass
        # 0: key, 1:value, 2:type
        if root is None:
            sub_node = QTreeWidgetItem(self.__right_tree)
            sub_node.setText(0, key)
        else:
            sub_node = create_tree_item(key=key, edit=False)
            root.addChild(sub_node)
            root.setExpanded(True)

        if isinstance(value, bool):
            combobox = QComboBox()
            combobox.addItems(BOOL_FLAGS)
            combobox.setCurrentText(str(value))
            combobox.currentTextChanged.connect(self._text_changed)
            sub_node.setText(1, str(value))
            self.__right_tree.setItemWidget(sub_node, 1, combobox)

        elif isinstance(value, (int, float, str)):
            logger.debug("value %s type str", value)
            if key == 'validDataRatio':
                combobox = QComboBox()
                combobox.addItems(VALID_RATIO)
                combobox.setCurrentText(str(value))
                combobox.currentTextChanged.connect(self._text_changed)
                self.__right_tree.setItemWidget(sub_node, 1, combobox)
                sub_node.setText(1, str(value))

            sub_node.setText(1, str(value))
            if key != 'dataDir':
                sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)

            if key in ['startTaskID', 'scoreTaskID', 'winTaskID', 'loseTaskID']:
                combobox = NoWheelEventComboBox()  # 去除响应鼠标滚动事件，避免无意修改数值
                task_manager = TaskManager()
                task = task_manager.get_task()
                task_names = [sub_task[1] for sub_task in task.get_all()]

                # 无任务task时选择此项
                task_text = ''
                task_names.append(task_text)
                combobox.addItems(task_names)
                sub_node.setText(1, self.__get_task_name(value))
                combobox.setCurrentText(self.__get_task_name(value))
                combobox.currentTextChanged.connect(self._text_changed)
                self.__right_tree.setItemWidget(sub_node, 1, combobox)

        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                self.create_complex_node(key=sub_key, value=sub_value, root=sub_node)

            sub_node.setExpanded(True)

    @staticmethod
    def __get_task_name(value):
        task_manager = TaskManager()
        task = task_manager.get_task()
        for sub_task in task.get_all():
            if sub_task[0] == value:
                return sub_task[1]
        return ""

    def update_left_tree(self):
        pass

    def load_model_parameter(self):
        self.__right_tree.clear()
        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()

        if ai_type == AIType.IMITATION_AI.value:
            self.create_im_parameter_item()

        elif ai_type == AIType.DQN_AI.value:
            self.create_dqn_parameter_item()

        elif ai_type == AIType.RAIN_BOW_AI.value:
            self.create_rain_bow_parameter_item()

    def _text_changed(self, text):
        current_item = self.__right_tree.currentItem()
        current_item.setText(1, text)

    def save_parameter(self):
        out_params = OrderedDict()
        top_nodes = get_tree_top_nodes(self.__right_tree)
        for node in top_nodes:
            key = node.text(0)
            if node.childCount() == 0:
                value = node.text(1)
                out_params[key] = value
            else:
                out_params[key] = save_action(node)

        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()
        if ai_type == AIType.IMITATION_AI.value:
            self.__im_parameter.save_parameter(out_params)

        elif ai_type == AIType.DQN_AI.value:
            self.__dqn_parameter.save_parameter(out_params)

        elif ai_type == AIType.RAIN_BOW_AI.value:
            self.__rain_bow_parameter.save_parameter(out_params)

        is_ok, check_content, _ = ai_mgr.check_learning_config()
        if not is_ok:
            show_warning_tips('Task数值无效，请在(%s)重新配置' % check_content)
