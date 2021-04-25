# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from enum import unique, Enum
from qtpy import QtWidgets

from ....common.define import RUN_NAME, STOP_RECORD, STOP_TRAIN, STOP_TEST, CONFIG_RECORD, START_RECORD, \
    START_TRAIN, TEST_CONFIG, START_TEST, file_path_keys, Number_Key, rect_node_keys
from ..tree_manager import tree_mgr
from ...canvas.ui_canvas import canvas, update_rect_shapes
from ...dialog.tip_dialog import show_warning_tips
from ....common.singleton import Singleton
from ...utils import ui, Mode, set_log_text, create_tree_item, get_tree_top_nodes, right_tree_value_changed
from .train_node import TrainNode
from .test_node import TestNode
from ....project.project_manager import g_project_manager
from ....context.app_context import AppContext

logger = logging.getLogger("sdktool")


@unique
class RunMode(Enum):
    NONE = 0
    CONFIG_RECORD = 1
    START_RECORD = 2
    STOP_RECORD = 3
    START_TRAIN = 4
    STOP_TRAIN = 5
    START_TEST = 6
    STOP_TEST = 7


class RunTree(metaclass=Singleton):
    def __init__(self):
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__run_node = None
        self.__train_node = None
        self.__test_node = None
        self.__mode = RunMode.NONE
        self.__train_node = TrainNode()
        self.__train_node.clear_right_tree_signal.connect(self.save_previous_rtree)
        self.__train_node.log_signal.connect(self._set_log_text)
        self.__train_node.run_signal.connect(self._recv_run_signal)

        self.__test_node = TestNode()
        self.__test_node.clear_right_tree_signal.connect(self.save_previous_rtree)
        self.__test_node.log_signal.connect(self._set_log_text)
        self.__test_node.run_signal.connect(self._recv_run_signal)
        self.__pre_number_value = None

        tree_mgr.set_object(Mode.RUN, self)

    @staticmethod
    def _set_log_text(str_log):
        set_log_text(str_log)

    @staticmethod
    def _save_pre_mode_tree():
        # 保存之前的右树
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.RUN and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            pre_tree.save_previous_rtree()
        tree_mgr.set_mode(Mode.RUN)

    def _new_run_node(self):
        # 检查工程节点是否已经创建
        project_path = g_project_manager.get_project_path()
        if not project_path:
            show_warning_tips("please new project")
            return

        self._save_pre_mode_tree()

        # 检查RUN_NAME节点是否已经创建
        if self.__run_node is None:
            project_node = self.__left_tree.topLevelItem(0)
            self.__run_node = create_tree_item(key=RUN_NAME, edit=False)
            project_node.addChild(self.__run_node)
            project_node.setExpanded(True)

    def new_train_node(self):
        self._save_pre_mode_tree()

        # 创建run节点
        self._new_run_node()
        # 创建 train_node
        self.__train_node.create_node(self.__run_node)

    def new_test_node(self):
        self._save_pre_mode_tree()
        # 创建run节点
        self._new_run_node()
        # 创建test节点
        self.__test_node.create_node(self.__run_node)

    def double_click_left_tree(self, node, column):
        try:
            if node is None:
                logger.error("current node is None, column: %s", column)
                return

            if not self.save_previous_rtree():
                show_warning_tips("save previous tree failed")
                return

            node_type = node.text(2)
            if self.__train_node.is_recording() and node_type != STOP_RECORD:
                show_warning_tips("recording sample is running, please wait or stop it")
                return

            if self.__train_node.is_training() and node_type != STOP_TRAIN:
                show_warning_tips("training sample is running, please wait or stop it")
                return

            if self.__test_node.is_testing() and node_type != STOP_TEST:
                show_warning_tips("testing sdk is running, please wait or stop it")
                return

            if node_type == CONFIG_RECORD:
                self.__train_node.config_record()
                self.__mode = RunMode.CONFIG_RECORD

            elif node_type == START_RECORD:
                self.__train_node.start_record()
                self.__mode = RunMode.START_RECORD

            elif node_type == STOP_RECORD:
                self.__train_node.stop_record()
                self.__mode = RunMode.STOP_RECORD

            elif node_type == START_TRAIN:
                self.__train_node.start_train()
                self.__mode = RunMode.START_TRAIN

            elif node_type == STOP_TRAIN:
                self.__train_node.stop_train()
                self.__mode = RunMode.STOP_TRAIN

            elif node_type == TEST_CONFIG:
                self.__test_node.config()

            elif node_type == START_TEST:
                self.__test_node.start_test()

            elif node_type == STOP_TEST:
                self.__test_node.stop_test()

            tree_mgr.set_mode(Mode.RUN)
        except KeyError as err:
            set_log_text("{}".format(err))

    def double_click_right_tree(self, node, column):
        if node is None:
            logger.error("node is none, column: %s", column)
            return

        node_key = node.text(0)
        if node_key in file_path_keys:
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None,
                                                                 "select action configure file",
                                                                 None,
                                                                 "*.json")

            # 如果未选择，则直接退出
            if len(file_path) == 0:
                logger.info("give up select action configure  file")
                return

            node.setText(1, file_path)

        if node.text(0) in Number_Key:
            self.__pre_number_value = node.text(1)

    @staticmethod
    def _save_diff_mode_tree():
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.SCENE and pre_mode is not None:
            pre_tree = tree_mgr.get_object(pre_mode)
            return pre_tree.save_previous_rtree()

        tree_mgr.set_mode(Mode.RUN)
        return True

    def save_previous_rtree(self):
        # 没有右树，直接返回
        tree_top_nodes = get_tree_top_nodes(self.__right_tree)
        if len(tree_top_nodes) == 0:
            return True

        # 保存前一种类型的右树的值
        pre_mode = tree_mgr.get_mode()
        if pre_mode != Mode.RUN:
            return self._save_diff_mode_tree()

        if self.__mode == RunMode.CONFIG_RECORD:
            self.__train_node.save_record_config()

        return True

    def finish(self):
        self.__train_node.finish()
        self.__test_node.finish()

    @staticmethod
    def _recv_run_signal(run: str, stop_run: str, flag: bool):
        app_ctx = AppContext()
        run_info = app_ctx.get_info("run_info")
        if run_info is None:
            run_info = dict()

        info = dict()
        info['flag'] = flag
        info['stop'] = stop_run
        run_info[run] = info
        app_ctx.set_info("run_info", run_info)

    def right_tree_value_changed(self, node, column):
        if node is None:
            logger.info("item value changed failed, curent_item is none")
            return

        if canvas.mouse_move_flag:
            logger.info("mouse is moving")
            return

        right_tree_value_changed(canvas, node, column, self.__pre_number_value)
        parent = node.parent()
        if parent is None:
            return

        if parent.text(0) in rect_node_keys:
            update_rect_shapes(parent)
