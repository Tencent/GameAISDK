# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from ....common.define import DEFAULT_UI_KEYPOINT, DEFAULT_UI_CHECK_SAME_FRAME
from ....config_manager.ui.ui_manager import UIType
from .hall_node_info import HallNodeInfo
from ....config_manager.ui.ui_action import ROI
from ..project_data_manager import ProjectDataManager
from ...utils import get_value


logger = logging.getLogger("sdktool")


class StartNodeInfo(HallNodeInfo):
    def __init__(self, ui_type=UIType.START_UI.value):
        super(StartNodeInfo, self).__init__(ui_type)

    def change_to_data_cfg(self):
        data_cfg = super(StartNodeInfo, self).change_to_data_cfg()
        data_cfg['is_start'] = True
        return data_cfg
