# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from .ui_explore_tree.ui_explore_tree import UIExploreTree
from ..tree_manager import tree_mgr
from ....common.singleton import Singleton
from ...utils import Mode
from ...main_window.tool_window import ui


logger = logging.getLogger("sdktool")


class AppTree(metaclass=Singleton):

    def __init__(self):
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__run_node = None
        self.__train_node = None
        self.__test_node = None
        self.__explore_tree = UIExploreTree()
        tree_mgr.set_object(Mode.UI_AUTO_EXPLORE, self)

    def new_ui_explore_node(self):
        self.__explore_tree.build_tree()

    def save_previous_rtree(self):
        self.__explore_tree.save_label_file()  # 保存当前图像的标签
        return True

    def save_labels(self):
        """ 保存当前标签

        :return:
        """
        mode = tree_mgr.get_mode()
        logger.debug("mode is %s", mode)
        if mode != Mode.UI_AUTO_EXPLORE:
            return False

        self.__explore_tree.save_label_file()  # 保存当前图像的标签
        return True
