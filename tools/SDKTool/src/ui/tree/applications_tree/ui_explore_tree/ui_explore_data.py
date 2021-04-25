# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging


logger = logging.getLogger("sdktool")


class UIExploreData(object):
    def __init__(self):
        cwd = os.getcwd()
        self.__auto_label_path = '{}/data/UIExplore/sample'.format(cwd)
        self.__user_label_path = '{}/data/UIExplore/sample'.format(cwd)
        self.__train_sample_path = '{}/data/UIExplore/sample'.format(cwd)
        self.__explore_ret_path = '{}/data/UIExplore/results'.format(cwd)
        self.path_list = [self.__auto_label_path,
                          self.__user_label_path,
                          self.__train_sample_path,
                          self.__explore_ret_path,
                          ]

    def set_auto_label_path(self, path: str):
        self.__auto_label_path = path

    def get_auto_label_path(self):
        return self.__auto_label_path

    def set_usr_label_path(self, path: str):
        self.__user_label_path = path

    def get_usr_label_path(self):
        return self.__user_label_path

    def set_train_sample_path(self, path: str):
        self.__train_sample_path = path

    def get_train_sample_path(self):
        return self.__train_sample_path

    def set_explore_ret_path(self, path):
        self.__explore_ret_path = path

    def get_explore_ret_path(self):
        return self.__explore_ret_path
