# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from ...common.define import DEFAULT_TEMPLATE_THRESHOLD


class ROI(object):
    def __init__(self, x: int, y: int, w: int, h: int, threshold=DEFAULT_TEMPLATE_THRESHOLD):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.templateThreshold = threshold


class PointAction(object):
    def __init__(self, x: int, y: int, threshold: float, expand_pixel_w: int, expand_pixel_h: int,
                 roi_expand_ratio_w: float, roi_expand_ratio_h: float):
        self.x = x
        self.y = y
        self.threshold = threshold
        self.expand_pixel_w = expand_pixel_w
        self.expand_pixel_h = expand_pixel_h
        self.roi_expand_ratio_w = roi_expand_ratio_w
        self.roi_expand_ratio_h = roi_expand_ratio_h


class DragCheckAction(object):
    def __init__(self, direction: str, drag_x: int, drag_y: int, drag_len: int, target_img: str,
                 target_x: int, target_y: int, target_w: int, target_h: int):
        self.direction = direction
        self.drag_x = drag_x
        self.drag_y = drag_y
        self.drag_len = drag_len
        self.target_img = target_img
        self.target_x = target_x
        self.target_y = target_y
        self.target_w = target_w
        self.target_h = target_h


class ScriptClickAction(object):
    def __init__(self, task_id: int, during_ms: int, sleep_ms: int, action_type: str, point_action: PointAction):
        self.task_id = task_id
        self.during_ms = during_ms
        self.sleep_ms = sleep_ms
        self.action_type = action_type
        self.point_action = point_action


class ScriptDragAction(object):
    def __init__(self, task_id: int, during_ms: int, sleep_ms: int, action_type: str,
                 start_point_action: PointAction, end_point_action: PointAction):
        self.task_id = task_id
        self.during_ms = during_ms
        self.sleep_ms = sleep_ms
        self.action_type = action_type
        self.start_point_action = start_point_action
        self.end_point_action = end_point_action
