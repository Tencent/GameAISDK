# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import configparser


class AgentAIConfig(object):
    def __init__(self, logger=None):
        self._logger = logger
        self.__agentai_config_path = None
        self._parser = None
        self._run_data_path = None

    def set_explore_run_inst(self, value):
        self._run_data_path = value

    @property
    def config_path(self):
        if self.__agentai_config_path is None:
            self.__agentai_config_path = os.path.join(self._run_data_path,
                                                           '..',
                                                           '..',
                                                           "cfg",
                                                           "task",
                                                           "agent",
                                                           "AgentAI.ini")
        return self.__agentai_config_path

    @property
    def parser(self):
        if self._parser is None:
            self._parser = configparser.ConfigParser()
            self._parser.read(self.config_path, encoding='UTF-8')
        return self._parser

    def get(self, section, key):
        """ 修改配置项

        :param section:
        :param key:
        :return:
        """
        if self.parser:
            return self.parser.get(section, key)
        return None

    def set(self, section, key, value):
        """ 修改配置项

        :param section:
        :param key:
        :param value:
        :return:
        """
        if self.parser:
            self.parser.set(section, key, value)

    def save(self):
        """ 保存

        :return:
        """
        with open(self.config_path, 'w', encoding='UTF-8') as fd:
            self.parser.write(fd)


logger = logging.getLogger('sdktool')
agentai_cfg_inst = AgentAIConfig(logger)
