# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict
from abc import abstractmethod

from .task_interface import TaskInterface


class BaseTask(TaskInterface):

    def __init__(self):
        self.__group_id = 1
        self.__group_name = ''
        self._cfg_data = list()

    def _add(self, task: dict) -> None:
        self._cfg_data.append(task)
 
    def set_grpoup_name(self, group_name: str) -> None:
        self.__group_name = group_name

    @abstractmethod
    def update(self, task_id: int, task_name: str, **kwargs) -> tuple:
        raise NotImplementedError()

    @abstractmethod
    def delete(self, task_id: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def alloc_id(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def get(self, task_id: int):
        raise NotImplementedError()

    def get_all(self) -> list:
        return [(task['taskID'], task['taskName']) for task in self._cfg_data]

    def load(self, task_config: dict) -> bool:
        try:
            task = task_config['alltask'][0]
            self.__group_name = task['name']
            self._cfg_data.clear()
            self._cfg_data.extend(task['task'])
        except KeyError as err:
            return False
        return True

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError()

    def dump(self) -> OrderedDict:
        if len(self._cfg_data) == 0:
            return None

        task = OrderedDict()
        task['groupID'] = self.__group_id
        task['name'] = self.__group_name
        task['task'] = self._cfg_data
        task_config = OrderedDict()
        task_config['alltask'] = [task]
        return task_config
