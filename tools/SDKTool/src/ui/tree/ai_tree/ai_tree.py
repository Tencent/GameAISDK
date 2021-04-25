# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import traceback
import shutil
import cv2

from PyQt5 import QtGui
from PyQt5.QtWidgets import QFileDialog

from ..tree_manager import tree_mgr
from ....common.define import Enum, Mode, unique, AI_ALGORITHM, AI_DEFINE_ACTION, AI_GAME_BEGIN, \
    AI_GAME_OVER, AI_OUT_ACTION, AI_MODEL_PARAMETER, AI_RESOLUTION, rect_node_keys, image_path_keys, \
    Number_Key, point_node_keys, need_value_keys, positive_integer_value_keys
from ....common.singleton import Singleton
from ....config_manager.ai.ai_manager import AIManager
from ....context.app_context import AppContext
from .algorithm_node import AlgorithmNode
from ....config_manager.ai.ai_algorithm import AIAlgorithmType
from .action_node import ActionNode
from .state_node import StateNode
from .parameter_node import ParameterNode
from .resolution_node import ResolutionNode
from ...main_window.tool_window import ui
from ...canvas.shape import Shape
from ...canvas.ui_canvas import canvas, reset_canvas_roi, reset_canvas_action, update_rect_shapes
from ...dialog.tip_dialog import show_warning_tips, show_question_tips
from ....ui.tree.project_data_manager import ProjectDataManager
from ...utils import get_sub_nodes, is_image, get_tree_top_nodes, ExecResult, right_tree_value_changed
from ....subprocess_service.subprocess_service_manager import backend_service_manager as bsa

logger = logging.getLogger("sdktool")


@unique
class AIMode(Enum):
    NONE = 0
    ALGORITHM = 1
    ACTION_GAME = 2
    ACTION_AI = 3
    STATE_GAME_OVER = 4
    PARAMETER = 5
    RESOLUTION = 6
    STATE_GAME_START = 7


class AITree(metaclass=Singleton):
    def __init__(self):
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right

        self.__mode = AIMode.NONE
        self.pre_number_value = None

        self.action_node = None
        self.algorithm_node = None
        self.state_node = None
        self.parameter_node = None
        self.resolution_node = None

        tree_mgr.set_object(Mode.AI, self)

    def __init_nodes(self):
        """ 创建AI节点下的各类型节点

        :attention: 需在create_sub_nodes函数调用前动态创建，否则在重加载项目时会出问题
        :return:
        """
        self.action_node = ActionNode()
        self.action_node.clear_right_tree_signal.connect(self.save_previous_rtree)

        self.algorithm_node = AlgorithmNode(self.action_node)
        self.algorithm_node.clear_right_tree_signal.connect(self.save_previous_rtree)

        self.state_node = StateNode()
        self.state_node.clear_right_tree_signal.connect(self.save_previous_rtree)

        self.parameter_node = ParameterNode()
        self.parameter_node.clear_right_tree_signal.connect(self.save_previous_rtree)

        self.resolution_node = ResolutionNode()
        self.resolution_node.clear_right_tree_signal.connect(self.save_previous_rtree)

    def new_node(self):
        result = ExecResult()
        if not self.save_previous_rtree(result):
            logger.error("save previous right tree failed")
            return False

        project_node = self.__left_tree.topLevelItem(0)
        if len(project_node.text(0)) == 0:
            show_warning_tips("please new project first")
            return False

        nodes = get_sub_nodes(project_node)
        for node in nodes:
            if node.text(0) == 'AI':
                if not show_question_tips('已有AI节点，是否覆盖'):
                    return
                break

        if bsa.has_service_running():
            show_warning_tips("已有服务在运行，请先停止后再新建AI节点")
            return

        mgr = AIManager()
        mgr.clear_config()
        mgr.init_config()

        # 需默认加载缺省IM算法的配置，否则会在工程保存时，把IM算法参数文件的数据洗掉
        mgr.set_ai_type(AIAlgorithmType.IM)
        mgr.load_learning_config(AIAlgorithmType.IM)

        self.__right_tree.clear()
        self.create_sub_nodes()
        return True

    def create_sub_nodes(self):
        self.__init_nodes()
        self.algorithm_node.create_node()
        self.action_node.create_node()
        self.state_node.create_node()
        self.parameter_node.create_node()
        self.parameter_node.set_ai_tree(self)
        return True

    @staticmethod
    def _save_diff_mode_tree():
        # 保存之前的右树
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.AI and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.AI)
        return True

    def load_ai(self, project_dir=None):
        logger.debug('load ai project_dir: %s', project_dir)
        self.create_sub_nodes()

    def new_game_action(self):
        if not self.project_is_ready():
            show_warning_tips("please new project and connect phone first")

            return

        if not self._save_diff_mode_tree():
            show_warning_tips("save previous right tree failed")

            return

        if self.action_node.new_game_action():
            self.__mode = AIMode.ACTION_GAME

    def new_game_none_action(self):
        if not self.project_is_ready():
            show_warning_tips("please new project and connect phone first")

            return

        if not self._save_diff_mode_tree():
            show_warning_tips("save previous right tree failed")

            return

        self.action_node.new_game_none_action()
        self.__mode = AIMode.ACTION_GAME

    def new_ai_action(self):
        if not self.project_is_ready():
            show_warning_tips("please new project and connect phone first")

            return

        if not self._save_diff_mode_tree():
            show_warning_tips("save previous right tree failed")

            return

        if self.action_node.new_ai_action():
            self.__mode = AIMode.ACTION_AI

    def delete_action(self):
        self.action_node.delete_action()

    def double_click_left_tree(self, node, column):
        if node is None:
            logger.error("current node is None， column: %s", column)
            return

        parent = node.parent()
        if parent is None:
            logger.warning("parent node is None")
            return

        if not self.save_previous_rtree():
            show_warning_tips("save previous right tree failed")
            return

        tree_mgr.set_mode(Mode.AI)

        node_type = node.text(2)
        if node_type == AI_ALGORITHM:
            self.algorithm_node.load(node)
            self.__mode = AIMode.ALGORITHM

        if node_type == AI_DEFINE_ACTION:
            self.action_node.load_game_action(node)
            self.__mode = AIMode.ACTION_GAME

        if node_type == AI_OUT_ACTION:
            self.action_node.load_ai_action(node)
            self.__mode = AIMode.ACTION_AI

        if node_type == AI_GAME_BEGIN:
            self.state_node.load_game_begin()
            self.__mode = AIMode.STATE_GAME_START

        if node_type == AI_GAME_OVER:
            self.state_node.load_game_over()
            self.__mode = AIMode.STATE_GAME_OVER

        if node_type == AI_MODEL_PARAMETER:
            self.parameter_node.load_model_parameter()
            self.__mode = AIMode.PARAMETER

        if node_type == AI_RESOLUTION:
            self.resolution_node.load_resolution()
            self.__mode = AIMode.RESOLUTION

        logger.info('current ai mode:%s', self.__mode)

    @staticmethod
    def __get_reset(file_path):
        return os.path.exists(file_path)

    def double_click_right_tree(self, node, column):
        logger.debug('double_click_right_tree, column: %s', column)
        text = node.text(0)
        if text in rect_node_keys:
            self.update_canvas()

        elif text in Number_Key:
            self.pre_number_value = node.text(1)

        key = node.text(0)

        if key in image_path_keys:
            file_path = node.text(1)
            # if not file_path:
            #     file_path = node.text(1)
            # reset = self.__get_reset(file_path)
            self.click_image_path(file_path=file_path)

    def click_image_path(self, file_path=None):
        reset_path = False
        if not file_path or not os.path.exists(file_path):
            reset_path = True
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
        data_path = ProjectDataManager().get_project_data_path()
        project_file_path = os.path.join(data_path, file_name)
        if not os.path.exists(project_file_path):
            shutil.copy(file_path, project_file_path)
        node = self.__right_tree.currentItem()
        node.setText(1, project_file_path)
        # node.setText(3, project_file_path)

        frame = QtGui.QImage(project_file_path)
        pix = QtGui.QPixmap.fromImage(frame)
        canvas.load_pixmap(pix)
        canvas.update()

        nodes = get_sub_nodes(node.parent())

        self.action_node.new_canvas_shapes(nodes)

        parent = node.parent()
        if parent is not None:
            parent.setText(3, file_path)

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

    def is_rect_param_valid(self, nodes=None):
        if nodes is None:
            cur_node = self.__right_tree.currentItem()
            nodes = get_sub_nodes(cur_node)

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

    def new_canvas_shapes(self, nodes):
        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.mode = canvas.CREATE
        if nodes is None:
            cur_node = self.__right_tree.currentItem()
            nodes = get_sub_nodes(cur_node)

        for node in nodes:
            if node.text(0) in rect_node_keys:
                canvas.set_rect_tree_item(node)
                canvas.current_model.append(Shape.RECT)
                canvas.set_editing(False)
            elif node.text(0) in point_node_keys:
                canvas.set_editing(False)
                canvas.current_model.append(Shape.POINT)
                canvas.set_point_tree_item(node)

    def load_canvas_shapes(self, nodes):
        shapes = []
        if nodes is None:
            cur_node = self.__right_tree.currentItem()
            nodes = get_sub_nodes(cur_node)
        for node in nodes:
            key = node.text(0)
            shape = None
            if key in rect_node_keys:
                canvas.set_rect_tree_item(node)
                canvas.set_editing()
                shape = reset_canvas_roi(node)
            if key in point_node_keys:
                shape = reset_canvas_action(node)

            if shape is not None:
                shapes.append(shape)
                canvas.shape_tree[shape] = node

        canvas.load_shapes(shapes)
        canvas.update()
        app_ctx = AppContext()
        app_ctx.set_info("phone", False)

    def update_canvas(self):
        # canvas.reset_state()
        canvas.reset_shapes()
        new_shapes = False
        image_path = self.find_image_path()
        right_node = self.__right_tree.currentItem()
        nodes = get_sub_nodes(right_node)
        if image_path is None:
            new_shapes = True
        elif not self.is_rect_param_valid():
            new_shapes = True
        else:
            new_shapes = False

        if new_shapes:
            self.new_canvas_shapes(nodes)
        else:
            image = QtGui.QImage(image_path)
            pix = QtGui.QPixmap.fromImage(image)
            canvas.load_pixmap(pix)
            self.load_canvas_shapes(nodes)
        canvas.update()

    def save_previous_rtree(self, result=None):
        # 判断右树是否存在节点
        top_level_nodes = get_tree_top_nodes(self.__right_tree)
        if len(top_level_nodes) == 0:
            return True

        # 保存之前的右树
        pre_mode = tree_mgr.get_mode()
        logger.debug("pre mode is %s", pre_mode)
        if pre_mode != Mode.AI:
            return self._save_diff_mode_tree()

        if result is None:
            result = ExecResult()
        try:
            self.check_right_tree()
        except RuntimeError as err:
            exp = traceback.format_exc()
            logger.error(exp)
            show_warning_tips("{}".format(err))

            result.flag = False
            return False

        logger.debug("save right tree")
        if self.__mode == AIMode.ACTION_GAME:
            self.action_node.save_game_action()
        elif self.__mode == AIMode.ACTION_AI:
            self.action_node.save_ai_action()
        elif self.__mode == AIMode.STATE_GAME_START:
            self.state_node.save_game_begin()
        elif self.__mode == AIMode.STATE_GAME_OVER:
            self.state_node.save_game_over()
        elif self.__mode == AIMode.PARAMETER:
            self.parameter_node.save_parameter()
        elif self.__mode == AIMode.RESOLUTION:
            self.resolution_node.save_resolution()

        return True

    @staticmethod
    def project_is_ready():
        project_data = ProjectDataManager()
        return project_data.is_ready()

    def save_ai(self):
        mode = tree_mgr.get_mode()
        if mode != Mode.AI:
            return

        result = ExecResult()
        self.save_previous_rtree(result)
        return result.flag

    def check_right_tree(self, root=None):
        if root is None:
            nodes = get_tree_top_nodes(self.__right_tree)
        else:
            nodes = get_sub_nodes(root)

        for node in nodes:
            text0 = node.text(0)
            text1 = node.text(1)
            logger.debug("text 0 %s text 1 %s", text0, text1)
            if node.text(0) in image_path_keys:
                if not is_image(node.text(1)):
                    show_warning_tips("{} should have a right value".format(node.text(0)))
                    return

            if node.text(0) in need_value_keys and len(node.text(1)) == 0:
                show_warning_tips("{} should have value".format(node.text(0)))
                return
            if node.text(0) in positive_integer_value_keys and int(node.text(1)) <= 0:
                show_warning_tips("{} should have a positive integer value".format(node.text(0)))
                return

            if node.childCount() > 0:
                self.check_right_tree(node)

    @staticmethod
    def set_input_size(node, w, h):
        """ 修改inputHeight和inputWidth的数值

        :param node:
        :param w:
        :param h:
        :return:
        """
        def find_node(node, node_key):
            text = node.text(0)
            if text == node_key:
                return node

            cnt = node.childCount()
            for i in range(cnt):
                child_node = node.child(i)
                target_node = find_node(child_node, node_key)
                if target_node:
                    return target_node

            return None

        # 找到根节点
        node_tree = node.treeWidget()
        topLevelItemCount = node_tree.topLevelItemCount()
        for i in range(topLevelItemCount):
            topLevelItem = node_tree.topLevelItem(i)  # network 节点
            # 找到inputHeight和inputWidth这两个节点
            input_width_node = find_node(topLevelItem, 'inputWidth')
            input_height_node = find_node(topLevelItem, 'inputHeight')

            if input_width_node and input_height_node:
                long_edge = max(int(input_width_node.text(1)), int(input_height_node.text(1)))
                short_edge = int(long_edge * min(w, h) / max(w, h))
                if w > h:
                    input_width_node.setText(1, str(long_edge))
                    input_height_node.setText(1, str(short_edge))
                else:
                    input_width_node.setText(1, str(short_edge))
                    input_height_node.setText(1, str(long_edge))

                break

    def right_tree_value_changed(self, node, column):
        if node is None:
            logger.info("item value changed failed, curent_item is none")
            return
        if node.text(0) == 'path':
            logger.info('path changed')
            img_path = node.text(1)
            if img_path and os.path.exists(img_path):
                img_data = cv2.imread(img_path)
                if img_data is not None:  # 修改inputHeight和inputWidth的数值
                    h, w = img_data.shape[:2]
                    self.set_input_size(node, w, h)

        if canvas.mouse_move_flag:
            logger.info("mouse is movinging")
            return

        right_tree_value_changed(canvas, node, column, self.pre_number_value)
        parent = node.parent()
        if parent is None:
            return

        if parent.text(0) in rect_node_keys:
            update_rect_shapes(parent)
