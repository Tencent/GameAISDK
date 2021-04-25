# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import shutil
import os

from PyQt5 import QtGui
from PyQt5 import QtWidgets

from ....common.singleton import Singleton
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ...dialog.tip_dialog import show_warning_tips, show_question_tips
from .comm_ui_node import CommUINode
from .over_ui_node import OverUINode
from .pop_ui_node import POPUINode
from .hall_node_info import HallNodeInfo
from .start_node_info import StartNodeInfo
from .over_node_info import OverNodeInfo
from .pop_node_info import PopNodeInfo
from ...dialog.edit_dialog import EditDialog
from ....config_manager.ui.ui_manager import UIType, UIManager
from ...dialog.load_ui_dlg import LoadUIDlg
from ...canvas.ui_canvas import canvas, update_rect_shapes
from ...tree.tree_manager import tree_mgr
from ....common.define import ITEM_TYPE_GAME_OVER, ITEM_TYPE_GAME_START, ITEM_TYPE_GAME_HALL, ITEM_TYPE_GAME_POP_UI, \
    ITEM_TYPE_DEVICE_POP_UI, ITEM_TYPE_UI_ELEMENT, ITEM_TYPE_CLOSE_ICONS, UI_NAMES, image_path_keys, Number_Key, \
    file_path_keys, rect_node_keys, Mode
from ...utils import is_json_file, get_sub_nodes, create_tree_item, clear_child, show_work_tree, \
    right_tree_value_changed, show_detail_item, show_critical_item, is_image, is_roi_invalid
from ..project_data_manager import ProjectDataManager
from ...dialog.label_dialog import LabelDialog
from ...main_window.tool_window import ui

logger = logging.getLogger("sdktool")


class UITree(metaclass=Singleton):
    def __init__(self):
        super(UITree, self).__init__()
        self.__ui_tree_item = None
        self.__left_tree = None
        self.__right_tree = None
        self.__dlg = None
        self.__pre_number_value = 0
        # self.__pre_right_tree_key = None
        self.__pre_left_tree_key = None
        self.__node = dict()
        self.__pre_right_tree_key = None

    def init(self, left_tree=None, right_tree=None):
        self.__left_tree = left_tree
        self.__right_tree = right_tree
        self.__node["HallUI"] = CommUINode(config=HallNodeInfo(ui_type=UIType.HALL_UI.value), left_tree=left_tree,
                                           right_tree=right_tree)
        self.__node["StartUI"] = CommUINode(config=StartNodeInfo(ui_type=UIType.START_UI.value), left_tree=left_tree,
                                            right_tree=right_tree)
        self.__node["OverUI"] = OverUINode(config=OverNodeInfo(), left_tree=left_tree, right_tree=right_tree)

        self.__node["Game"] = POPUINode(config=PopNodeInfo(ui_type=UIType.CLOSE_ICON_UI.value),
                                        left_tree=left_tree, right_tree=right_tree)
        self.__node["Device"] = POPUINode(config=PopNodeInfo(ui_type=UIType.DEVICE_CLOSE_ICON_UI.value),
                                          left_tree=left_tree,
                                          right_tree=right_tree)

        tree_mgr.set_object(Mode.UI, self)

    def check_add_element(self):
        data_mgr = ProjectDataManager()
        media_source = data_mgr.get_media_source()
        if not media_source.is_ready():
            show_warning_tips("please select source first")
            return

        uis = [ITEM_TYPE_GAME_OVER, ITEM_TYPE_GAME_START, ITEM_TYPE_GAME_HALL,
               ITEM_TYPE_GAME_POP_UI, ITEM_TYPE_DEVICE_POP_UI]

        current_node = self.__left_tree.currentItem()

        if current_node is None or current_node.text(2) not in uis:
            show_warning_tips("please select UI Node({})".format(['HallUI', 'StartUI', 'OverUI', 'POPUI']))
            return

        logger.info("func for add element")
        self.__dlg = EditDialog(label_text='name', default_edit='element_name', title='tips')
        self.__dlg.edit.setFocus()
        self.__dlg.finish_signal.connect(self.add_element)
        self.__dlg.pop_up()

    def add_task(self, right_tree):
        logger.debug("add_task right_tree:%s", right_tree)
        cur_node = self.__right_tree.currentItem()
        self.__node["HallUI"].new_task_node(cur_node)

    def del_task(self, right_tree):
        logger.debug("del_task right_tree:%s", right_tree)
        node = self.__right_tree.currentItem()
        dlg = LabelDialog(text="please confirm to delete {} task ?".format(node.text(0)), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_task(node))
        dlg.pop_up()

    @staticmethod
    def _del_task(node):
        if node is None:
            logger.info("node is None")
            return
        parent = node.parent()
        parent.removeChild(node)

    def add_element(self, element_name):
        if not self.save_previous_rtree():
            return

        left_tree_root = self.__left_tree.currentItem()
        text = left_tree_root.text(0)
        logger.info("current item 0th text is %s, element　name %s", text, element_name)
        result = False

        if text in self.__node.keys():
            result = self.__node[text].new_element_node(element_name)
        else:
            logger.error("unknown left node %s", text)
        self.__dlg.set_valid(result)

    def _del_node(self, node):
        canvas.reset_state()
        parent = node.parent()
        text = parent.text(0)
        if text in self.__node.keys():
            self.__node[text].delete_element_node(node)
        else:
            raise Exception("unknown node %s", text)
        logger.info("delete node, current item 0th text is %s", text)

    def delete_element(self, tree):
        if tree is None:
            logger.error("input tree is None")
            return
        node = tree.currentItem()
        if node.text(2) != ITEM_TYPE_UI_ELEMENT:
            show_warning_tips("this is not a element")
            return

        dlg = LabelDialog(text="please confirm to delete {} element ?".format(node.text(0)), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_node(node))
        dlg.pop_up()

    def load_element(self, node, right_tree_node):
        if node is None:
            raise Exception("node is None, right_tree_node: %s", right_tree_node)

        if not self.save_previous_rtree():
            return

        element_id = node.text(1)
        parent = node.parent()
        text = parent.text(0)

        if text in self.__node.keys():
            self.__node[text].load_element_node(element_id)
        else:
            logger.error("text {} is not in register in load_node_func, please check")
            return

    def load_ui(self, ui_config=None):
        if ui_config is None:
            dlg = LoadUIDlg()
            dlg.pop_up()
            ui_config = dlg.ui_config_edit.text()
            if ui_config is None:
                logger.error("ui_node ui_node is None")
            if not is_json_file(ui_config):
                dlg = LabelDialog(text="{} is not a json file".format(ui_config))
                dlg.pop_up()

                return

        self.new_ui()

        for _, sub_ui in self.__node.items():
            sub_ui.load_file(ui_config)

    def new_ui(self):
        # 左树处理
        project_node = self.__left_tree.topLevelItem(0)
        project_name = project_node.text(0)
        if len(project_name) == 0:
            show_warning_tips("please new project first")
            return

        root = None
        nodes = get_sub_nodes(project_node)
        for node in nodes:
            if node.text(0) == 'UI':
                root = node
                if not show_question_tips('已有UI节点，是否覆盖'):
                    return
                break

        if bsa.has_service_running():
            show_warning_tips("已有服务在运行，请先停止后再新建UI节点")
            return

        if root is None:
            root = create_tree_item(key='UI')
            project_node.addChild(root)
            project_node.setExpanded(True)
        ui.set_ui_canvas(canvas)

        sub_nodes = get_sub_nodes(root)
        sub_node_dict = dict()
        for sub_node in sub_nodes:
            sub_node_dict[sub_node.text(0)] = sub_node
            # sub_node_keys.append(sub_node.text(0))

        if 'HallUI' not in sub_node_dict.keys():
            root.addChild(self.__node["HallUI"].create_root_node(name="HallUI", item_type=ITEM_TYPE_GAME_HALL))
        else:
            node = sub_node_dict.get("HallUI")
            clear_child(node)
            self.__node["HallUI"].set_root_node(node)

        if 'StartUI' not in sub_node_dict.keys():
            root.addChild(self.__node["StartUI"].create_root_node(name="StartUI", item_type=ITEM_TYPE_GAME_START))
        else:
            node = sub_node_dict.get("StartUI")
            clear_child(node)
            self.__node["StartUI"].set_root_node(node)

        if 'OverUI' not in sub_node_dict:
            root.addChild(self.__node["OverUI"].create_root_node(name="OverUI", item_type=ITEM_TYPE_GAME_OVER))
        else:
            node = sub_node_dict.get("OverUI")
            clear_child(node)
            self.__node["OverUI"].set_root_node(node)

        if 'POPUI' not in sub_node_dict.keys():
            close_node = create_tree_item(key="POPUI", node_type=ITEM_TYPE_CLOSE_ICONS)
            root.addChild(close_node)
            close_node.addChild(self.__node["Game"].create_root_node(name="Game", item_type=ITEM_TYPE_GAME_POP_UI))
            close_node.addChild(self.__node["Device"].create_root_node(name="Device",
                                                                       item_type=ITEM_TYPE_DEVICE_POP_UI))
            close_node.setExpanded(True)
        else:
            close_node = sub_node_dict.get("POPUI")
            sub_close_nodes = get_sub_nodes(close_node)
            for sub_close_node in sub_close_nodes:
                if sub_close_node.text(0) == 'Game':
                    clear_child(sub_close_node)
                    self.__node["Game"].set_root_node(sub_close_node)
                elif sub_close_node.text(0) == 'Device':
                    clear_child(sub_close_node)
                    self.__node["Device"].set_root_node(sub_close_node)

        root.setExpanded(True)

        # 保存之前的右树
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.UI and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.UI)

        # 清除右树
        for _ in range(self.__right_tree.topLevelItemCount()):
            self.__right_tree.takeTopLevelItem(0)

        # 清除UI数据
        self.clear_ui()

        tree_mgr.update(self)
        show_work_tree(self.__left_tree, Mode.UI)

    @staticmethod
    def clear_ui():
        ui_mgr = UIManager()
        ui_mgr.clear_config()

    def save_ui(self):
        name_node = self.__right_tree.topLevelItem(0)
        if name_node is None:
            return True
        ui_key = name_node.text(2)
        if ui_key in UI_NAMES:
            return self.__node[ui_key].save_file()
        return True

    @staticmethod
    def _save_diff_mode_tree():
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.UI and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.UI)
        return True

    def save_previous_rtree(self):
        # 保存前一种类型的右树
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.UI:
            return self._save_diff_mode_tree()

        # 保存当前类型的右树
        # save right tree
        name_node = self.__right_tree.topLevelItem(0)
        if name_node is None:
            return True

        cur_ui_type = name_node.text(2)
        success = True
        if cur_ui_type in self.__node.keys():
            success = self.__node[cur_ui_type].save_check_element()
        return success

    def double_click_left_tree(self, node, column):
        logger.debug("double click left tree")
        logger.debug("node text %s, column %s", node.text(0), column)
        if column == 0:
            self.__pre_left_tree_key = node.text(0)

        node_type = node.text(2)
        if node_type in [ITEM_TYPE_UI_ELEMENT]:
            if not self.save_previous_rtree():
                return

            parent = node.parent()
            text = parent.text(0)
            element_id = node.text(1)
            image_path = node.text(3)
            logger.debug("text %s, id %s, image %s", text, element_id, image_path)
            if text in self.__node.keys():
                self.__node[text].load_element_node(element_id)
            else:
                logger.error("text {} is not in register in load_node_func, please check")
        else:
            logger.info("element type %s", node_type)
        tree_mgr.set_mode(Mode.UI)

    def double_click_right_tree(self, node, column):
        canvas.mouse_move_flag = False

        if column == 0:
            self.__pre_right_tree_key = node.text(0)

        key = node.text(0)
        file_path = node.text(3)
        if key in image_path_keys:
            reset = False
            if not os.path.exists(file_path):
                reset = True
            self.click_image_path(file_path=file_path, reset_path=reset)

        if key in ['task']:
            sub_nodes = get_sub_nodes(node)
            action_node = None
            for sub_node in sub_nodes:
                logger.debug("text 0 %s", sub_node.text(0))
                if sub_node.text(0) == 'action':
                    action_node = sub_node
                    break
            action_x = 0
            action_y = 0
            for ss_node_index in range(action_node.childCount()):
                ss_node = action_node.child(ss_node_index)
                if ss_node.text(0) in ['actionX', 'actionX1']:
                    action_x = int(ss_node.text(1))
                elif ss_node.text(0) in ['actionY', 'actionY1']:
                    action_y = int(ss_node.text(1))

            if action_x == 0 and action_y == 0:
                self.__node["HallUI"].new_canvas_shapes(nodes=sub_nodes)
            else:
                self.__node["HallUI"].load_canvas_shapes(nodes=sub_nodes)

        if key in Number_Key:
            self.__pre_number_value = node.text(1)

        if key in file_path_keys:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "select file", file_path, "*")
            _, file_name = os.path.split(file_path)
            project_data = ProjectDataManager().get_project_data_path()
            project_file_path = os.path.join(project_data, file_name)
            if not os.path.exists(project_file_path):
                shutil.copy(file_path, project_file_path)

            node.setText(1, project_file_path)
            node.setText(3, project_file_path)

        if key in ['target']:
            self.__node["HallUI"].update_canvas(root=node)

    def right_tree_value_changed(self, node, column):
        if not node:
            logger.info("item value changed failed, current_item is none")
            return
        if node.text(0) in ['template']:
            # 查找当前的UI类型
            name_node = self.__right_tree.topLevelItem(0)
            if not name_node:
                return

            cur_ui_type = name_node.text(2)
            if cur_ui_type in ["HallUI", "StartUI"]:
                # self.__node["HallUI"].template_edit_finished()
                self.__node[cur_ui_type].template_edit_finished()
                return
            logger.warning("template node in UIType %s", cur_ui_type)

        if canvas.mouse_move_flag:
            logger.info("mouse is movinging")
            return

        right_tree_value_changed(canvas, node, column, self.__pre_number_value)
        parent = node.parent()
        if parent is None:
            return

        if parent.text(0) in rect_node_keys:
            update_rect_shapes(parent)

    def set_element_path(self, key, image_path):
        if None in [key, image_path]:
            logger.error("input key %s or image_path %s is None", key, image_path)
            return

        current_item = self.__left_tree.currentItem()
        if current_item is None:
            logger.error("current item is None")
            return

        if current_item.text(0) == key:
            current_item.setText(3, image_path)
            logger.info("set node %s 3 %s", current_item.text(0), current_item.text(3))
        else:
            for index in range(current_item.childCount()):
                sub_node = current_item.child(index)
                if sub_node.text(0) == key:
                    sub_node.setText(3, image_path)
                    logger.info("set node %s 3 %s", sub_node.text(0), sub_node.text(3))
                    break

    def show_detail(self):
        item = self.__right_tree.currentItem()
        if item is None:
            return
        show_detail_item(item)

    def show_critical(self):
        item = self.__right_tree.currentItem()
        if item is None:
            return
        show_critical_item(item)

    def change_file_path(self):
        node = self.__right_tree.currentItem()
        if node is None:
            return
        if node.text(0) in image_path_keys:
            self.click_image_path(reset_path=True)

    def click_image_path(self, file_path=None, reset_path=False):
        if reset_path:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "select file", file_path, "*")

            # 如果未选择，则直接退出
            if len(file_path) == 0:
                logger.info("give up select image path")
                return

            # 如果选择的不是图像，则提示后，退出
            if not is_image(file_path):
                show_warning_tips("please select a image")
                return

        _, file_name = os.path.split(file_path)
        data_path = ProjectDataManager().get_project_data_path()
        project_file_path = os.path.join(data_path, file_name)
        if not os.path.exists(project_file_path):
            shutil.copy(file_path, project_file_path)
        node = self.__right_tree.currentItem()
        node.setText(1, project_file_path)
        node.setText(3, project_file_path)

        left_node = self.__left_tree.currentItem()
        if left_node is None:
            return

        frame = QtGui.QImage(project_file_path)
        pix = QtGui.QPixmap.fromImage(frame)
        canvas.load_pixmap(pix)
        canvas.update()

        cur_text = left_node.text(0)
        parent_text = None
        parent = left_node.parent()
        if parent is not None:
            parent_text = parent.text(0)
        sub_ui_key = {cur_text, parent_text} & set(self.__node.keys())
        if sub_ui_key is not None:
            sub_ui_key = sub_ui_key.pop()
        if not reset_path:
            self.__node[sub_ui_key].update_canvas()
        else:
            key = node.text(0)
            if key == 'targetImg':
                parent = node.parent()
                if not is_roi_invalid(parent.child(1)):
                    self.__node["HallUI"].new_canvas_shapes(get_sub_nodes(parent))
            else:
                if key == 'imgPath':
                    name_node = self.__right_tree.topLevelItem(0)
                    self.set_element_path(name_node.text(1), image_path=project_file_path)
                    self.__node[sub_ui_key].new_canvas_shapes()
