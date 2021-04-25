# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict

from .base_ui import BaseUI


class CloseIconUI(BaseUI):

    def __init__(self):
        BaseUI.__init__(self)

    def update(self, element_id: int, element_name: str, **kwargs) -> tuple:
        try:
            item = OrderedDict()
            item['id'] = element_id
            item['name'] = element_name
            item['desc'] = kwargs['description']
            item['imgPath'] = kwargs['img_path']
            roi = kwargs['roi']
            item['x'] = roi.x
            item['y'] = roi.y
            item['width'] = roi.w
            item['height'] = roi.h

            self.delete(element_id)
            self._add(item)
        except KeyError as err:
            return False, 'Element has no key: {}'.format(err)

        return True, ''

    def alloc_id(self) -> int:
        return 0

    def dump(self) -> list:
        return []
