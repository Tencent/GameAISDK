# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from collections import OrderedDict
from abc import abstractmethod

from .ui_interface import UIInterface
from .ui_action import PointAction


class BaseUI(UIInterface):

    def __init__(self):
        self._cfg_data = list()

    def _add(self, cfg_item: OrderedDict) -> None:
        self._cfg_data.append(cfg_item)
 
    @abstractmethod
    def update(self, element_id: int, element_name: str, **kwargs) -> tuple:
        raise NotImplementedError()

    def delete(self, element_id: int) -> None:
        element_count = len(self._cfg_data)
        for i in range(0, element_count):
            if self._cfg_data[i]['id'] == element_id:
                self._cfg_data.pop(i)
                break

    def get(self, element_id: int) -> OrderedDict:
        item = OrderedDict()
        for element in self._cfg_data:
            if element['id'] == element_id:
                item = element
                break
        return item

    def get_all(self) -> list:
        return [(element['id'], element['name']) for element in self._cfg_data]

    @abstractmethod
    def alloc_id(self) -> int:
        id_ret = 1
        id_list = [element['id'] for element in self._cfg_data]
        if len(id_list) > 0:
            id_ret = max(id_list) + 1
        return id_ret

    def load(self, config: list) -> bool:
        self._cfg_data.clear()
        self._cfg_data.extend(config)
        return True

    def clear(self) -> None:
        self._cfg_data.clear()

    @abstractmethod
    def dump(self) -> list:
        return self._cfg_data

    def _parse_roi(self, item: OrderedDict, args: dict) -> None:
        roi = args['roi']
        item['x'] = roi.x
        item['y'] = roi.y
        item['w'] = roi.w
        item['h'] = roi.h

    def _parse_rois(self, item: OrderedDict, args: dict) -> None:
        item['imgPath'] = args['img_path']
        item['keyPoints'] = args['key_points']
        item['checkSameFrameCnt'] = args['same_frame_count']
        count = len(args['rois'])
        if count == 0:
            item['template'] = 0
        elif count == 1:
            item['template'] = 1
            roi = args['rois'][0]
            item['x'] = roi.x
            item['y'] = roi.y
            item['w'] = roi.w
            item['h'] = roi.h
            item['templateThreshold'] = roi.templateThreshold
        else:
            item['template'] = count
            item['templateOp'] = args['template_op']
            for i in range(0, count):
                roi = args['rois'][i]
                item['x{}'.format(i+1)] = roi.x
                item['y{}'.format(i+1)] = roi.y
                item['w{}'.format(i+1)] = roi.w
                item['h{}'.format(i+1)] = roi.h
                item['templateThreshold{}'.format(i + 1)] = roi.templateThreshold

    def _convert_point_action(self, item: OrderedDict, point_action: PointAction) -> None:
        item['actionX'] = point_action.x
        item['actionY'] = point_action.y
        item['actionThreshold'] = point_action.threshold
        item['actionTmplExpdWPixel'] = point_action.expand_pixel_w
        item['actionTmplExpdHPixel'] = point_action.expand_pixel_h
        item['actionROIExpdWRatio'] = point_action.roi_expand_ratio_w
        item['actionROIExpdHRatio'] = point_action.roi_expand_ratio_h

    def _convert_drag_action(self,
                             item: OrderedDict,
                             start_point_action: PointAction,
                             end_point_action: PointAction) -> None:
        item['actionX1'] = start_point_action.x
        item['actionY1'] = start_point_action.y
        item['actionThreshold1'] = start_point_action.threshold
        item['actionTmplExpdWPixel1'] = start_point_action.expand_pixel_w
        item['actionTmplExpdHPixel1'] = start_point_action.expand_pixel_h
        item['actionROIExpdWRatio1'] = start_point_action.roi_expand_ratio_w
        item['actionROIExpdHRatio1'] = start_point_action.roi_expand_ratio_h
        item['actionX2'] = end_point_action.x
        item['actionY2'] = end_point_action.y
        item['actionThreshold2'] = end_point_action.threshold
        item['actionTmplExpdWPixel2'] = end_point_action.expand_pixel_w
        item['actionTmplExpdHPixel2'] = end_point_action.expand_pixel_h
        item['actionROIExpdWRatio2'] = end_point_action.roi_expand_ratio_w
        item['actionROIExpdHRatio2'] = end_point_action.roi_expand_ratio_h

    @staticmethod
    def _get_basic_item(element_id: int, element_name: str, **kwargs):
        item = OrderedDict()
        item['id'] = element_id
        item['name'] = element_name
        item['desc'] = kwargs['description']
        item['actionType'] = kwargs['action_type']
        return item

    def _solve_basic_type(self, item, **kwargs):
        if item['actionType'] == 'click':
            self._parse_rois(item, kwargs)
            self._convert_point_action(item, kwargs['action'])
        elif item['actionType'] == 'drag':
            self._parse_rois(item, kwargs)
            self._convert_drag_action(item, kwargs['drag_start'], kwargs['drag_end'])
