# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from .base_task import BaseTask


class ReferTask(BaseTask):

    def __init__(self):
        BaseTask.__init__(self)

    def update(self, task_id: int, task_name: str, **kwargs) -> tuple:
        task_list = kwargs.get('refer_tasks')
        self.delete(task_id)
        for task in task_list:
            self._add(task)
        return (True, '')

    def delete(self, task_id: int) -> None:
        count = len(self._cfg_data)
        for i in range(count-1, -1, -1):
            if self._cfg_data[i]['objTask'] == task_id:
                self._cfg_data.pop(i)

    def get(self, task_id: int):
        refer_tasks = list()
        for task in self._cfg_data:
            if task['objTask'] == task_id:
                refer_tasks.append(task)
        return refer_tasks

    def clear(self) -> None:
        self._cfg_data.clear()
