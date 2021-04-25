# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from .base_node_info import BaseNodeInfo
from ....config_manager.ui.ui_manager import UIType
from ....config_manager.ui.ui_action import ROI
from ..project_data_manager import ProjectDataManager
from ...utils import get_value
from ....common.define import DEFAULT_TEMPLATE_THRESHOLD

logger = logging.getLogger("sdktool")


class OverNodeInfo(BaseNodeInfo):
    def __init__(self):
        super(OverNodeInfo, self).__init__(UIType.OVER_UI.value)

    def init(self, config_value):
        self._node_cfg.clear()
        self._node_cfg["name"] = config_value.get("name")
        self._node_cfg["id"] = config_value.get("id") or -1
        self._node_cfg["actionType"] = config_value.get("actionType") or "click"
        self._node_cfg["desc"] = config_value.get("desc") or ""
        self._node_cfg["imgPath"] = config_value.get("imgPath") or ""
        if len(self._node_cfg["imgPath"]) > 0:
            self._node_cfg["imgPath"] = ProjectDataManager().change_to_tool_path(self._node_cfg["imgPath"])
        self._node_cfg["ROI"] = self.int_roi(config_value)
        if self._node_cfg["actionType"] == 'click':
            self._node_cfg["action"] = self.init_click_action(config_value)

        elif self._node_cfg["actionType"] == 'drag':
            self._node_cfg["action"] = self.init_drag_action(config_value)

        return self._node_cfg

    def change_to_data_cfg(self):
        data_cfg = dict()
        rois = self._node_cfg.get('ROI')
        if rois is None:
            logger.error("not have over item")
            return data_cfg

        data_cfg["element_id"] = int(self._node_cfg.get("id") or -1)
        data_cfg["element_name"] = self._node_cfg.get('name')
        data_cfg['description'] = self._node_cfg.get('desc')
        data_cfg["action_type"] = self._node_cfg.get('actionType')
        data_cfg['img_path'] = self._node_cfg.get('imgPath')

        data_cfg["img_path"] = ProjectDataManager().change_to_sdk_path(data_cfg["img_path"])

        # rois = self._node_cfg.get('ROI')
        # if rois is not None:
        roi = rois[0]
        x = int(get_value(roi, 'x', 0))
        y = int(get_value(roi, 'y', 0))
        w = int(get_value(roi, 'w', 0))
        h = int(get_value(roi, 'h', 0))
        threshold = float(roi.get('templateThreshold', DEFAULT_TEMPLATE_THRESHOLD))
        data_cfg['roi'] = ROI(x, y, w, h, threshold)

        if data_cfg["action_type"] == 'click':
            data_cfg['action'] = self.get_click_action()
        elif data_cfg['action_type'] == 'drag':
            data_cfg['drag_start'], data_cfg['drag_end'] = self.get_drag_action()

        return data_cfg
