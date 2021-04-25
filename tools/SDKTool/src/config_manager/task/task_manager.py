# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
from enum import Enum, unique
from collections import OrderedDict

from ...common.singleton import Singleton
from .scene_task import SceneTask
from .refer_task import ReferTask


class TaskManager(metaclass=Singleton):

    __init = False

    def __init__(self):
        super(TaskManager, self).__init__()
        if not self.__init:
            self.__refer_task = ReferTask()
            self.__scene_task = SceneTask(self.__refer_task)
            self.__init = True

    def init(self) -> bool:
        return True

    def finish(self) -> None:
        pass

    def get_task(self):
        return self.__scene_task

    def load_config(self, task_file: str, refer_file: str) -> bool:
        if not self._load_task(self.__scene_task, task_file):
            return False
        if refer_file and not self._load_task(self.__refer_task, refer_file):
            return False
        return True

    def clear_config(self) -> None:
        self.__refer_task.clear()
        self.__scene_task.clear()

    def dump_config(self, task_file: str, refer_file: str) -> bool:
        if not self._dump_task(self.__scene_task, task_file):
            return False
        if refer_file and not self._dump_task(self.__refer_task, refer_file):
            return False
        return True

    def _load_task(self, task_instance, task_file: str):
        try:
            with open(task_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            task_config = json.loads(json_str, object_pairs_hook=OrderedDict)
            return task_instance.load(task_config)
        except FileNotFoundError:
            return False

    def _dump_task(self, task_instance, task_file: str):
        try:
            task_config = task_instance.dump()
            if task_config is not None:
                json_str = json.dumps(task_config, indent=4, ensure_ascii=False)
                with open(task_file, 'w', encoding='utf-8') as file:
                    file.write(json_str)
            elif os.path.isfile(task_file):
                os.remove(task_file)
        except FileNotFoundError:
            return False
        return True
