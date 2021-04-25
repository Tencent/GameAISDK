# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging


logger = logging.getLogger("sdktool")


class TreeManager(object):
    def __init__(self):
        self._pre_tree = None
        self._mode = None
        self.__trees = dict()

    def update(self, tree=None):
        if tree is None:
            logger.error("input tree is None")
            return False

        if self._pre_tree == tree:
            return

        self._pre_tree = tree

        return True

    def set_mode(self, mode: int):
        self._mode = mode

    def get_mode(self):
        return self._mode

    def set_object(self, mode, obj):
        self.__trees[mode] = obj

    def get_object(self, mode):
        return self.__trees.get(mode)


tree_mgr = TreeManager()


def save_current_data():
    """ 在启动服务前，先保存数据

    :return: True/False
    """
    cur_mode = tree_mgr.get_mode()
    cur_tree = tree_mgr.get_object(cur_mode)
    return cur_tree.save_previous_rtree()
