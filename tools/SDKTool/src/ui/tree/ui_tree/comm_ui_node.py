# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt

from ....context.app_context import AppContext
from ...tree.ui_tree.base_node import BaseNode
from ...utils import get_sub_nodes, create_tree_item
from ...canvas.ui_canvas import canvas, reset_canvas_roi, reset_canvas_action
from ....common.define import TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG, TYPE_UIACTION_SCRIPT, \
    TYPE_UIACTION_DRAGCHECK, ITEM_TYPE_UI_SCRIPT_TASK, ITEM_TYPE_UI_SCRIPT_TASKS, Drag_Key, \
    Click_Key
from ...dialog.tip_dialog import show_warning_tips

logger = logging.getLogger("sdktool")


class CommUINode(BaseNode):
    def __init__(self, config=None, left_tree=None, right_tree=None):
        super().__init__(config=config, left_tree=left_tree, right_tree=right_tree)
        self.__template_number = 0

    def action_dir_changed(self, text):
        # find 'actionDir' node
        dir_node = None
        nodes = self._get_top_level_nodes()
        for node in nodes:
            logger.debug("text 0 %s", node.text(0))
            if node.text(0) == 'action':
                for sub_index in range(node.childCount()):
                    sub_node = node.child(sub_index)
                    if sub_node.text(0) == 'actionDir':
                        dir_node = sub_node
                break
        if dir_node is None:
            logger.error("find action node action failed")
            return

        dir_node.setText(1, text)

    def action_type_changed(self, text):
        logger.info("action type changed, current text is %s", text)
        cur_node = self.right_tree.currentItem()
        parent = cur_node.parent()
        # find 'action' node
        action_node = None
        sub_nodes = []
        if parent is not None:
            sub_nodes = get_sub_nodes(parent)
            for cur_node in sub_nodes:
                logger.debug("text 0 %s", cur_node.text(0))
                if cur_node.text(0) in ['action', 'tasks']:
                    action_node = cur_node
                    break
        else:
            sub_nodes = self._get_top_level_nodes()
            for cur_node in sub_nodes:
                if cur_node.text(0) in ['action', 'tasks']:
                    action_node = cur_node
                    break

        if action_node is None:
            logger.error("find action node action failed")
            return

        for _ in range(action_node.childCount()):
            action_node.takeChild(0)

        action_node.setText(0, 'action')
        action_node.setText(2, '')
        # generate new action ui_node
        action_node_cfg = None
        if text == TYPE_UIACTION_CLICK:
            action_node_cfg = self._cfg.init_click_action()

        elif text == TYPE_UIACTION_DRAG:
            action_node_cfg = self._cfg.init_drag_action()

        elif text == TYPE_UIACTION_SCRIPT:
            action_node_cfg = self._cfg.init_script_action()
            action_node.setText(0, 'tasks')
            action_node.setText(2, ITEM_TYPE_UI_SCRIPT_TASKS)

        elif text == TYPE_UIACTION_DRAGCHECK:
            action_node_cfg = self._cfg.init_drag_check_action()

        if action_node_cfg is None:
            logger.error("action node ui_node is None")
            return

        # create new children of 'action' node
        for key, value in action_node_cfg.items():
            self._create_complex_node(key=key, value=value, root=action_node)

        action_type_node = None
        for cur_node in sub_nodes:
            if cur_node.text(0) == 'actionType':
                action_type_node = cur_node
                break

        if action_type_node is None:
            logger.error("find action type node action failed")
            return

        action_type_node.setText(1, text)

        self.new_canvas_shapes(nodes=sub_nodes)

    def get_action_type(self):
        types = [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG, TYPE_UIACTION_DRAGCHECK, TYPE_UIACTION_SCRIPT]
        right_item = self.right_tree.currentItem()
        if right_item is None:
            return types
        if right_item.text(0) in ['tasks']:
            return [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG]
        return types

    def template_edit_changed(self, text):
        template_node = None
        nodes = self._get_top_level_nodes()
        for node in nodes:
            if node.text(0) == 'template':
                template_node = node
                break

        if template_node is None:
            logger.error("find template node action failed")
            return
        template_node.setText(1, text)

    def template_edit_finished(self):
        # 可能是删除template这一项时，导致的template_edit_finished被触发，此时不处理
        top_node = self.right_tree.topLevelItem(0)
        if top_node is None:
            return
        if top_node.text(0) != 'name':
            return

        template_node = self.right_tree.currentItem()
        if not template_node:
            return
        try:
            number = int(template_node.text(1))
        except ValueError:
            show_warning_tips('必须是>=0的整数值')
            template_node.setText(1, '0')
            return

        self._cfg.save_element(self.right_tree)
        config = self._cfg.add_template_roi(self._cfg.get_config(), number)
        self.update_right_tree(config=config)

        self.new_canvas_shapes()

    def is_action_valid(self, root=None):
        if root is None:
            nodes = self._get_top_level_nodes()
        else:
            nodes = get_sub_nodes(root)

        for node in nodes:
            if node.text(0) in ["action", "dragPoint"]:
                # drag or click
                if node.childCount() in [len(Drag_Key), len(Click_Key)] and \
                        int(node.child(0).text(1)) == 0 and int(node.child(1).text(1)) == 0:
                    return False
                for sub_node_index in range(node.childCount()):
                    sub_node = node.child(sub_node_index)
                    if sub_node.text(0) == 'dragPoint' and int(sub_node.child(0).text(1)) == 0 and \
                            int(sub_node.child(1).text(1)) == 0:
                        return False
        return True

    @staticmethod
    def _load_roi_check(node, shapes):
        canvas.set_rect_tree_item(node)
        canvas.set_editing()
        shape = reset_canvas_roi(node)
        if shape:
            shapes.append(shape)
            canvas.shape_tree[shape] = node

    @staticmethod
    def _load_task_check(node, actions):
        for sub_node_index in range(node.childCount()):
            sub_node = node.child(sub_node_index)
            if sub_node.text(0) == 'task':
                for ss_node_index in range(sub_node.childCount()):
                    ss_node = sub_node.child(ss_node_index)
                    if ss_node.text(1) == 'action':
                        actions.append(ss_node)

    def load_canvas_shapes(self, nodes=None):
        app_ctx = AppContext()
        app_ctx.set_info("phone", False)
        shapes = []
        action_type = TYPE_UIACTION_CLICK
        if nodes is None:
            nodes = self._get_top_level_nodes()
        for node in nodes:
            actions = []
            key = node.text(0)
            if key == 'ROI':
                self._load_roi_check(node, shapes)
            elif key == 'actionType':
                action_type = node.text(1)

            elif key == 'action' and action_type in [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG]:
                actions.append(node)

            elif key == 'action' and action_type in [TYPE_UIACTION_DRAGCHECK]:
                for sub_node_index in range(node.childCount()):
                    sub_node = node.child(sub_node_index)
                    if sub_node.text(0) == 'dragPoint':
                        actions.append(sub_node)
            elif key in ['tasks']:
                self._load_task_check(node, actions)

            for action in actions:
                shape = reset_canvas_action(action)
                if shape is not None:
                    shapes.append(shape)

        canvas.load_shapes(shapes)
        canvas.update()

    def create_template_number(self, value=None, root=None):
        if root is None:
            template_node = QTreeWidgetItem(self.right_tree)
            template_node.setText(0, 'template')
            template_node.setText(1, str(value))
            template_node.setFlags(template_node.flags() | Qt.ItemIsEditable)
        else:
            template_node = create_tree_item(key='template', value=value, edit=True)
            root.addChild(template_node)

    def create_template_op(self, value=None, root=None):
        if root is None:
            template_node = QTreeWidgetItem(self.right_tree)
            template_node.setText(0, 'templateOp')
        else:
            template_node = create_tree_item(key='templateOp')
            root.addChild(template_node)

        logger.debug("template op text %s", value)
        template_node.setText(1, value)

        combobox = QtWidgets.QComboBox()
        combobox.addItems([
            'and',
            'or'
        ])
        combobox.setCurrentText(value)
        combobox.currentTextChanged.connect(self._save_template_op)
        self.right_tree.setItemWidget(template_node, 1, combobox)

    def new_task_node(self, root):
        script_item = self._cfg.init_script_click_action()
        sub_task = create_tree_item(key='task', node_type=ITEM_TYPE_UI_SCRIPT_TASK)
        root.addChild(sub_task)
        root.setExpanded(True)
        for key, value in script_item.items():
            if key == 'taskid':
                value = self._get_task_id()
            self._create_complex_node(key=key, value=value, root=sub_task)
        sub_task.setExpanded(True)

    def _get_task_id(self):
        new_task_id = 1
        current_node = self.right_tree.currentItem()
        if current_node.text(0) != 'tasks':
            logger.error("key is %s not tasks", current_node.text(0))
            return new_task_id
        for index in range(current_node.childCount()):
            sub_node = current_node.child(index)
            if sub_node.text(0) == 'task':
                for ss_node_index in range(sub_node.childCount()):
                    ss_node = sub_node.child(ss_node_index)
                    if ss_node.text(0) == 'taskid':
                        if new_task_id <= int(ss_node.text(1)):
                            new_task_id = int(ss_node.text(1)) + 1
        logger.info("new task id is %s", new_task_id)
        return new_task_id

    def _save_template_op(self, text):
        item = self.right_tree.currentItem()
        item.setText(1, text)
