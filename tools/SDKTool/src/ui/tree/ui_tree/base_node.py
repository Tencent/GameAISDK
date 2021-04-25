# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore import Qt

from ...tree.tree_manager import tree_mgr
from ...utils import create_tree_item, get_sub_nodes, Mode, is_image, get_tree_top_nodes, is_str_valid, \
    show_critical_item
from ...canvas.ui_canvas import canvas
from ...canvas.shape import Shape
from ...dialog.tip_dialog import show_critical_tips, show_warning_tips
from ....config_manager.ui.ui_manager import UIType
from ....common.define import ITEM_TYPE_UI_ELEMENT, need_value_keys, positive_integer_value_keys, image_path_keys, \
    DISABLE_EDIT_KEYS, TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG, TYPE_UIACTION_DRAGCHECK, ITEM_TYPE_UI_SCRIPT_TASKS, \
    ITEM_TYPE_UI_ROI


logger = logging.getLogger("sdktool")

ui_type_map = \
    {
        UIType.HALL_UI.value: "HallUI",
        UIType.START_UI.value: "StartUI",
        UIType.OVER_UI.value: "OverUI",
        UIType.CLOSE_ICON_UI.value: "Game",
        UIType.DEVICE_CLOSE_ICON_UI.value: "Device"
    }


class BaseNode(object):
    def __init__(self, config=None, left_tree=None, right_tree=None):
        self._cfg = config
        self._root = None
        self.left_tree = left_tree
        self.right_tree = right_tree

    def create_root_node(self, name=None, item_type=None):
        logger.info("add root node")
        self._root = create_tree_item(key=name, node_type=item_type, edit=False)
        logger.info("root %s", self._root)
        return self._root

    def set_root_node(self, root_node):
        self._root = root_node

    def set_cfg(self, cfg=None):
        self._cfg = cfg

    def save_file(self):
        return self.save_check_element()

    def load_file(self, config_file=None):
        elements = self._cfg.load_config(config_file)
        for ele_id, ele_name in elements:
            self._root.addChild(create_tree_item(key=ele_name, value=ele_id,
                                                 node_type=ITEM_TYPE_UI_ELEMENT, edit=False))

    def save_check_element(self):
        """ 每次切换element的时候,保存当前的配置

        :return:
        """
        if not self.check_element_node():
            return False

        node_count = self.right_tree.topLevelItemCount()
        if node_count > 0:
            self._cfg.save_element(self.right_tree)

        return True

    def load_element_node(self, element_id):
        config = self._cfg.load_element(int(element_id))
        if not config:
            show_warning_tips("not find {} in ui_node".format(element_id))
            return False
        self.update_right_tree(config)
        self.update_canvas()
        return True

    def delete_element_node(self, node):
        if node is None:
            show_warning_tips("input tree item is None")
            return False

        # 从左树父节点中删除子节点
        element_id = node.text(1)
        logger.info("delete element id %s", element_id)
        self._cfg.delete_element(int(element_id))
        self._root.removeChild(node)
        # 同时右树清空
        self.update_right_tree(dict())
        return True

    def check_element_node(self, root=None):
        if root is None:
            nodes = self._get_top_level_nodes()
        else:
            nodes = get_sub_nodes(root)

        for node in nodes:
            if (node.text(0) in need_value_keys) and len(node.text(1)) == 0:
                show_warning_tips("{} should have value".format(node.text(0)))
                return False

            if node.text(0) in positive_integer_value_keys and int(node.text(1)) <= 0:
                show_warning_tips("{} should have a positive integer value".format(node.text(0)))
                return False

            if node.childCount() > 0:
                self.check_element_node(node)

        return True

    def new_element_node(self, element_name=None):
        if not self.is_name_valid(element_name):
            return False

        if not self.check_element_node():
            return False

        for _ in range(self.right_tree.topLevelItemCount()):
            self.right_tree.takeTopLevelItem(0)

        config = self._cfg.new_element_cfg(element_name)
        self._root.addChild(create_tree_item(key=element_name,
                                             value=config.get('id'),
                                             node_type=ITEM_TYPE_UI_ELEMENT,
                                             edit=False))
        self._root.setExpanded(True)

        self.update_right_tree(config=config)
        self.update_canvas()

        tree_mgr.set_mode(Mode.UI)
        return True

    def _find_image_path(self, root=None):
        # find image path in 4th column of left tree
        result_node = self.left_tree.currentItem()
        # 0:key, 1:value, 2:type, 3:image_path
        image_path = result_node.text(3)
        if is_image(image_path):
            return image_path, result_node
        # cur_node = self.right_tree.currentItem()
        if root is not None:
            nodes = get_sub_nodes(root)
        else:
            nodes = self._get_top_level_nodes()
        for node in nodes:
            if node.text(0) in image_path_keys:
                image_path = node.text(1)
                result_node = node

                if is_image(image_path):
                    return image_path, result_node

        return image_path, result_node

    def _get_top_level_nodes(self):
        return get_tree_top_nodes(self.right_tree)

    def update_canvas(self, root=None):
        canvas.reset_state()
        # 获取图像路径和带有图像路径的节点
        image_path, _ = self._find_image_path(root)
        new_shapes = False

        if is_image(image_path):
            frame = QtGui.QImage(image_path)
            pix = QtGui.QPixmap.fromImage(frame)
            canvas.load_pixmap(pix)
            canvas.update()
        else:
            new_shapes = True

        if not self.is_action_valid(root):
            new_shapes = True

        if root is None:
            sub_nodes = self._get_top_level_nodes()
        else:
            sub_nodes = get_sub_nodes(root)

        if new_shapes:
            self.new_canvas_shapes(sub_nodes)
        else:
            self.load_canvas_shapes(sub_nodes)

    def is_name_valid(self, element_name=None):
        for index in range(self._root.childCount()):
            item = self._root.child(index)
            if item.text(0) == element_name:
                show_warning_tips("name have already exist")
                return False

        if not is_str_valid(element_name):
            show_warning_tips("{} is not valid(char or num)".format(element_name))
            return False

        return True

    def new_action_type(self, value=None, root=None):
        if root is not None:
            action_type_node = create_tree_item(key='actionType', value=value)
            root.addChild(action_type_node)
        else:
            action_type_node = QTreeWidgetItem(self.right_tree)
            action_type_node.setText(0, 'actionType')
            action_type_node.setText(1, value)

        combobox = QtWidgets.QComboBox()
        combobox.addItems(self.get_action_type())
        combobox.setCurrentText(str(value))
        combobox.currentTextChanged.connect(self.action_type_changed)
        # action_type.
        logger.info("add combobox node")
        self.right_tree.setItemWidget(action_type_node, 1, combobox)
        return action_type_node

    @staticmethod
    def get_action_type():
        return []

    @staticmethod
    def is_action_valid(root=None):
        logger.debug('root: %s', root)
        return True

    def action_type_changed(self, text):
        pass

    def _set_canvas_action(self, node):
        # find action type
        parent = node.parent()
        action_type = TYPE_UIACTION_CLICK
        if parent is not None:
            for sub_node_index in range(parent.childCount()):
                sub_node = parent.child(sub_node_index)
                if sub_node.text(0) == 'actionType':
                    action_type = sub_node.text(1)
                    break
        else:
            for sub_node_index in range(self.right_tree.topLevelItemCount()):
                sub_node = self.right_tree.topLevelItem(sub_node_index)
                if sub_node.text(0) == 'actionType':
                    action_type = sub_node.text(1)
                    break

        # various 'action type' with diff canvas model
        if node.text(0) == 'action' and action_type in [TYPE_UIACTION_CLICK]:
            canvas.set_editing(False)
            canvas.current_model.append(Shape.POINT)
            canvas.set_point_tree_item(node)

        elif node.text(0) == 'action' and action_type in [TYPE_UIACTION_DRAG]:
            canvas.set_editing(False)
            canvas.current_model.append(Shape.LINE)
            canvas.set_line_tree_item(node)

        elif node.text(0) == 'action' and action_type in [TYPE_UIACTION_DRAGCHECK]:
            for sub_node_index in range(node.childCount()):
                sub_node = node.child(sub_node_index)
                if sub_node.text(0) == 'dragPoint':
                    canvas.set_editing(False)
                    canvas.current_model.append(Shape.POINT)
                    canvas.set_point_tree_item(sub_node)
        else:
            logger.error("unknown action type %s", action_type)

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

            elif node.text(0) == 'action':
                self._set_canvas_action(node)

            elif node.text(1) in ['tasks']:
                sub_nodes = get_sub_nodes(node)
                for sub_node in sub_nodes:
                    if sub_node.text(0) != 'task':
                        continue
                    ss_nodes = get_sub_nodes(sub_node)
                    for ss_node in ss_nodes:
                        if ss_node.text(1) != 'action':
                            continue
                        self._set_canvas_action(ss_node)

    def load_canvas_shapes(self, nodes=None):
        raise NotImplementedError()

    def _create_complex_node(self, key, value, root=None):
        logger.debug("create complex node key %s, value %s, root is %s", key, value, root)
        edit_flag = True
        if key in DISABLE_EDIT_KEYS:
            edit_flag = False

        if isinstance(value, (int, float)):
            if root is None:
                sub_node = QTreeWidgetItem(self.right_tree)
                sub_node.setText(0, key)
                sub_node.setText(1, str(value))
                if key not in DISABLE_EDIT_KEYS:
                    sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)
            else:
                sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
                root.addChild(sub_node)

        elif isinstance(value, str):
            if key == 'actionType':
                self.new_action_type(value=value, root=root)
            elif key == 'actionDir':
                sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
                root.addChild(sub_node)
                combobox = QtWidgets.QComboBox()
                combobox.addItems(['down', 'up', 'left', 'right'])

                combobox.setCurrentText(value)
                combobox.currentTextChanged.connect(self.action_dir_changed)
                # action_type.
                logger.info("add combobox node")
                self.right_tree.setItemWidget(sub_node, 1, combobox)
            else:
                sub_node = create_tree_item(key=key, value=value, edit=edit_flag)
                root.addChild(sub_node)

        elif isinstance(value, dict):
            ui_type = None
            if key == "tasks":
                ui_type = ITEM_TYPE_UI_SCRIPT_TASKS

            if root is None:
                sub_root_node = QTreeWidgetItem(self.right_tree)
                sub_root_node.setText(0, key)
                sub_root_node.setText(2, ui_type)
            else:
                sub_root_node = create_tree_item(key=key, node_type=ui_type)
                root.addChild(sub_root_node)

            for sub_key, sub_value in value.items():
                self._create_complex_node(key=sub_key, value=sub_value, root=sub_root_node)
            sub_root_node.setExpanded(True)

        elif isinstance(value, list):
            ui_type = None
            for sub_value in value:
                if key == 'ROI':
                    ui_type = ITEM_TYPE_UI_ROI
                elif key == 'task':
                    ui_type = ITEM_TYPE_UI_SCRIPT_TASKS
                if root is None:
                    sub_root_node = QTreeWidgetItem(self.right_tree)
                    sub_root_node.setText(0, key)
                    sub_root_node.setText(2, ui_type)
                else:
                    sub_root_node = create_tree_item(key=key, node_type=ui_type)
                    root.addChild(sub_root_node)
                # x,y,w,h.....
                for roi_key, roi_value in sub_value.items():
                    self._create_complex_node(key=roi_key, value=roi_value, root=sub_root_node)
                sub_root_node.setExpanded(True)

    def update_right_tree(self, config=None):
        self.right_tree.clear()
        for key, value in config.items():
            logger.debug("key %s, value %s", key, value)
            if isinstance(value, (str, int, float)):
                if key == 'actionType':
                    self.new_action_type(value=value, root=None)
                elif key == 'name':
                    node = QTreeWidgetItem(self.right_tree)
                    node.setText(0, key)
                    node.setText(1, str(value))
                    node.setText(2, ui_type_map.get(self._cfg.ui_type))
                elif key == 'template':
                    self.create_template_number(value=value, root=None)
                elif key == 'templateOp':
                    self.create_template_op(value=value, root=None)
                else:
                    node = QTreeWidgetItem(self.right_tree)
                    node.setText(0, key)
                    node.setText(1, str(value))
                    if key not in DISABLE_EDIT_KEYS:
                        node.setFlags(node.flags() | Qt.ItemIsEditable)

            elif isinstance(value, (dict, list)):
                self._create_complex_node(key=key, value=value, root=None)

        nodes = self._get_top_level_nodes()
        for node in nodes:
            show_critical_item(node)
