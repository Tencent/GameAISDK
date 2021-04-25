# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem

from ....common.define import DISABLE_EDIT_KEYS, TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG, ITEM_TYPE_UI_ROI
from ....context.app_context import AppContext
from .base_node import BaseNode, ui_type_map
from ...utils import show_critical_item, get_sub_nodes, create_tree_item
from ...canvas.ui_canvas import canvas, reset_canvas_roi, reset_canvas_action
from ...canvas.shape import Shape


logger = logging.getLogger("sdktool")


class OverUINode(BaseNode):
    def __init__(self, config=None, left_tree=None, right_tree=None):
        super().__init__(config=config, left_tree=left_tree, right_tree=right_tree)

    # def update_right_tree(self, config=None):
    #     self.right_tree.clear()
    #     for key, value in config.items():
    #         logger.debug("key %s, value %s", key, value)
    #         if isinstance(value, (str, int, float)):
    #             if key == 'actionType':
    #                 self.new_action_type(value=value, root=None)
    #             elif key == 'name':
    #                 node = QTreeWidgetItem(self.right_tree)
    #                 node.setText(0, key)
    #                 node.setText(1, str(value))
    #                 node.setText(2, ui_type_map.get(self._cfg.ui_type))
    #             else:
    #                 node = QTreeWidgetItem(self.right_tree)
    #                 node.setText(0, key)
    #                 node.setText(1, str(value))
    #                 if key not in DISABLE_EDIT_KEYS:
    #                     node.setFlags(node.flags() | Qt.ItemIsEditable)
    #
    #         elif isinstance(value, (dict, list)):
    #             self._create_complex_node(key=key, value=value, root=None)
    #
    #     nodes = self._get_top_level_nodes()
    #     for node in nodes:
    #         show_critical_item(node)

    def action_type_changed(self, text):
        logger.info("action type changed, current text is %s", text)
        # find 'action' node
        action_node = None
        sub_nodes = self._get_top_level_nodes()
        for cur_node in sub_nodes:
            if cur_node.text(0) in ['action']:
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
        return [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG]

    def is_action_valid(self, root=None):
        if root is None:
            nodes = self._get_top_level_nodes()
        else:
            nodes = get_sub_nodes(root)

        for node in nodes:
            if node.text(0) in ["action"]:
                # drag or click
                # if node.childCount() in [len(Drag_Key), len(Click_Key)]:
                sub_node1 = node.child(0)
                sub_node2 = node.child(1)
                if int(sub_node1.text(1)) == 0 and int(sub_node2.text(1)) == 0:
                    return False
        return True

    # def new_canvas_shapes(self, nodes=None):
    #     canvas.reset_shapes()
    #     canvas.shapes.clear()
    #     canvas.mode = canvas.CREATE
    #     if nodes is None:
    #         nodes = self._get_top_level_nodes()
    #     for node in nodes:
    #         if node.text(0) == "ROI":
    #             canvas.set_rect_tree_item(node)
    #             canvas.current_model.append(Shape.RECT)
    #             canvas.set_editing(False)
    #         elif node.text(0) == 'action':
    #             self._set_canvas_action(node)

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
                canvas.set_rect_tree_item(node)
                canvas.set_editing()
                shape = reset_canvas_roi(node)
                if shape is not None:
                    shapes.append(shape)
                    canvas.shape_tree[shape] = node

            elif key == 'actionType':
                action_type = node.text(1)

            elif key == 'action' and action_type in [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG]:
                actions.append(node)

            for action in actions:
                shape = reset_canvas_action(action)
                if shape is not None:
                    shapes.append(shape)

        canvas.load_shapes(shapes)
        canvas.update()

    # def _set_canvas_action(self, node):
    #     # find action type
    #     parent = node.parent()
    #     action_type = TYPE_UIACTION_CLICK
    #     if parent is not None:
    #         for sub_node_index in range(parent.childCount()):
    #             sub_node = parent.child(sub_node_index)
    #             if sub_node.text(0) == 'actionType':
    #                 action_type = sub_node.text(1)
    #                 break
    #     else:
    #         for sub_node_index in range(self.right_tree.topLevelItemCount()):
    #             sub_node = self.right_tree.topLevelItem(sub_node_index)
    #             if sub_node.text(0) == 'actionType':
    #                 action_type = sub_node.text(1)
    #                 break
    #
    #     # various 'action type' with diff canvas model
    #     if node.text(0) == 'action' and action_type in [TYPE_UIACTION_CLICK]:
    #         canvas.set_editing(False)
    #         canvas.current_model.append(Shape.POINT)
    #         canvas.set_point_tree_item(node)
    #
    #     elif node.text(0) == 'action' and action_type in [TYPE_UIACTION_DRAG]:
    #         canvas.set_editing(False)
    #         canvas.current_model.append(Shape.LINE)
    #         canvas.set_line_tree_item(node)
    #     else:
    #         logger.error("unknown action type %s", action_type)

    # def _create_complex_node(self, key, value, root=None):
    #     logger.debug("create complex node key %s, value %s, root is %s", key, value, root)
    #     edit_flag = True
    #     if key in DISABLE_EDIT_KEYS:
    #         edit_flag = False
    #
    #     if isinstance(value, (int, float)):
    #         if root is None:
    #             sub_node = QTreeWidgetItem(self.right_tree)
    #             sub_node.setText(0, key)
    #             sub_node.setText(1, str(value))
    #             if edit_flag:
    #                 sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)
    #         else:
    #             sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
    #             root.addChild(sub_node)
    #
    #     elif isinstance(value, str):
    #         if key == 'actionType':
    #             self.new_action_type(value=value, root=root)
    #         else:
    #             sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
    #             root.addChild(sub_node)
    #
    #     elif isinstance(value, dict):
    #         # ui_type = None
    #         if root is None:
    #             sub_root_node = QTreeWidgetItem(self.right_tree)
    #             sub_root_node.setText(0, key)
    #             # sub_root_node.setText(2, ui_type)
    #         else:
    #             sub_root_node = create_tree_item(key=key)
    #             root.addChild(sub_root_node)
    #
    #         for sub_key, sub_value in value.items():
    #             self._create_complex_node(key=sub_key, value=sub_value, root=sub_root_node)
    #         sub_root_node.setExpanded(True)
    #
    #     elif isinstance(value, list):
    #         ui_type = None
    #         for sub_value in value:
    #             if key == 'ROI':
    #                 ui_type = ITEM_TYPE_UI_ROI
    #             if root is None:
    #                 sub_root_node = QTreeWidgetItem(self.right_tree)
    #                 sub_root_node.setText(0, key)
    #                 sub_root_node.setText(2, ui_type)
    #             else:
    #                 sub_root_node = create_tree_item(key=key, node_type=ui_type)
    #                 root.addChild(sub_root_node)
    #             # x,y,w,h.....
    #             for roi_key, roi_value in sub_value.items():
    #                 self._create_complex_node(key=roi_key, value=roi_value, root=sub_root_node)
    #             sub_root_node.setExpanded(True)
