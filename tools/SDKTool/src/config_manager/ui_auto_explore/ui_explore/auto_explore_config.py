# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging

from ....config_manager.common.utils import load_json_file, save_json_file


class AutoExploreConfig(object):
    def __init__(self, logger=None):
        self._logger = logger
        self.__auto_explore_config_path = None
        self._run_data_path = None

    def set_run_data_path(self, value):
        self._run_data_path = value

    @property
    def config_path(self):
        if self.__auto_explore_config_path is None:
            self.__auto_explore_config_path = os.path.join(self._run_data_path,
                                                           '..',
                                                           '..',
                                                           "cfg",
                                                           "task",
                                                           "agent",
                                                           "UiAutoExplore.json")
        return self.__auto_explore_config_path

    def get_auto_config_params(self):
        return load_json_file(self.config_path)

    def save_auto_config_params(self, config_params):
        return save_json_file(self.config_path, config_params, indent=4)

logger = logging.getLogger('sdktool')
auto_explore_cfg_inst = AutoExploreConfig(logger)
