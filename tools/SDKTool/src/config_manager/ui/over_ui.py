# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict

from .base_ui import BaseUI


class OverUI(BaseUI):

    def __init__(self):
        BaseUI.__init__(self)

    def update(self, element_id: int, element_name: str, **kwargs) -> tuple:
        try:
            item = OrderedDict()
            item['id'] = element_id
            item['name'] = element_name
            item['desc'] = kwargs['description']
            item['imgPath'] = kwargs['img_path']
            item['actionType'] = kwargs['action_type']

            if item['actionType'] == 'click':
                self._parse_roi(item, kwargs)
                self._convert_point_action(item, kwargs['action'])
            elif item['actionType'] == 'drag':
                self._parse_roi(item, kwargs)
                self._convert_drag_action(item, kwargs['drag_start'], kwargs['drag_end'])
            else:
                raise ValueError('action type is error.')

            self.delete(element_id)
            self._add(item)
        except KeyError as err:
            return False, 'Element has no key: {}'.format(err)
        except ValueError as err:
            return False, 'Wrong param: {}'.format(err)

        return True, ''
