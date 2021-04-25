# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt

from ....common.define import DISABLE_EDIT_KEYS, ITEM_TYPE_UI_ROI
from ....context.app_context import AppContext
from .base_node import BaseNode, ui_type_map
from ...utils import show_critical_item, create_tree_item
from ...canvas.ui_canvas import canvas, reset_canvas_roi
from ...canvas.shape import Shape

logger = logging.getLogger("sdktool")


class POPUINode(BaseNode):
    def __init__(self, config=None, left_tree=None, right_tree=None):
        super().__init__(config=config, left_tree=left_tree, right_tree=right_tree)

    # def update_right_tree(self, config=None):
    #     self.right_tree.clear()
    #
    #     for key, value in config.items():
    #         edit_flag = True
    #         if key in DISABLE_EDIT_KEYS:
    #             edit_flag = False
    #
    #         logger.debug("key %s, value %s", key, value)
    #         if isinstance(value, (str, int, float)):
    #             if key == 'name':
    #                 node = QTreeWidgetItem(self.right_tree)
    #                 node.setText(0, key)
    #                 node.setText(1, str(value))
    #                 node.setText(2, ui_type_map.get(self._cfg.ui_type))
    #             else:
    #                 node = QTreeWidgetItem(self.right_tree)
    #                 node.setText(0, key)
    #                 node.setText(1, str(value))
    #                 if edit_flag:
    #                     node.setFlags(node.flags() | Qt.ItemIsEditable)
    #
    #         elif isinstance(value, (dict, list)):
    #             self._create_complex_node(key=key, value=value, root=None)
    #
    #     nodes = self._get_top_level_nodes()
    #     for node in nodes:
    #         show_critical_item(node)

    def new_canvas_shapes(self, nodes=None):
        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.mode = canvas.CREATE
        if nodes is None:
            nodes = self._get_top_level_nodes()
        for node in nodes:
            if node.text(0) == "ROI":
                canvas.set_rect_tree_item(node)
                canvas.current_model.append(Shape.RECT)
                canvas.set_editing(False)

    def load_canvas_shapes(self, nodes=None):
        app_ctx = AppContext()
        app_ctx.set_info("phone", False)
        shapes = []
        if nodes is None:
            nodes = self._get_top_level_nodes()
        for node in nodes:
            key = node.text(0)
            if key == 'ROI':
                canvas.set_rect_tree_item(node)
                canvas.set_editing()
                shape = reset_canvas_roi(node)
                if shape is not None:
                    shapes.append(shape)
                    canvas.shape_tree[shape] = node

        canvas.load_shapes(shapes)
        canvas.update()

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
    #             sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)
    #         else:
    #             sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
    #             root.addChild(sub_node)
    #
    #     elif isinstance(value, str):
    #         sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
    #         root.addChild(sub_node)
    #
    #     elif isinstance(value, dict):
    #         ui_type = None
    #         if root is None:
    #             sub_root_node = QTreeWidgetItem(self.right_tree)
    #             sub_root_node.setText(0, key)
    #             sub_root_node.setText(2, ui_type)
    #         else:
    #             sub_root_node = create_tree_item(key=key, node_type=ui_type)
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
