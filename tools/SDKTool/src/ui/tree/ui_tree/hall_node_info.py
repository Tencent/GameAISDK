# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging


from collections import OrderedDict

from ....common.define import DEFAULT_UI_KEYPOINT, DEFAULT_UI_CHECK_SAME_FRAME, TYPE_UIACTION_CLICK, \
    TYPE_UIACTION_DRAG, TYPE_UIACTION_DRAGCHECK, TYPE_UIACTION_SCRIPT, DEFAULT_TEMPLATE_THRESHOLD
from ....config_manager.ui.ui_action import ROI
from ....config_manager.ui.ui_manager import UIType
from ...tree.ui_tree.base_node_info import BaseNodeInfo
from ..project_data_manager import g_project_data_mgr
from ...utils import get_value


logger = logging.getLogger("sdktool")


class HallNodeInfo(BaseNodeInfo):
    def __init__(self, ui_type=UIType.HALL_UI.value):
        super(HallNodeInfo, self).__init__(ui_type)

    def init(self, config_value):
        self._node_cfg.clear()
        self._node_cfg["name"] = get_value(config_value, "name", '')
        self._node_cfg["id"] = get_value(config_value, "id", -1)
        self._node_cfg["actionType"] = get_value(config_value, "actionType", "click")

        self._node_cfg["template"] = get_value(config_value, "template", "0")

        self._node_cfg["desc"] = get_value(config_value, "desc", "")
        self._node_cfg["imgPath"] = get_value(config_value, "imgPath", "")
        if len(self._node_cfg["imgPath"]) > 0:
            self._node_cfg["imgPath"] = g_project_data_mgr.change_to_tool_path(self._node_cfg["imgPath"])

        self._node_cfg["keyPoints"] = get_value(config_value, "keyPoints", DEFAULT_UI_KEYPOINT)
        self._node_cfg['checkSameFrameCnt'] = get_value(config_value, 'checkSameFrameCnt', DEFAULT_UI_CHECK_SAME_FRAME)
        self.load_template_cfg(config_value)

        if self._node_cfg["actionType"] == 'click':
            self._node_cfg["action"] = self.init_click_action(config_value)

        elif self._node_cfg["actionType"] == 'drag':
            self._node_cfg["action"] = self.init_drag_action(config_value)

        elif self._node_cfg["actionType"] == 'dragcheck':
            self._node_cfg["action"] = self.init_drag_check_action(config_value)

        elif self._node_cfg.get("actionType") == 'script':
            self._node_cfg["tasks"] = self.init_script_action(config_value)

        return self._node_cfg

    def change_to_data_cfg(self):
        data_cfg = dict()
        data_cfg["element_id"] = int(get_value(self._node_cfg, "id", -1))
        data_cfg["element_name"] = get_value(self._node_cfg, 'name', '')
        data_cfg['description'] = get_value(self._node_cfg, 'desc', '')
        data_cfg["action_type"] = get_value(self._node_cfg, 'actionType', '')
        data_cfg['img_path'] = get_value(self._node_cfg, 'imgPath', '')

        if data_cfg['img_path']:
            data_cfg['img_path'] = g_project_data_mgr.change_to_sdk_path(data_cfg['img_path'])

        number = get_value(self._node_cfg, 'keyPoints', DEFAULT_UI_KEYPOINT)
        data_cfg['key_points'] = int(number)
        data_cfg['rois'] = []
        rois = self._node_cfg.get("ROI") or []
        for roi in rois:
            x = int(get_value(roi, 'x', 0))
            y = int(get_value(roi, 'y', 0))
            w = roi.get('w') or roi.get('width') or 0
            h = roi.get('h') or roi.get('height') or 0
            w = int(w)
            h = int(h)
            threshold = float(roi.get('templateThreshold', DEFAULT_TEMPLATE_THRESHOLD))
            data_cfg['rois'].append(ROI(x, y, w, h, threshold))

        if len(rois) > 1:
            data_cfg['template_op'] = self._node_cfg.get('templateOp')

        number = self._node_cfg.get('checkSameFrameCnt')
        if number is None:
            number = DEFAULT_UI_CHECK_SAME_FRAME
        data_cfg['same_frame_count'] = int(number)

        if data_cfg["action_type"] == 'click':
            data_cfg['action'] = self.get_click_action()
        elif data_cfg['action_type'] == 'drag':
            data_cfg['drag_start'], data_cfg['drag_end'] = self.get_drag_action()

        elif data_cfg['action_type'] == 'dragcheck':
            data_cfg['action'] = self.get_drag_check_action()
        elif data_cfg['action_type'] == 'script':
            data_cfg['script_path'], data_cfg['tasks'] = self.get_script_action()
            if data_cfg['script_path']:
                data_cfg['script_path'] = g_project_data_mgr.change_to_sdk_path(data_cfg['script_path'])

        return data_cfg

    def add_template_roi(self, item, template_number):
        #  new a configure data and set it to self.__node_cfg
        new_item = OrderedDict()
        new_item["name"] = item.get("name")
        new_item["id"] = item.get("id")
        new_item["actionType"] = item.get("actionType") or "click"
        new_item["template"] = template_number
        new_item["desc"] = item.get("desc")
        new_item["imgPath"] = item.get("imgPath")

        if template_number == 0:
            pass
        elif template_number == 1:
            new_item["ROI"] = []
            new_item["ROI"].append(self.int_roi())
        else:
            new_item["templateOp"] = 'and'
            new_item["ROI"] = []
            for _ in range(template_number):
                new_item["ROI"].append(self.int_roi())

        new_item["keyPoints"] = item.get("keyPoints")
        new_item['checkSameFrameCnt'] = 5

        # new or load previous value
        if new_item["actionType"] == TYPE_UIACTION_CLICK:
            new_item["action"] = self.init_click_action(item.get('action'))

        elif new_item["actionType"] == TYPE_UIACTION_DRAG:
            new_item["action"] = self.init_drag_action(item.get('action'))

        elif new_item["actionType"] == TYPE_UIACTION_DRAGCHECK:
            new_item['action'] = self.init_drag_check_action(item.get('action'))

        elif new_item["actionType"] == TYPE_UIACTION_SCRIPT:
            new_item['tasks'] = self.init_script_action(item.get('tasks'))

        self._node_cfg = new_item
        return self._node_cfg

    def load_template_cfg(self, value):
        count = int(value.get("template") or 0)
        if count < 1:
            return

        if count == 1:
            self._node_cfg["ROI"] = []
            self._node_cfg["ROI"].append(self.int_roi(value))
        else:
            self._node_cfg["templateOp"] = value.get('templateOp') or 'and'

            self._node_cfg["ROI"] = []
            for index in range(count):
                roi = OrderedDict()
                roi['x'] = value.get('x{}'.format(index + 1))
                roi['y'] = value.get('y{}'.format(index + 1))
                roi['w'] = value.get('w{}'.format(index + 1))
                roi['h'] = value.get('h{}'.format(index + 1))
                self._node_cfg["ROI"].append(roi)
