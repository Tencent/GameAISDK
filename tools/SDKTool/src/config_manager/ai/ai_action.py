# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
from abc import ABCMeta, abstractmethod
from collections import OrderedDict


class Action(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        self._action_list = list()

    def _add(self, action_cfg: OrderedDict) -> None:
        self._action_list.append(action_cfg)

    @abstractmethod
    def update(self, action_id: int, action_name: str, **kwargs) -> tuple:
        raise NotImplementedError()

    def update_inner(self, action_id: int, action_name: str, **kwargs) -> tuple:
        try:
            item = OrderedDict()
            item['id'] = action_id
            item['name'] = action_name
            for key, value in kwargs.items():
                item[key] = value

            self.delete(action_id)
            self._add(item)
            return True, ''

        except KeyError as err:
            return False, 'action has no key: {}'.format(err)

    def delete(self, action_id: int) -> None:
        count = len(self._action_list)
        for i in range(0, count):
            if self._action_list[i]['id'] == action_id:
                self._action_list.pop(i)
                break

    def alloc_id(self) -> int:
        id_ret = 0
        id_list = [action['id'] for action in self._action_list]
        if len(id_list) > 0:
            id_ret = max(id_list) + 1
        return id_ret

    def get(self, action_id: int) -> OrderedDict:
        item = OrderedDict()
        for action in self._action_list:
            if action['id'] == action_id:
                item = action
                break
        return item

    def get_all(self) -> list:
        return [(action['id'], action['name']) for action in self._action_list]

    def load(self, config: list) -> bool:
        self.clear()
        self._action_list.extend(config)
        return True

    def clear(self):
        self._action_list.clear()

    def dump(self) -> list:
        return self._action_list


class GameAction(Action):
    def __init__(self):
        super(GameAction, self).__init__()

    def update(self, action_id: int, action_name: str, **kwargs) -> tuple:
        return self.update_inner(action_id, action_name, **kwargs)


class AIAction(Action):
    def __init__(self):
        super(AIAction, self).__init__()

    def update(self, action_id: int, action_name: str, **kwargs) -> tuple:
        return self.update_inner(action_id, action_name, **kwargs)
