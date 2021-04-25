# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging


logger = logging.getLogger("sdktool")


class GameState(object):

    def __init__(self):
        self.__begin_task_id = list()
        self.__over_task_id = list()

    def set_begin_task_id(self, task_ids: list) -> None:
        self.__begin_task_id.clear()
        self.__begin_task_id.extend(task_ids)

    def set_over_task_id(self, task_ids: list) -> None:
        self.__over_task_id.clear()
        self.__over_task_id.extend(task_ids)

    def get_begin_task_id(self) -> list:
        return self.__begin_task_id

    def get_over_task_id(self) -> list:
        return self.__over_task_id

    def load(self, config: dict) -> bool:
        if not isinstance(config, dict):
            return False

        try:
            self.clear()
            self.set_begin_task_id(config['beginTaskID'])
            self.set_over_task_id(config['overTaskID'])
        except KeyError as err:
            logger.error("load the game state err:{}".format(err))
            return False

        return True

    def clear(self) -> None:
        self.__begin_task_id.clear()
        self.__over_task_id.clear()

    def dump(self) -> dict:
        config = dict()
        config['beginTaskID'] = self.__begin_task_id
        config['overTaskID'] = self.__over_task_id
        return config
