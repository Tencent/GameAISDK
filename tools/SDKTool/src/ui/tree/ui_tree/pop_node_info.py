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


class PopNodeInfo(BaseNodeInfo):
    def __init__(self, ui_type=UIType.CLOSE_ICON_UI.value):
        super(PopNodeInfo, self).__init__(ui_type)

    def init(self, value):
        self._node_cfg.clear()
        self._node_cfg["name"] = get_value(value, "name", '')
        self._node_cfg["id"] = get_value(value, "id", -1)
        self._node_cfg["desc"] = get_value(value, "desc", "")
        self._node_cfg["imgPath"] = get_value(value, "imgPath", "")
        self._node_cfg["imgPath"] = ProjectDataManager().change_to_tool_path(self._node_cfg["imgPath"])
        self._node_cfg["ROI"] = self.int_roi(value)

        return self._node_cfg

    def change_to_data_cfg(self):
        data_cfg = dict()
        rois = self._node_cfg.get('ROI')
        if rois is None:
            return data_cfg

        data_cfg["element_id"] = int(get_value(self._node_cfg, "id", -1))
        data_cfg["element_name"] = get_value(self._node_cfg, 'name', '')
        data_cfg['description'] = get_value(self._node_cfg, 'desc', '')
        data_cfg['img_path'] = get_value(self._node_cfg, 'imgPath', '')
        if len(self._node_cfg["imgPath"]) > 0:
            data_cfg["img_path"] = ProjectDataManager().change_to_sdk_path(data_cfg["img_path"])
        # rois = self._node_cfg.get('ROI')
        # if rois is None:
        roi = rois[0]
        x = int(get_value(roi, 'x', 0))
        y = int(get_value(roi, 'y', 0))
        w = int(get_value(roi, 'w', 0))
        h = int(get_value(roi, 'h', 0))
        threshold = float(roi.get('templateThreshold', DEFAULT_TEMPLATE_THRESHOLD))
        data_cfg['roi'] = ROI(x, y, w, h, threshold)

        return data_cfg
