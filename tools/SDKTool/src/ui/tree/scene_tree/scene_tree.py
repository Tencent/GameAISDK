# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import shutil

from PyQt5 import QtGui
from PyQt5.QtWidgets import QFileDialog

from ....common.define import Mode, SCENE_TASKS_TYPE, ITEM_TYPE_TASK, image_path_keys, Number_Key, \
    file_path_keys, rect_node_keys
from ....common.singleton import Singleton
from ...dialog.edit_dialog import EditDialog
from ...dialog.label_dialog import LabelDialog
from ...dialog.tip_dialog import show_warning_tips, show_critical_tips, show_question_tips
from ..project_data_manager import ProjectDataManager
from ..scene_tree.scene_node import SceneNode
from ...utils import create_tree_item, get_sub_nodes, is_image, show_work_tree, right_tree_value_changed, is_str_valid
from ...main_window.tool_window import ui
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa
from ...canvas.ui_canvas import canvas, update_rect_shapes
from ..tree_manager import tree_mgr
from ....project.project_manager import g_project_manager

logger = logging.getLogger("sdktool")


class SceneTree(metaclass=Singleton):
    def __init__(self):
        super(SceneTree, self).__init__()
        self.__ui_tree_item = None
        self.__left_tree = None
        self.__right_tree = None
        self.__dlg = None
        self.__pre_number_value = 0
        self.__pre_right_tree_key = None
        self.__pre_right_tree_value = None

        self.__pre_left_tree_key = None
        self.__cur_reg_type = None
        self.__tasks_node = None
        self.__sceneNode = SceneNode()

    def init(self, left_tree=None, right_tree=None):
        tree_mgr.set_object(Mode.SCENE, self)

        self.__left_tree = left_tree
        self.__right_tree = right_tree
        return self.__sceneNode.init(right_tree)

    def new_scene(self):
        # 左树处理
        project_node = self.__left_tree.topLevelItem(0)
        project_name = project_node.text(0)
        if len(project_name) == 0:
            show_warning_tips("please new project first")
            return

        # 保存之前的右树
        if not self._save_diff_mode_tree():
            show_warning_tips("save previous right tree failed")
            return

        root = None
        nodes = get_sub_nodes(project_node)
        for node in nodes:
            if node.text(0) == 'Scene':
                root = node
                if not show_question_tips('已有Scene节点，是否覆盖'):
                    return
                break

        if bsa.has_service_running():
            show_warning_tips("已有服务在运行，请先停止后再新建Scene节点")
            return

        if root is None:
            root = create_tree_item(key='Scene')
            project_node.addChild(root)
            project_node.setExpanded(True)

        ui.set_ui_canvas(canvas)
        sub_nodes = get_sub_nodes(root)
        sub_node_keys = []
        for sub_node in sub_nodes:
            sub_node_keys.append(sub_node.text(0))
        if 'name' not in sub_node_keys:
            root.addChild(create_tree_item(key="name", edit=True))
        if 'tasks' not in sub_node_keys:
            self.__tasks_node = create_tree_item(key='tasks', node_type=SCENE_TASKS_TYPE)
            root.addChild(self.__tasks_node)
        else:
            for _ in range(self.__tasks_node.childCount()):
                self.__tasks_node.takeChild(0)

        root.setExpanded(True)

        # 清除右树
        for _ in range(self.__right_tree.topLevelItemCount()):
            self.__right_tree.takeTopLevelItem(0)
        # 清除Scene数据
        self.__sceneNode.clear_config()

        tree_mgr.update(self)

        show_work_tree(self.__left_tree, Mode.SCENE)
        # g_project_manager.set_left_tree_created_flag(1)

    def load_scene(self, task_config=None, refer_config=None):
        if task_config is None:
            return
        self.new_scene()

        all_config = self.__sceneNode.load_config(task_config, refer_config)
        for item in all_config:
            task_id = item[0]
            task_name = item[1]
            if len(task_name) == 0:
                task_name = 'task{}'.format(task_id)
            self.__tasks_node.addChild(create_tree_item(key=task_name, value=task_id,
                                                        node_type=ITEM_TYPE_TASK, edit=False))

    def save_scene(self):
        mode = tree_mgr.get_mode()
        logger.debug("mode is %s", mode)
        if mode != Mode.SCENE:
            return True

        return self.__sceneNode.save_config()

    def new_task(self):
        data_mgr = ProjectDataManager()
        media_source = data_mgr.get_media_source()
        if not media_source.is_ready():
            show_warning_tips("please select source first")
            return
        current_node = self.__left_tree.currentItem()

        if current_node is None or current_node.text(2) != SCENE_TASKS_TYPE:
            show_warning_tips("please new task on left tree ('Scene' node)")
            return

        logger.info("func for new task")
        self.__dlg = EditDialog(label_text='name', default_edit='task_name', title='tips')
        self.__dlg.edit.setFocus()
        self.__dlg.finish_signal.connect(self._new_task_node)
        self.__dlg.pop_up()

    def _del_task(self, node):
        if node is None:
            logger.info("node is None")
            return
        canvas.reset_state()
        task_id = node.text(1)
        logger.debug("delete task name %s  id %s", node.text(0), task_id)
        self.__sceneNode.del_task_node(int(task_id))

        parent = node.parent()
        parent.removeChild(node)

        self.__right_tree.clear()

    def del_task(self):
        node = self.__left_tree.currentItem()
        if node.text(2) != ITEM_TYPE_TASK:
            show_warning_tips("this is not a task")
            return

        task_name = node.text(0)
        dlg = LabelDialog(text="please confirm to delete {} task ?".format(task_name), title="confirm")
        dlg.finish_signal.connect(lambda: self._del_task(node))
        dlg.pop_up()

    def load_task(self, task_id):
        canvas.reset_state()
        canvas.update()
        self.__right_tree.clear()
        self.__sceneNode.load_task_node(task_id)

    def update_refer_canvas(self):
        right_node = self.__right_tree.currentItem()
        nodes = get_sub_nodes(right_node)
        new_shape_nodes = []
        load_shape_nodes = []
        for node in nodes:
            if node.text(0) == 'template':
                image_path = self.__sceneNode.find_image_path(node)
                if image_path is not None:
                    image = QtGui.QImage(image_path)
                    pixmap = QtGui.QPixmap.fromImage(image)
                    canvas.load_pixmap(pixmap)
                    canvas.update()

            if node.text(0) == 'templateLocation':
                if self.__sceneNode.is_rect_param_valid([node]):
                    load_shape_nodes.append(node)
                else:
                    new_shape_nodes.append(node)
        if len(load_shape_nodes) > 0:
            self.__sceneNode.load_canvas_shapes(load_shape_nodes)

        if len(new_shape_nodes) > 0:
            self.__sceneNode.new_canvas_shapes(new_shape_nodes)
        canvas.update()

    def update_canvas(self):
        canvas.reset_shapes()
        image_path = self.__sceneNode.find_image_path()
        right_node = self.__right_tree.currentItem()
        nodes = get_sub_nodes(right_node)
        if image_path is None or not self.__sceneNode.is_rect_param_valid():
            self.__sceneNode.new_canvas_shapes(nodes)
        else:
            image = QtGui.QImage(image_path)
            pix = QtGui.QPixmap.fromImage(image)
            canvas.load_pixmap(pix)
            self.__sceneNode.load_canvas_shapes(nodes)
        canvas.update()

    def update_refer_infer_algorithm(self):
        right_node = self.__right_tree.currentItem()
        parent_node = right_node.parent()
        nodes = get_sub_nodes(parent_node)
        image_path = None
        for node in nodes:
            node_text = node.text(0)
            if node_text in image_path_keys:
                image_path = node.text(1)
                break

        rect_nodes = get_sub_nodes(right_node)
        if image_path is None or not self.__sceneNode.is_rect_param_valid(rect_nodes):
            self.__sceneNode.new_canvas_shapes(rect_nodes)
        else:
            image = QtGui.QImage(image_path)
            pix = QtGui.QPixmap.fromImage(image)
            canvas.load_pixmap(pix)
            self.__sceneNode.load_canvas_shapes([right_node])
        canvas.update()

    def update_right_tree(self, config=None):
        if config is None:
            return
        for key, value in config.items():
            self.__sceneNode.create_complex_node(key, value)

    def double_click_right_tree(self, node, column):
        logger.debug("double_click_right_tree, node: %s, column:%s", node, column)
        canvas.mouse_move_flag = False
        # if column == 0:
        self.__pre_right_tree_key = node.text(0)
        self.__pre_right_tree_value = node.text(1)
        # if column == 2:
        #     self.__pre_right_tree_key

        key = node.text(0)
        file_path = node.text(3)
        if key in image_path_keys:
            reset = False
            if not os.path.exists(file_path):
                reset = True
            self.click_image_path(file_path=file_path, reset_path=reset)

        if key in Number_Key:
            self.__pre_number_value = node.text(1)

        if key in file_path_keys:
            file_path, _ = QFileDialog.getOpenFileName(None, "select file", file_path, "*")
            _, file_name = os.path.split(file_path)
            project_path = g_project_manager.get_project_path()
            project_file_path = os.path.join(project_path, file_name)
            if not os.path.exists(project_file_path):
                shutil.copy(file_path, project_file_path)

            node.setText(1, file_name)  # 应存放文件名
            node.setText(3, project_file_path)

        if key in ['template', 'element']:
            # 点击template和element的时候才会显示ROI的内容
            self.update_canvas()
        elif key in ['refer']:
            self.update_refer_canvas()
        elif key in ['inferROI', 'inferSubROI']:
            self.update_refer_infer_algorithm()
        node.setExpanded(True)

    def double_click_left_tree(self, node, column):
        logger.debug("double click left tree")
        logger.debug("node text %s, column %s", node.text(0), column)
        if column == 0:
            self.__pre_left_tree_key = node.text(0)

        task_name = node.text(0)
        task_id = node.text(1)
        node_type = node.text(2)
        logger.debug("name %s id %s type %s", task_name, task_id, node_type)

        if node_type in [ITEM_TYPE_TASK]:
            try:
                self.__sceneNode.is_r_node_valid()
            except RuntimeError as err:
                # logger.error("err is {}".format(err))
                show_critical_tips("{}".format(err))
                return

            if not self.save_previous_rtree():
                return

            self.load_task(int(task_id))

        tree_mgr.set_mode(Mode.SCENE)

    def click_image_path(self, file_path=None, reset_path=False):
        if reset_path:
            file_path, _ = QFileDialog.getOpenFileName(None, "select file", file_path, "*")
            # 如果没有选择，则直接退出
            if len(file_path) == 0:
                logger.info("give up select image path")
                return

            # 如果选择的不是图像，则提示后，退出
            if not is_image(file_path):
                show_warning_tips("please select a image")
                return

        _, file_name = os.path.split(file_path)
        project_path = ProjectDataManager().get_project_data_path()
        project_file_path = os.path.join(project_path, file_name)
        if not os.path.exists(project_file_path):
            shutil.copy(file_path, project_file_path)
        right_node = self.__right_tree.currentItem()
        right_node.setText(1, project_file_path)
        right_node.setText(3, project_file_path)

        # 画图相关
        # if is_image(file_path):
        frame = QtGui.QImage(project_file_path)
        pix = QtGui.QPixmap.fromImage(frame)
        canvas.load_pixmap(pix)
        canvas.update()

        need_new_shapes = False
        if not self.is_image_path_valid():
            need_new_shapes = True
        if reset_path:
            need_new_shapes = True
        parent = right_node.parent()
        pparent = parent.parent()
        logger.debug("parent: %s pparent: %s", parent.text(0), pparent.text(0))
        # if pparent.text(0) in ['elements']:
        #     nodes = get_sub_nodes(right_node.parent())
        if parent.text(0) == 'refer':
            nodes = get_sub_nodes(right_node.parent())
            nodes_copy = [i for i in nodes]
            for node in nodes_copy:
                if node.text(0) in ['templateLocation']:
                    nodes.remove(node)
        elif pparent.text(0) == 'refer':
            nodes = get_sub_nodes(pparent)
            nodes_copy = [i for i in nodes]
            for node in nodes_copy:
                logger.debug("text is %s", node.text(0))
                if node.text(0) in ['inferROI', 'inferSubROI']:
                    nodes.remove(node)
        else:
            nodes = get_sub_nodes(right_node.parent())

        if need_new_shapes:
            self.__sceneNode.new_canvas_shapes(nodes)
        else:
            self.__sceneNode.load_canvas_shapes(nodes)

        # 0:key, 1:value, 2:type   3:file_path
        parent = right_node.parent()
        if parent is not None:
            parent.setText(3, file_path)

    def change_file_path(self):
        node = self.__right_tree.currentItem()
        if node is None:
            return

        if node.text(0) in image_path_keys:
            self.click_image_path(reset_path=True)
        else:
            pass

    def right_tree_value_changed(self, node, column):
        if node is None:
            logger.info("item value changed failed, current_item is none")
            return
        if canvas.mouse_move_flag:
            logger.info("mouse is moving")
            return

        # def right_tree_value_changed(self, node, column):
        right_tree_value_changed(canvas, node, column, self.__pre_number_value)
        parent = node.parent()
        if parent is None:
            return

        if parent.text(0) in rect_node_keys:
            update_rect_shapes(parent)

    def is_name_valid(self, task_name=None):
        if self.__tasks_node is None:
            logger.error("no tasks node, please check")
            return False
        nodes = get_sub_nodes(self.__tasks_node)
        for node in nodes:
            if node.text(0) == task_name:
                return False
        return True

    def is_image_path_valid(self):
        # find image path in 4th column of left tree
        cur_left_item = self.__left_tree.currentItem()
        # 0:task_name, 1:task_value, 2:reg type, 3:image_path
        image_path = cur_left_item.text(3)
        if not is_image(image_path):
            return False

        return True

    def get_scene_node(self):
        return self.__sceneNode

    def _new_task_node(self, task_name):
        logger.info("new_task")
        # 判断任务名称是否重复
        node = self.__left_tree.currentItem()
        sub_nodes = get_sub_nodes(node)
        for sub_node in sub_nodes:
            if sub_node.text(0) == task_name:
                show_warning_tips('{} has already exist'.format(task_name))
                return False
        # 检查命名是否合法(数字或是英文字符)
        if not is_str_valid(task_name):
            show_warning_tips('{} is not valid(char or num)'.format(task_name))
            return False

        left_tree_root = self.__left_tree.currentItem()
        text = left_tree_root.text(0)
        logger.info("current item 0th text is %s, element　name %s", text, task_name)
        result = self.is_name_valid(task_name)
        # 判断右树是否合法，是否含有无效数字
        try:
            self.__sceneNode.is_r_node_valid()
        except RuntimeError as err:
            # print("err is {}".format(err))
            show_critical_tips("{}".format(err))
            self.update_canvas()
            return False

        if not self.save_previous_rtree():
            return False

        for _ in range(self.__right_tree.topLevelItemCount()):
            self.__right_tree.takeTopLevelItem(0)

        config = self.__sceneNode.new_task_node(task_name)
        self.__tasks_node.addChild(
            create_tree_item(key=task_name, value=config.get('taskID'), node_type=ITEM_TYPE_TASK, edit=False))
        self.__tasks_node.setExpanded(True)

        self.update_right_tree(config=config)
        self.__dlg.set_valid(result)
        tree_mgr.set_mode(Mode.SCENE)

    @staticmethod
    def _save_diff_mode_tree():
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.SCENE and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.SCENE)
        return True

    def save_previous_rtree(self):
        # 保存前一种类型的右树的值
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.SCENE:
            return self._save_diff_mode_tree()

        # 保存当前类型的右树的值
        try:
            self.__sceneNode.is_r_node_valid()
        except RuntimeError as err:
            show_critical_tips("{}".format(err))
            return False

        self.__sceneNode.save_task_node()
        return True
