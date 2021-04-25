# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict

from .base_ui import BaseUI


class StartUI(BaseUI):

    def __init__(self):
        BaseUI.__init__(self)

    def update(self, element_id: int, element_name: str, **kwargs) -> tuple:
        try:
            item = self._get_basic_item(element_id, element_name, **kwargs)

            if item['actionType'] == 'click' or item['actionType'] == 'drag':
                self._solve_basic_type(item, **kwargs)
            else:
                raise ValueError('action type is error.')

            self.delete(element_id)
            self._add(item)
        except KeyError as err:
            return False, 'Element has no key: {}'.format(err)
        except ValueError as err:
            return False, 'Wrong param: {}'.format(err)

        return True, ''

    def alloc_id(self) -> int:
        id_ret = 1000
        id_list = [element['id'] for element in self._cfg_data]
        if len(id_list) > 0:
            id_ret = max(id_list) + 1
        return id_ret

    def dump(self):
        start_ui = [{'id': element['id']} for element in self._cfg_data]
        return self._cfg_data, start_ui
