# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
from ....config_manager.common.utils import load_file, save_file, load_json_file, save_json_file


class ExploreTrain(object):

    def __init__(self, logger=None):
        self.__train_params_dict = {}
        self.__train_data_path = None
        self.__train_params_file_path = None
        self._logger = logger

    @property
    def train_data_path(self):
        return self.__train_data_path

    @train_data_path.setter
    def train_data_path(self, train_data_path):
        if not isinstance(train_data_path, str):
            msg = "train_data_path type error, only support str, type: {}".format(type(train_data_path))
            print(msg) if self._logger is None else self._logger.info(msg)
            return

        self.__train_data_path = train_data_path
        self.__train_params_file_path = os.path.abspath(os.path.join(self.__train_data_path,
                                                                     "..",
                                                                     "cache",
                                                                     "explore_train_params.json"))
        self.__train_params_dict = load_json_file(self.__train_params_file_path)


    @property
    def train_params_dict(self):
        return self.__train_params_dict

    @train_params_dict.setter
    def train_params_dict(self, train_parmas_dict):
        if not isinstance(train_parmas_dict, dict):
            msg = "train_parmas_dict type error, only support dict, type: {}".format(type(train_parmas_dict))
            print(msg) if self._logger is None else self._logger.info(msg)
            return

        self.__train_params_dict = train_parmas_dict
        if self.__train_params_file_path:
            train_param_file_dir = os.path.dirname(self.__train_params_file_path)
            if not os.path.exists(train_param_file_dir):
                os.makedirs(train_param_file_dir)
            save_json_file(self.__train_params_file_path, train_parmas_dict)


logger = logging.getLogger('sdktool')
explore_train_inst = ExploreTrain(logger)
