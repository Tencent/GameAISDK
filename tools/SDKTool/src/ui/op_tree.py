# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QTreeWidgetItem

from ..context.app_context import g_app_context
from ..ui.dialog.tip_dialog import show_warning_tips
from ..ui.tree.project_data_manager import ProjectDataManager
from ..ui.tree.project_node import ProjectNode, ROOT_NODE_TYPE_IN_RIGHT_TREE
from ..ui.tree.ai_tree.ai_tree import AITree
from ..ui.tree.run_tree.run_tree import RunTree
from ..ui.tree.ui_tree.ui_tree import UITree
from ..ui.tree.scene_tree.scene_tree import SceneTree
from ..ui.tree.applications_tree.ui_explore_tree.ui_explore_tree import UIExploreTree
from ..ui.tree.tree_manager import tree_mgr
from ..ui.tree.applications_tree.ui_explore_tree.define import TOP_LEVEL_TREE_KEYS, CHILD_ITEM_KEYS
from ..ui.utils import show_work_tree
from ..common.define import Mode, ITEM_TYPE_GAME_OVER, ITEM_TYPE_GAME_START, ITEM_TYPE_GAME_HALL, \
    ITEM_TYPE_GAME_POP_UI, ITEM_TYPE_DEVICE_POP_UI, ITEM_TYPE_UI_SCRIPT_TASKS, ITEM_TYPE_UISTATE_ID, \
    ITEM_TYPE_UI_ELEMENT, SCENE_TASKS_TYPE, ITEM_TYPE_TASK, AI_DEFINE_ACTIONS, AI_OUT_ACTIONS, \
    AI_DEFINE_ACTION, AI_OUT_ACTION, ITEM_TYPE_UI_SCRIPT_TASK, ITEM_TYPE_ELEMENTS, ITEM_TYPE_ELEMENT, \
    ITEM_TYPE_TEMPLATE, ITEM_TYPE_REFER_TASK, UI_NAMES, AI_KEYS, RUN_KEYS, path_keys

logger = logging.getLogger("sdktool")


class OpTree(object):
    def __init__(self):
        self.action_add_ui_element = QtWidgets.QAction()
        self.action_del_ui_element = QtWidgets.QAction()

        self.action_add_scene_element = QtWidgets.QAction()
        self.action_del_scene_element = QtWidgets.QAction()

        self.action_add_script_task = QtWidgets.QAction()
        self.action_del_script_task = QtWidgets.QAction()

        self.action_change_file_path = QtWidgets.QAction()

        self.action_add_template = QtWidgets.QAction()
        self.action_del_template = QtWidgets.QAction()

        self.action_add_refer_template = QtWidgets.QAction()

        self.action_add_task = QtWidgets.QAction()
        self.action_del_task = QtWidgets.QAction()

        self.action_add_refer = QtWidgets.QAction()
        self.action_del_refer = QtWidgets.QAction()

        self.action_detail_conf = QtWidgets.QAction()
        self.action_hidden_Conf = QtWidgets.QAction()

        self.game_action = QtWidgets.QAction()
        self.ai_action = QtWidgets.QAction()

        self.action_delete_action = QtWidgets.QAction()
        self.define_none_action = QtWidgets.QAction()

        self.__ui_tree = UITree()
        self.__scene_tree = SceneTree()
        self.__left_tree = None
        self.__right_tree = None

        # self.__mode = None
        self.__trees = dict()
        self.__trees[Mode.SCENE] = self.__scene_tree
        self.__trees[Mode.UI] = self.__ui_tree
        self.__trees[Mode.AI] = AITree()
        self.__trees[Mode.RUN] = RunTree()
        self.__trees[Mode.UI_AUTO_EXPLORE] = UIExploreTree()

    def define_action(self):
        self.action_add_ui_element.setText("add element")
        self.action_del_ui_element.setText("delete element")

        self.action_add_scene_element.setText("add element")
        self.action_del_scene_element.setText("delete element")

        self.action_add_script_task.setText("add task")
        self.action_del_script_task.setText("delete task")

        self.action_change_file_path.setText("change file path")

        self.action_add_template.setText("add template")
        self.action_del_template.setText("delete template")

        self.action_add_refer_template.setText("add template")

        self.action_add_task.setText("add task")
        self.action_del_task.setText("delete task")

        self.action_add_refer.setText("add refer")
        self.action_del_refer.setText("delete refer")

        self.action_detail_conf.setText("show detail")
        self.action_hidden_Conf.setText("hidden non-critical")

        self.game_action.setText("add action")
        self.ai_action.setText("add action")

        self.action_delete_action.setText('delete action')
        self.define_none_action.setText('add none action')

    def set_slot(self, left_tree=None, right_tree=None):
        if None in [left_tree, right_tree]:
            logger.error("left tree or right tree is valid, please check")
            return

        self.__left_tree = left_tree
        self.__right_tree = right_tree

        left_tree.customContextMenuRequested.connect(lambda: self.set_left_tree_menu(tree_widget=left_tree))
        right_tree.customContextMenuRequested.connect(lambda: self.set_right_tree_menu(tree_widget=right_tree))

        left_tree_root = QTreeWidgetItem(left_tree)
        right_tree_root = QTreeWidgetItem(right_tree)
        logger.debug("left text 0 %s, right text 0 %s", left_tree_root.text(0), right_tree_root.text(0))
        self.action_add_ui_element.triggered.connect(self.__ui_tree.check_add_element)
        self.action_del_ui_element.triggered.connect(lambda: self.__ui_tree.delete_element(left_tree))

        self.action_add_script_task.triggered.connect(lambda: self.__ui_tree.add_task(right_tree))
        self.action_del_script_task.triggered.connect(lambda: self.__ui_tree.del_task(right_tree))
        self.action_detail_conf.triggered.connect(self.__ui_tree.show_detail)
        self.action_hidden_Conf.triggered.connect(self.__ui_tree.show_critical)
        self.action_change_file_path.triggered.connect(self.change_file_path)

        scene_node = self.__scene_tree.get_scene_node()
        self.action_add_scene_element.triggered.connect(scene_node.add_element)
        self.action_del_scene_element.triggered.connect(scene_node.del_element)
        self.action_del_template.triggered.connect(scene_node.del_template)
        self.action_add_template.triggered.connect(scene_node.add_template)
        self.action_add_refer_template.triggered.connect(scene_node.add_refer_template)

        self.action_add_refer.triggered.connect(scene_node.add_refer)
        self.action_del_refer.triggered.connect(scene_node.del_refer)
        self.action_add_task.triggered.connect(self.__scene_tree.new_task)
        self.action_del_task.triggered.connect(self.__scene_tree.del_task)

        ai_tree = AITree()
        self.game_action.triggered.connect(ai_tree.new_game_action)
        self.define_none_action.triggered.connect(ai_tree.new_game_none_action)
        self.ai_action.triggered.connect(ai_tree.new_ai_action)
        self.action_delete_action.triggered.connect(ai_tree.delete_action)

        left_tree.itemDoubleClicked.connect(self.double_click_left_tree)
        right_tree.itemDoubleClicked.connect(self.double_click_right_tree)
        right_tree.itemChanged.connect(self.right_tree_value_changed)

    def set_left_tree_menu(self, tree_widget):
        menu = QtWidgets.QMenu(tree_widget)
        current_item = tree_widget.currentItem()
        if not current_item:
            return

        logger.debug("current item text 0 %s, text 1 %s", current_item.text(0), current_item.text(2))
        menu.clear()
        if current_item:
            if current_item.text(2) in [ITEM_TYPE_GAME_OVER, ITEM_TYPE_GAME_START, ITEM_TYPE_GAME_HALL,
                                        ITEM_TYPE_GAME_POP_UI, ITEM_TYPE_DEVICE_POP_UI]:
                menu.addAction(self.action_add_ui_element)
            elif current_item.text(2) == ITEM_TYPE_UI_SCRIPT_TASKS:
                menu.addAction(self.action_add_script_task)

            elif current_item.text(2) in [ITEM_TYPE_UISTATE_ID, ITEM_TYPE_UI_ELEMENT]:
                menu.addAction(self.action_del_ui_element)

            elif current_item.text(2) == SCENE_TASKS_TYPE:
                menu.addAction(self.action_add_task)
            elif current_item.text(2) == ITEM_TYPE_TASK:
                menu.addAction(self.action_del_task)

            elif current_item.text(2) == AI_DEFINE_ACTIONS:
                menu.addAction(self.game_action)
                menu.addAction(self.define_none_action)
            elif current_item.text(2) == AI_OUT_ACTIONS:
                menu.addAction(self.ai_action)
            elif current_item.text(2) in [AI_DEFINE_ACTION] or current_item.text(2) in [AI_OUT_ACTION]:
                menu.addAction(self.action_delete_action)
            else:
                if tree_mgr.get_mode() == Mode.UI_AUTO_EXPLORE:
                    self.__trees[Mode.UI_AUTO_EXPLORE].on_right_menu()

            menu.exec_(QtGui.QCursor.pos())

    def set_right_tree_menu(self, tree_widget):
        menu = QtWidgets.QMenu(tree_widget)
        current_item = tree_widget.currentItem()
        if current_item is None:
            logger.error("currentItem is none, please check")
            return
        logger.info("current item text 0 %s, text 1 %s", current_item.text(0), current_item.text(2))
        menu.clear()
        key = current_item.text(0)
        if current_item.text(2) == ITEM_TYPE_UI_SCRIPT_TASKS:
            menu.addAction(self.action_add_script_task)
        if current_item.text(2) == ITEM_TYPE_UI_SCRIPT_TASK:
            menu.addAction(self.action_del_script_task)
        elif current_item.text(2) in [ITEM_TYPE_UI_ELEMENT]:
            menu.addAction(self.action_del_ui_element)
        elif key in path_keys:
            menu.addAction(self.action_change_file_path)
        elif current_item.text(2) == ITEM_TYPE_ELEMENTS:
            menu.addAction(self.action_add_scene_element)
        elif current_item.text(2) == ITEM_TYPE_ELEMENT:
            menu.addAction(self.action_add_template)
            menu.addAction(self.action_del_scene_element)
            menu.addAction(self.action_add_refer)
        elif current_item.text(2) == ITEM_TYPE_TEMPLATE:
            menu.addAction(self.action_del_template)
        elif current_item.text(2) == ITEM_TYPE_REFER_TASK:
            menu.addAction(self.action_del_refer)
            menu.addAction(self.action_add_refer_template)
        menu.addAction(self.action_detail_conf)
        menu.addAction(self.action_hidden_Conf)
        menu.exec_(QtGui.QCursor.pos())

    def double_click_left_tree(self, node, column):
        if node is None:
            return

        # 判断是否有正在运行的进程
        run_info = g_app_context.get_info('run_info') or dict()
        for key, value in run_info.items():
            flag = value.get('flag')
            stop = value.get('stop')
            if stop != node.text(0) and flag:
                show_warning_tips("{} process is running, please stop it first or wait it finish".format(key))
                return

        parent = node.parent()
        if parent is None:
            project_name = ProjectDataManager().get_name()
            if node.text(0) == project_name:
                if ProjectNode().load_project_node():
                    tree_mgr.set_mode(Mode.PROJECT)
            return

        # # 保存工程节点的右树
        parent_text = parent.text(0)
        logger.debug('parent text %s', parent_text)

        if parent_text == 'tasks':
            self.__scene_tree.double_click_left_tree(node, column)
            tree_mgr.set_mode(Mode.SCENE)

        elif parent_text in UI_NAMES:
            logger.debug("parent text %s set phone flag is %s", parent_text, False)
            self.__ui_tree.double_click_left_tree(node, column)
            tree_mgr.set_mode(Mode.UI)

        elif parent_text in AI_KEYS:
            ai_tree = AITree()
            ai_tree.double_click_left_tree(node, column)
            tree_mgr.set_mode(Mode.AI)

        elif parent_text in RUN_KEYS:
            run_tree = RunTree()
            run_tree.double_click_left_tree(node, column)
            tree_mgr.set_mode(Mode.RUN)

        elif parent_text in TOP_LEVEL_TREE_KEYS or parent_text in [CHILD_ITEM_KEYS[2][0]]:
            ui_explore_tree = UIExploreTree()
            ui_explore_tree.double_click_left_tree(node, column)
            tree_mgr.set_mode(Mode.UI_AUTO_EXPLORE)

        else:
            node.setExpanded(True)

        # 展开正在当前选中的树，收缩其他的树节点
        mode = tree_mgr.get_mode()
        show_work_tree(self.__left_tree, mode)

    def double_click_right_tree(self, node, column):
        # 双击后不缩放节点, todo:无效
        left_node = self.__left_tree.currentItem()
        if left_node is None:
            show_warning_tips('请先在左树添加一个节点[UI|AI|Scene|Applications]!')
            return

        r_top_level_item = self.__right_tree.topLevelItem(0)
        if r_top_level_item and r_top_level_item.text(2) == ROOT_NODE_TYPE_IN_RIGHT_TREE:
            ProjectNode().update_right_tree()
            return

        parent = left_node.parent()
        if parent is None:
            logger.error("left node parent is None")
            return
        parent_text = parent.text(0)
        cur_text = left_node.text(0)

        if "tasks" in [parent_text, cur_text]:
            self.__scene_tree.double_click_right_tree(node, column)
            tree_mgr.set_mode(Mode.SCENE)

        elif parent_text in UI_NAMES or cur_text in UI_NAMES:
            self.__ui_tree.double_click_right_tree(node, column)
            tree_mgr.set_mode(Mode.UI)

        elif parent_text in AI_KEYS:
            ai_tree = AITree()
            ai_tree.double_click_right_tree(node, column)
            tree_mgr.set_mode(Mode.AI)

        elif parent_text in RUN_KEYS:
            run_tree = RunTree()
            run_tree.double_click_right_tree(node, column)
            tree_mgr.set_mode(Mode.RUN)

        elif parent_text in TOP_LEVEL_TREE_KEYS or parent_text in [CHILD_ITEM_KEYS[2][0]]:
            explore_tree = UIExploreTree()
            explore_tree.double_click_right_tree(node, column)

        else:
            logger.error("unknown node %s parent node %s", cur_text, parent_text)

        # logger.debug("************current mode is {}***************".format(self.__mode))

        node.setExpanded(True)

    def right_tree_value_changed(self, node, column):
        left_node = self.__left_tree.currentItem()
        if left_node is None:
            return
        parent = left_node.parent()
        if parent is None:
            return

        parent_text = parent.text(0)
        cur_text = left_node.text(0)

        if "tasks" in [parent_text, cur_text]:
            self.__scene_tree.right_tree_value_changed(node, column)
        elif parent_text in UI_NAMES or cur_text in UI_NAMES:
            self.__ui_tree.right_tree_value_changed(node, column)
        elif parent_text in AI_KEYS:
            ai_tree = AITree()
            ai_tree.right_tree_value_changed(node, column)

        elif parent_text in RUN_KEYS:
            run_tree = RunTree()
            run_tree.right_tree_value_changed(node, column)
            tree_mgr.set_mode(Mode.RUN)

        elif parent_text in TOP_LEVEL_TREE_KEYS or parent_text in [CHILD_ITEM_KEYS[2][0]]:
            explore_tree = UIExploreTree()
            explore_tree.right_tree_value_changed(node, column)
            tree_mgr.set_mode(Mode.UI_AUTO_EXPLORE)

        else:
            logger.error("unknown node %s parent node %s", cur_text, parent_text)

    def change_file_path(self):
        mode = tree_mgr.get_mode()
        if mode == Mode.UI:
            self.__ui_tree.change_file_path()
        elif mode == Mode.SCENE:
            self.__scene_tree.change_file_path()

        else:
            logger.error("unknown node")
