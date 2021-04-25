# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox
from PyQt5 import QtGui

from ....common.define import ITEM_TYPE_ELEMENT, ITEM_TYPE_TEMPLATE, ITEM_TYPE_ELEMENTS, SCENE_HIDDEN_KEYS, \
    ITEM_TYPE_REFER_TASK, ITEM_TYPE_ELEMENT_NAME, DISABLE_EDIT_KEYS, DEFAULT_TEMPLATE_THRESHOLD, rect_node_keys, \
    image_path_keys, need_value_keys, positive_integer_value_keys, task_type_list, refer_type_list, \
    refer_location_algorithm, algorithm_keys, ITEM_ELEMENTS_NAME, ITEM_CONDITION_NAME, ITEM_CONDITIONS_NAME
from ....context.app_context import AppContext
from ...canvas.ui_canvas import canvas, reset_canvas_roi
from ...canvas.shape import Shape
from ...dialog.label_dialog import LabelDialog
from ...dialog.tip_dialog import show_critical_tips, show_warning_tips
from ...tree.scene_tree.task_node_info import TaskNodeInfo
from ...utils import get_sub_nodes, create_tree_item, is_image, get_tree_top_nodes, get_item_by_type

logger = logging.getLogger("sdktool")


class SceneNode(object):
    def __init__(self):
        self.__right_tree = None
        self.__cur_reg_type = None
        self.__cfg = TaskNodeInfo()

    def init(self, right_tree):
        if right_tree is None:
            logger.error("input param right tree is none")
            return False
        self.__right_tree = right_tree
        return self.__cfg.init()

    def add_element(self):
        root = self.__right_tree.currentItem()
        element = create_tree_item(key='element', node_type=ITEM_TYPE_ELEMENT, edit=False)
        root.addChild(element)
        config = self.__cfg.new_element_cfg(self.__cur_reg_type)
        for key, value in config.items():
            self.create_complex_node(key, value, element)
        element.setExpanded(True)

    def del_element(self):
        node = self.__right_tree.currentItem()
        if node is None:
            return

        dlg = LabelDialog(text="please confirm to delete {} element ?".format(node.text(0)), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_node(node))
        dlg.pop_up()

    def add_refer_template(self):
        node = self.__right_tree.currentItem()
        template_node = create_tree_item(key='template', node_type=ITEM_TYPE_TEMPLATE, edit=False)
        path_node = create_tree_item(key='path', edit=True)
        threshold_node = create_tree_item(key='threshold', value=DEFAULT_TEMPLATE_THRESHOLD)
        template_node.addChild(path_node)
        template_node.addChild(threshold_node)
        node.addChild(template_node)

    def add_template(self):
        node = self.__right_tree.currentItem()
        sub_nodes = get_sub_nodes(node)
        # 删除之前的refer节点
        refer_node = None
        for sub_node in sub_nodes:
            if sub_node.text(0) == 'refer':
                refer_node = sub_node
                node.removeChild(sub_node)
                break

        template_node = create_tree_item(key='template', node_type=ITEM_TYPE_TEMPLATE, edit=False)
        node.addChild(template_node)

        # 恢复refer节点，使得refer节点始终在最后
        if refer_node is not None:
            node.addChild(refer_node)

        config = self.__cfg.new_sub_item_cfg()
        for key, value in config.items():
            self.create_complex_node(key=key, value=value, root=template_node)

    def del_template(self):
        node = self.__right_tree.currentItem()
        dlg = LabelDialog(text="please confirm to delete template {} ?".format(node.text(0)), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_node(node))
        dlg.pop_up()

    def add_refer(self):
        node = self.__right_tree.currentItem()
        sub_nodes = get_sub_nodes(node)
        for sub_node in sub_nodes:
            if sub_node.text(0) == 'refer':
                dlg = LabelDialog(text="refer has already exist")
                dlg.pop_up()
                return

        refer_node = create_tree_item(key='refer', node_type=ITEM_TYPE_REFER_TASK, edit=False)
        node.addChild(refer_node)

        config = self.__cfg.new_refer_cfg()
        config["taskID"] = self.get_refer_id()
        for key, value in config.items():
            self.create_complex_node(key, value, refer_node)
        self.__cfg.set_refer_id(config['taskID'])

    def del_refer(self):
        node = self.__right_tree.currentItem()
        dlg = LabelDialog(text="please confirm to delete refer {} ?".format(node.text(0)), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_node(node))
        dlg.pop_up()

    def get_refer_id(self):
        node = self.__right_tree.currentItem()
        nodes = get_sub_nodes(node.parent())
        element_index = nodes.index(node)
        task_id = 0
        top_nodes = self.get_top_level_nodes()
        for _, top_node in enumerate(top_nodes):
            if top_node.text(0) == 'taskID':
                task_id = int(top_node.text(1))
                break
        logger.info("get refer id: task id %s, element index %s", task_id, element_index)
        return task_id * 1000 + element_index

    def get_top_level_nodes(self):
        return get_tree_top_nodes(self.__right_tree)

    def get_reg_type(self):
        return self.__cur_reg_type

    def reg_type_changed(self, text):
        node = self.__right_tree.currentItem()
        node.setText(1, text)
        self.__cur_reg_type = text
        nodes = self.get_top_level_nodes()
        elements = None
        for node in nodes:
            if node.text(0) == "elements":
                elements = node
                break

        if elements is None:
            return
        for _ in range(elements.childCount()):
            elements.takeChild(0)

        config = self.__cfg.new_element_cfg(text)
        element = create_tree_item(key='element', node_type=ITEM_TYPE_ELEMENT, edit=False)
        elements.addChild(element)

        for key, value in config.items():
            self.create_complex_node(key, value, element)

        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.update()

    def refer_type_changed(self, text):
        node = self.__right_tree.currentItem()
        node.setText(1, text)
        self.__cur_reg_type = text
        refer_node = node.parent()
        for _ in range(refer_node.childCount()):
            refer_node.takeChild(0)

        config = self.__cfg.new_refer_cfg(text)

        for key, value in config.items():
            self.create_complex_node(key, value, refer_node)

        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.update()

    def new_task_node(self, task_name):
        config = self.__cfg.new_task_cfg(task_name)
        return config

    def load_task_node(self, task_id):
        task_config = self.__cfg.load_task_cfg(task_id)
        for key, value in task_config.items():
            self.create_complex_node(key=key, value=value, root=None)

        # 默认在画布加载第一个元素的图片
        node_count = self.__right_tree.topLevelItemCount()
        if node_count == 0:
            return

        for index in range(node_count):
            parent = self.__right_tree.topLevelItem(index)
            if parent.text(0) == ITEM_ELEMENTS_NAME:
                nodes = get_item_by_type(ITEM_TYPE_ELEMENT, parent)
                for element_node in nodes:
                    image_path = self.find_image_path(element_node)
                    if image_path:
                        self.__right_tree.setCurrentItem(element_node)
                        child_nodes = get_sub_nodes(element_node)
                        image = QtGui.QImage(image_path)
                        pix = QtGui.QPixmap.fromImage(image)
                        canvas.load_pixmap(pix)
                        self.load_canvas_shapes(child_nodes)
                        canvas.update()
                        return

    def del_task_node(self, task_id):
        self.__cfg.delete_task(task_id)

    def save_task_node(self):
        return self.__cfg.save_task_node(self.__right_tree)

    def new_canvas_shapes(self, nodes=None):
        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.mode = canvas.CREATE
        if nodes is None:
            nodes = self.get_top_level_nodes()
        for node in nodes:
            if node.text(0) in ['ROI', 'location', 'templateLocation', 'inferROI', 'inferSubROI']:
                canvas.set_rect_tree_item(node)
                canvas.current_model.append(Shape.RECT)
                canvas.set_editing(False)

    def load_canvas_shapes(self, nodes=None):
        shapes = []
        if nodes is None:
            nodes = self.get_top_level_nodes()
        for node in nodes:
            key = node.text(0)
            if key in rect_node_keys:
                canvas.set_rect_tree_item(node)
                canvas.set_editing()
                shape = reset_canvas_roi(node)
                if shape is not None:
                    shapes.append(shape)
                    canvas.shape_tree[shape] = node

        canvas.load_shapes(shapes)
        canvas.update()
        app_ctx = AppContext()
        app_ctx.set_info("phone", False)

    def find_image_path(self, node=None):
        img_path = None
        if node is None:
            node = self.__right_tree.currentItem()
            if node is None:
                return img_path

        sub_nodes = get_sub_nodes(node)
        for sub_node in sub_nodes:
            if sub_node.text(0) in image_path_keys:
                img_path = sub_node.text(1)
                if not is_image(img_path):
                    logger.error("image path %s is invalid ", img_path)
                    img_path = None
                    break
        return img_path

    def save_config(self):
        try:
            self.is_r_node_valid()
            self.__cfg.save_task_node(self.__right_tree)
            return True
        except RuntimeError as err:
            logger.error("err is %s", err)
            show_critical_tips("{}".format(err))
            return False

    def load_config(self, config_file, refer_config):
        return self.__cfg.load_config(config_file, refer_config)

    def clear_config(self):
        self.__cfg.clear_config()

    def is_rect_param_valid(self, nodes=None):
        if nodes is None:
            nodes = self.get_top_level_nodes()
        for node in nodes:
            logger.debug("node %s", node.text(0))
            if node.text(0) in rect_node_keys:
                # 0:x 1:y, 2:w, 3:h
                width_node = node.child(2)
                height_node = node.child(3)
                width_value = int(width_node.text(1))
                height_value = int(height_node.text(1))
                if 0 in [width_value, height_value]:
                    return False

        return True

    def is_r_node_valid(self, root=None):
        if root is None:
            nodes = self.get_top_level_nodes()
        else:
            nodes = get_sub_nodes(root)

        for node in nodes:
            logger.debug("r valid 0 %s 1 %s", node.text(0), node.text(1))
            if node.text(0) in need_value_keys and len(node.text(1)) == 0:
                show_warning_tips("{} should have value".format(node.text(0)))
                return

            if node.text(0) in positive_integer_value_keys and int(node.text(1)) <= 0:
                show_warning_tips("{} should have a positive integer value".format(node.text(0)))
                return

            if node.childCount() > 0:
                self.is_r_node_valid(node)

    def create_complex_node(self, key, value, root=None):
        # 0: key, 1:value, 2:type 3:file/image path
        sub_node = None
        if isinstance(value, (int, float)):
            if root is None:
                sub_node = QTreeWidgetItem(self.__right_tree)
                sub_node.setText(0, key)
                sub_node.setText(1, str(value))
                sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)
            else:
                sub_node = create_tree_item(key=key, value=value, edit=True)
                root.addChild(sub_node)
                root.setExpanded(True)

        elif isinstance(value, str):
            if root is None:
                sub_node = QTreeWidgetItem(self.__right_tree)
                sub_node.setText(0, key)
                sub_node.setText(1, str(value))
                if key not in DISABLE_EDIT_KEYS:
                    sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)

            else:
                enable_edit = False
                if key in [ITEM_TYPE_ELEMENT_NAME, ITEM_CONDITION_NAME, ITEM_CONDITIONS_NAME]:
                    enable_edit = True
                sub_node = create_tree_item(key=key, value=value, edit=enable_edit)
                root.addChild(sub_node)

            if key == 'algorithm':
                self._create_algorithm_node(key=key, value=value, node=sub_node)
            elif key == 'type':
                self._set_type_node(key, value, sub_node)

        elif isinstance(value, dict):
            if root is None:
                sub_node = QTreeWidgetItem(self.__right_tree)
                sub_node.setText(0, key)
            else:
                sub_node = create_tree_item(key=key)
                root.addChild(sub_node)

            if key == 'refer':
                sub_node.setText(2, ITEM_TYPE_REFER_TASK)

            for sub_key, sub_value in value.items():
                self.create_complex_node(key=sub_key, value=sub_value, root=sub_node)

            sub_node.setExpanded(True)

        elif isinstance(value, list):
            if key == 'elements':
                sub_node = QTreeWidgetItem(self.__right_tree)
                sub_node.setText(0, key)
                sub_node.setText(2, ITEM_TYPE_ELEMENTS)
                sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)
            else:
                sub_node = root

            for sub_value in value:
                rename_key = key[:-1]
                sub_type = ITEM_TYPE_ELEMENT
                if rename_key == 'template':
                    sub_type = ITEM_TYPE_TEMPLATE
                enable_edit = False
                ss_node = create_tree_item(key=rename_key, node_type=sub_type, edit=enable_edit)
                sub_node.addChild(ss_node)
                for ss_key, ss_value in sub_value.items():
                    self.create_complex_node(key=ss_key, value=ss_value, root=ss_node)
                ss_node.setExpanded(True)
            sub_node.setExpanded(True)

        if sub_node is None:
            return

        if key in SCENE_HIDDEN_KEYS:
            sub_node.setHidden(True)

    @staticmethod
    def _del_node(node):
        parent = node.parent()
        parent.removeChild(node)

    def _set_type_node(self, key, value, node):
        node.setText(0, key)
        node.setText(1, value)
        node.setFlags(node.flags() | Qt.ItemIsEditable)
        if node.parent() is None:
            self.__cur_reg_type = value
            combobox = QComboBox()
            combobox.addItems(task_type_list)
            combobox.setCurrentText(value)
            combobox.currentTextChanged.connect(self.reg_type_changed)
            self.__right_tree.setItemWidget(node, 1, combobox)
        elif node.parent().text(0) == 'refer':
            combobox = QComboBox()
            combobox.addItems(refer_type_list)
            combobox.setCurrentText(value)
            combobox.currentTextChanged.connect(self.refer_type_changed)
            self.__right_tree.setItemWidget(node, 1, combobox)

    def _reg_alg_type_changed(self, text):
        node = self.__right_tree.currentItem()
        node.setText(1, text)

    def _refer_alg_type_changed(self, text):
        if text not in refer_location_algorithm:
            logger.error("text %s not in refer location algorithm %s", text, refer_location_algorithm)
            return

        node = self.__right_tree.currentItem()
        parent = node.parent()
        if parent is None:
            logger.error("node %s parent is none", node.text(0))
            return

        for _ in range(parent.childCount()):
            parent.takeChild(0)

        config = self.__cfg.init_location_node(text)
        for key, value in config.items():
            self.create_complex_node(key=key, value=value, root=parent)

        node = self.__right_tree.currentItem()
        if node is not None:
            node.setText(1, text)

    def _create_algorithm_node(self, key: str, value: str,  node):
        parent = node.parent()
        if parent is None:
            return
        if parent.text(0) == 'refer':
            sub_nodes = get_sub_nodes(node.parent())
        else:
            sub_nodes = self.get_top_level_nodes()

        # refer的情况
        reg_type = None
        for sub_node in sub_nodes:
            # logger.debug("sub_node.text(0) is {}".format(sub_node.text(0)))
            if sub_node.text(0) == 'type':
                reg_type = sub_node.text(1)

        logger.debug("reg type is %s", reg_type)
        algorithms = algorithm_keys.get(reg_type)
        if algorithms is None:
            node.setText(0, key)
            node.setText(1, value)
            return

        combobox = QComboBox()
        combobox.addItems(algorithms)
        combobox.setCurrentText(value)
        if parent.text(0) == 'refer':
            combobox.currentTextChanged.connect(self._refer_alg_type_changed)
        else:
            combobox.currentTextChanged.connect(self._reg_alg_type_changed)

        self.__right_tree.setItemWidget(node, 1, combobox)
