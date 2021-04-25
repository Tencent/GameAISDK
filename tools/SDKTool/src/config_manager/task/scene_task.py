# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict

from .base_task import BaseTask


class SceneTask(BaseTask):

    def __init__(self, refer_task_instance):
        BaseTask.__init__(self)
        self.__refer_task = refer_task_instance

    def update(self, task_id: int, task_name: str, **kwargs) -> tuple:
        try:
            item = OrderedDict()
            item['taskID'] = task_id
            item['taskName'] = task_name
            item['description'] = kwargs['description']
            item['type'] = kwargs['type']
            item['elements'] = kwargs['elements']
            refers = kwargs.get('refer_tasks')
            self.delete(task_id)
            if isinstance(refers, list):
                ret, err = self.__refer_task.update(task_id, task_name, refer_tasks=refers)
                if not ret:
                    return ret, err
            self._add(item)
        except KeyError as err:
            return False, 'Element has no key: {}'.format(err)

        return True, ''

    def delete(self, task_id: int) -> None:
        self.__refer_task.delete(task_id)

        count = len(self._cfg_data)
        for i in range(0, count):
            if self._cfg_data[i]['taskID'] == task_id:
                self._cfg_data.pop(i)
                break

    def alloc_id(self) -> int:
        id_ret = 1
        id_list = [task['taskID'] for task in self._cfg_data]
        if len(id_list) > 0:
            id_ret = max(id_list) + 1
        return id_ret

    def get(self, task_id: int):
        task = self._get_task(task_id)
        refer_tasks = self.__refer_task.get(task_id)
        return task, refer_tasks

    def clear(self) -> None:
        self._cfg_data.clear()
        self.__refer_task.clear()

    def _get_task(self, task_id: int):
        item = OrderedDict()
        for task in self._cfg_data:
            if task['taskID'] == task_id:
                item = task
                break
        return item

    def has_id(self, task_id: int):
        if self._get_task(task_id):
            return True
        return False
