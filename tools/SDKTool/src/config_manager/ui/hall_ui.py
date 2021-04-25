# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict

from .base_ui import BaseUI


class HallUI(BaseUI):

    def __init__(self):
        BaseUI.__init__(self)

    def _parse_drag_check_action(self, item: OrderedDict, args: dict) -> None:
        self._parse_rois(item, args)
        darg_action = args['action']
        item['actionDir'] = darg_action.direction
        item['dragX'] = darg_action.drag_x
        item['dragY'] = darg_action.drag_y
        item['dragLen'] = darg_action.drag_len
        item['targetImg'] = darg_action.target_img
        item['targetX'] = darg_action.target_x
        item['targetY'] = darg_action.target_y
        item['targetW'] = darg_action.target_w
        item['targetH'] = darg_action.target_h

    def _parse_script_action(self, item: OrderedDict, args: dict) -> None:
        self._parse_rois(item, args)
        item['scriptPath'] = args['script_path']
        item['tasks'] = []
        for t in args['tasks']:
            task = OrderedDict()
            task['taskid'] = t.task_id
            task['duringTimeMs'] = t.during_ms
            task['sleepTimeMs'] = t.sleep_ms
            task['type'] = t.action_type
            if t.action_type == 'click':
                self._convert_point_action(task, t.point_action)
            elif t.action_type == 'drag':
                self._convert_drag_action(task, t.start_point_action, t.end_point_action)
            item['tasks'].append(task)

    def update(self, element_id: int, element_name: str, **kwargs) -> tuple:
        try:
            item = self._get_basic_item(element_id, element_name, **kwargs)
            if item['actionType'] == 'click' or item['actionType'] == 'drag':
                self._solve_basic_type(item, **kwargs)
            elif item['actionType'] == 'dragcheck':
                self._parse_drag_check_action(item, kwargs)
            elif item['actionType'] == 'script':
                self._parse_script_action(item, kwargs)
            else:
                raise ValueError('action type is error.')

            self.delete(element_id)
            self._add(item)
        except KeyError as err:
            return False, 'Element has no key: {}'.format(err)
        except ValueError as err:
            return False, 'Wrong param: {}'.format(err)

        return True, ''
