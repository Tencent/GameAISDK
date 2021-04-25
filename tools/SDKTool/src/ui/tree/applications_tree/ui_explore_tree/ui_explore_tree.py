# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import os
import shutil
from collections import OrderedDict
import json

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QIcon

from .....common.define import AI_CONFIG_ALGORITHM_PATH, RunTypeText
from .....config_manager.ui_auto_explore import ui_explore_api as ueapi
from .....ui.tree.applications_tree.ui_explore_tree.define import QICON_IMGS, CHILD_ITEM_KEYS, TOP_LEVEL_TREE_KEYS, \
    TRAIN_PARAMS, RUN_PARAMS, int_Number_Key, BOOL_PARAMS_KEYS, PATH_NAME_LIST
from .....ui.tree.tree_manager import tree_mgr
from .....common.singleton import Singleton
from .....ui.dialog.tip_dialog import show_warning_tips
from .....ui.utils import create_tree_item, get_sub_nodes, get_file_list, Mode, get_tree_top_nodes, BOOL_FLAGS

from .....ui.tree.applications_tree.ui_explore_tree.ui_explore_node import UIExploreNode
from .....ui.main_window.tool_window import ui
from .....project.project_manager import g_project_manager


logger = logging.getLogger("sdktool")


class UIExploreTree(metaclass=Singleton):
    def __init__(self):
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__run_node = None
        self.__train_node = None
        self.__test_node = None
        self.__label_path = None
        self.__uiexplore_node = None

    def build_tree(self):
        self.__uiexplore_node = UIExploreNode()

        tree = self.__left_tree
        # 左树处理
        project_node = tree.topLevelItem(0)
        project_name = project_node.text(0)
        if not project_name:
            show_warning_tips("please new project first")
            return

        if g_project_manager.get_run_type() != RunTypeText.AUTO_EXPLORER:
            show_warning_tips("please select AutoExplore runtype first")
            return

        # 需删除'cfg/task/agent/Algorithm.json'，agentai的加载插件的逻辑需要
        project_path = g_project_manager.get_project_path()
        algorithm_json_path = os.path.join(project_path, AI_CONFIG_ALGORITHM_PATH)
        if os.path.exists(algorithm_json_path):
            os.remove(algorithm_json_path)

        explore_node = None
        nodes = get_sub_nodes(project_node)
        if len(nodes) == 0:
            explore_node = create_tree_item(key="UIExplore", edit=False)
            project_node.addChild(explore_node)
        elif len(nodes) == 1 and nodes[0].text(0) == 'UIExplore':
            explore_node = nodes[0]
        else:
            show_warning_tips("error node type")
            return

        project_node.setExpanded(True)

        # 创建样本目录
        # step 0 配置样本
        config_label_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[0], edit=False)

        label_path = os.path.join(project_path, 'data', 'samples')
        if not os.path.exists(label_path):
            os.mkdir(label_path)
        self.__label_path = label_path

        # 设置label路径
        ueapi.auto_save_label_path(label_path)
        ueapi.user_save_label_path(label_path)
        ueapi.explore_train_save_data_path(label_path)
        ueapi.explore_run_save_data_path(label_path)

        pathItem = create_tree_item(key=CHILD_ITEM_KEYS[0][0], value=self.__label_path, edit=True)
        pathItem.setIcon(0, QIcon(QICON_IMGS[0][0]))
        config_label_item.addChild(pathItem)

        # 实时产生样本
        snapshot_item = create_tree_item(key=CHILD_ITEM_KEYS[0][1], value=self.__label_path, edit=False)
        snapshot_item.setIcon(0, QIcon(QICON_IMGS[0][1]))
        config_label_item.addChild(snapshot_item)

        explore_node.addChild(config_label_item)
        config_label_item.setExpanded(True)

        # step 1 样本自动标记
        auto_label_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[1], edit=False)

        start_auto_label_item = create_tree_item(key=CHILD_ITEM_KEYS[1][0], value=self.__label_path, edit=False)
        start_auto_label_item.setIcon(0, QIcon(QICON_IMGS[1][0]))
        auto_label_item.addChild(start_auto_label_item)

        explore_node.addChild(auto_label_item)
        auto_label_item.setExpanded(True)

        # step 2 样本重标记
        relabel_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[2], edit=False)

        usrLabelSampleTree = create_tree_item(key=CHILD_ITEM_KEYS[2][0], value=self.__label_path, edit=False)
        usrLabelSampleTree.setIcon(0, QIcon(QICON_IMGS[2][0]))
        relabel_item.addChild(usrLabelSampleTree)
        get_file_list(self.__label_path, usrLabelSampleTree, 1)
        self.__uiexplore_node.set_image_list()

        zip_sample_item = create_tree_item(key=CHILD_ITEM_KEYS[2][1], value=self.__label_path, edit=False)
        zip_sample_item.setIcon(0, QIcon(QICON_IMGS[2][1]))
        relabel_item.addChild(zip_sample_item)

        explore_node.addChild(relabel_item)
        relabel_item.setExpanded(True)

        # step 3 训练
        train_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[3], edit=False)

        set_train_param_item = create_tree_item(key=CHILD_ITEM_KEYS[3][0], value=self.__label_path, edit=False)
        set_train_param_item.setIcon(0, QIcon(QICON_IMGS[3][0]))
        train_item.addChild(set_train_param_item)
        # train_item.addChild(start)

        start_train_item = create_tree_item(key=CHILD_ITEM_KEYS[3][1], value=self.__label_path, edit=False)
        start_train_item.setIcon(0, QIcon(QICON_IMGS[3][1]))
        train_item.addChild(start_train_item)

        stop_train_item = create_tree_item(key=CHILD_ITEM_KEYS[3][2], value=self.__label_path, edit=False)
        stop_train_item.setIcon(0, QIcon(QICON_IMGS[3][2]))
        train_item.addChild(stop_train_item)

        analysis_result_item = create_tree_item(key=CHILD_ITEM_KEYS[3][3], value=self.__label_path, edit=False)
        analysis_result_item.setIcon(0, QIcon(QICON_IMGS[3][3]))
        train_item.addChild(analysis_result_item)

        explore_node.addChild(train_item)
        train_item.setExpanded(True)

        # step 4 执行
        run_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[4], edit=False)

        set_run_param_item = create_tree_item(key=CHILD_ITEM_KEYS[4][0], value=self.__label_path, edit=False)
        set_run_param_item.setIcon(0, QIcon(QICON_IMGS[4][0]))
        run_item.addChild(set_run_param_item)

        start_run_item = create_tree_item(key=CHILD_ITEM_KEYS[4][1], value=self.__label_path, edit=False)
        start_run_item.setIcon(0, QIcon(QICON_IMGS[4][1]))
        run_item.addChild(start_run_item)

        stop_run_item = create_tree_item(key=CHILD_ITEM_KEYS[4][2], value=self.__label_path, edit=False)
        stop_run_item.setIcon(0, QIcon(QICON_IMGS[4][2]))
        run_item.addChild(stop_run_item)

        explore_node.addChild(run_item)
        run_item.setExpanded(True)

        # step 5 UI自动化探索结果
        result_item = create_tree_item(key=TOP_LEVEL_TREE_KEYS[5], edit=False)
        result1 = create_tree_item(key=CHILD_ITEM_KEYS[5][0], value=self.__label_path, edit=False)
        result1.setIcon(0, QIcon(QICON_IMGS[5][0]))
        result_item.addChild(result1)
        result2 = create_tree_item(key=CHILD_ITEM_KEYS[5][1], value=self.__label_path, edit=False)
        result2.setIcon(0, QIcon(QICON_IMGS[5][1]))
        result_item.addChild(result2)
        result3 = create_tree_item(key=CHILD_ITEM_KEYS[5][2], value=self.__label_path, edit=False)
        result3.setIcon(0, QIcon(QICON_IMGS[5][2]))
        result_item.addChild(result3)

        explore_node.addChild(result_item)
        result_item.setExpanded(True)

        # 设置属性
        params = ueapi.ui_explore_config_get()
        output_dir = 'data/run_result'
        if params and 'UiExplore' in params:
            output_dir = params['UiExplore'].get('OutputFolder')
        output_dir = os.path.join(project_path, output_dir)
        if os.path.exists(output_dir):
            graph_dir = os.path.join(output_dir, 'Graph')
            logger.info('set explore result:%s', graph_dir)
            ueapi.explore_result_save_path(graph_dir)

        explore_node.setExpanded(True)
        self.__left_tree.setCurrentItem(explore_node)
        tree_mgr.set_mode(Mode.UI_AUTO_EXPLORE)

    def double_click_left_tree(self, node, column):
        logger.debug("double click left tree")
        logger.debug("node text %s, column %s", node.text(0), column)

        self.__uiexplore_node.reset_state()
        self.__uiexplore_node.update_right_tree(node)
        tree_mgr.set_mode(Mode.UI_AUTO_EXPLORE)

    @staticmethod
    def open_directory():
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        dialog.setWindowTitle('从指定文件夹复制样本:')
        name = None
        if dialog.exec():
            name = dialog.selectedFiles()[0]
            logger.debug("name is %s, length %s", name, len(name))
        return name

    @staticmethod
    def save_label_file():
        top_nodes = get_tree_top_nodes(ui.tree_widget_right)
        file_name_item = None
        scene_item = None
        labels_item = None
        for node in top_nodes:
            if node.text(0) == "fileName":
                file_name_item = node
            elif node.text(0) == "scene":
                scene_item = node
            elif node.text(0) == 'labels':
                labels_item = node

        if None in [file_name_item, scene_item, labels_item]:
            logger.error("one of items(file name: %s, scene: %s, labels: %s) is not found",
                         file_name_item, scene_item, labels_item)
            return

        file_name = file_name_item.text(1)
        scene_name = scene_item.text(1)

        # 构造标签的字典
        label_json_dict = {}
        label_json_dict["fileName"] = file_name
        label_json_dict["scene"] = scene_name
        label_json_dict["labels"] = list()

        sub_labes = get_sub_nodes(labels_item)
        # 对于每个框，都要存储对应的项
        for node in sub_labes:
            label_dict = OrderedDict()

            # 填每个框对应的字段
            label_dict["label"] = node.text(0)
            label_dict["name"] = ""
            label_dict["clickNum"] = 0

            node_x = node.child(0)
            node_y = node.child(1)
            node_w = node.child(2)
            node_h = node.child(3)
            # 填框的坐标
            label_dict["x"] = int(node_x.text(1))
            label_dict["y"] = int(node_y.text(1))
            label_dict["w"] = int(node_w.text(1))
            label_dict["h"] = int(node_h.text(1))
            if label_dict['w'] == 0 or label_dict['h'] == 0:
                continue

            label_json_dict["labels"].append(label_dict)

        # 存储标签为json文件
        json_file_name = file_name_item.text(2)
        json_file_name = json_file_name[: json_file_name.rfind('.')] + ".json"

        with open(json_file_name, "w") as f:
            json.dump(label_json_dict, f, indent=4, separators=(',', ':'))

    def acc_image_index(self):
        self.__uiexplore_node.usr_label_image.acc_image_index()

    def dec_image_index(self):
        self.__uiexplore_node.usr_label_image.dec_image_index()

    def load_label_image(self):
        image_file = self.__uiexplore_node.usr_label_image.get_cur_image_name()
        if image_file:
            self.__uiexplore_node.load_label_image(image_file)

    @staticmethod
    def right_tree_value_changed(node, column):
        logger.debug("right_tree_value_changed, node: %s, column: %s", node, column)
        key = node.text(0)
        value = node.text(1)
        if key in TRAIN_PARAMS.keys():
            params = ueapi.explore_train_get_params()
            if key in int_Number_Key:
                value = int(value)
            params[key] = value
            ueapi.explore_train_save_params(params)
        if key in RUN_PARAMS.keys():
            params = ueapi.explore_run_get_params()
            if key in int_Number_Key:
                value = int(value)
            if key in BOOL_PARAMS_KEYS:
                if value in BOOL_FLAGS and value == BOOL_FLAGS[1]:
                    value = False
                else:
                    value = True
            params[key] = value
            ueapi.explore_run_save_params(params)

    def double_click_right_tree(self, node, column):
        logger.debug("double_click_right_tree, node: %s, column: %s", node, column)
        key = node.text(0)
        value = node.text(1)

        # 如果没有父节点，则不做操作，只对子节点进行操作
        logger.debug("update right tree, text0 %s, text1 %s", key, value)
        if key in PATH_NAME_LIST:
            src_folder = self.open_directory()
            logger.debug("directory is %s", src_folder)
            if src_folder is not None:
                dst_folder = value
                for f_item in os.listdir(src_folder):
                    dst_f_path = os.path.join(dst_folder, f_item)
                    if not os.path.exists(dst_f_path):
                        f_path = os.path.join(src_folder, f_item)
                        if os.path.isfile(f_path):
                            shutil.copy2(f_path, dst_folder)
                        elif os.path.isdir(f_path):
                            shutil.copytree(f_path, dst_f_path)

    def on_right_menu(self):
        self.__uiexplore_node.on_right_click()
