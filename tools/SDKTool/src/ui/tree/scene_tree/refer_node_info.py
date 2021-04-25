# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from src.ui.utils import get_value


logger = logging.getLogger("sdktool")


def create_common_config(node_cfg: OrderedDict,
                         detect_type="location",
                         detect_algorithm="Detect"):
    """ 创建通用数据

    :param node_cfg:
    :param detect_type:
    :param detect_algorithm:
    :param obj_task:
    :param obj_elements:
    :return:
    """
    config = OrderedDict()
    config['taskID'] = get_value(node_cfg, 'taskID', 0)
    config['type'] = get_value(node_cfg, 'type', detect_type)
    config['description'] = get_value(node_cfg, 'description', '')
    config['algorithm'] = get_value(node_cfg, 'algorithm', detect_algorithm)
    config['minScale'] = get_value(node_cfg, 'minScale', 0.8)
    config['maxScale'] = get_value(node_cfg, 'maxScale', 1.2)
    config['scaleLevel'] = get_value(node_cfg, 'scaleLevel', 9)
    config['expandWidth'] = get_value(node_cfg, 'expandWidth', 0.10)
    config['expandHeight'] = get_value(node_cfg, 'expandHeight', 0.10)
    config['matchCount'] = get_value(node_cfg, 'matchCount', 5)
    config['templates'] = get_value(node_cfg, 'templates', [])
    return config


def update_location_config(src_config_key, dst_config_key, node_cfg):
    node_cfg[dst_config_key] = OrderedDict()
    location = get_value(node_cfg, src_config_key, OrderedDict())
    node_cfg[dst_config_key]['x'] = get_value(location, 'x', 0)
    node_cfg[dst_config_key]['y'] = get_value(location, 'y', 0)
    node_cfg[dst_config_key]['w'] = get_value(location, 'w', 0)
    node_cfg[dst_config_key]['h'] = get_value(location, 'h', 0)


class ReferNodeInfo(object):

    def __init__(self):
        self.task_id = -1

        self.node_location_func = dict()
        self.node_location_func['Infer'] = self.init_infer_node
        self.node_location_func['Detect'] = self.init_detect_node

        self.node_func = dict()
        self.node_func['location'] = self.node_location_func

        self.node_bl_func = dict()
        self.node_bl_func['TemplateMatch'] = self.init_blood_length_node
        self.node_func['bloodlengthreg'] = self.node_bl_func

        self.data_location_func = dict()
        self.data_location_func['Infer'] = self.init_infer_data
        self.data_location_func['Detect'] = self.init_detect_data

    @staticmethod
    def init_detect_data(node_cfg: OrderedDict, obj_task=-1, obj_elements=None):
        cfg_data = create_common_config(node_cfg)
        update_location_config('templateLocation', 'location', cfg_data)
        cfg_data['objTask'] = obj_task
        if obj_elements is None:
            obj_elements = [0]
        cfg_data['objElements'] = obj_elements
        return cfg_data

    def init_detect_node(self, data_cfg=None):
        if data_cfg is None:
            data_cfg = OrderedDict()
        if 'taskID' not in data_cfg:
            data_cfg['taskID'] = self.task_id
        cfg_data = create_common_config(data_cfg, detect_type="location", detect_algorithm="Detect")
        update_location_config('location', 'templateLocation', cfg_data)
        if len(cfg_data['templates']) == 0:
            template = OrderedDict()
            template['path'] = ''
            template['threshold'] = 0.7
            cfg_data['templates'].append(template)

        return cfg_data

    @staticmethod
    def init_infer_data(node_cfg: OrderedDict, obj_task=-1, obj_elements=None):
        cfg_data = create_common_config(node_cfg, detect_algorithm="Infer")
        update_location_config('templateLocation', 'location', cfg_data)

        cfg_data['roiImg'] = get_value(node_cfg, 'roiImg', '')
        cfg_data['inferROI'] = get_value(node_cfg, 'inferROI', OrderedDict())
        infer_sub_rois = get_value(node_cfg, 'inferSubROIs', [])
        cfg_data['inferLocations'] = infer_sub_rois

        cfg_data['objTask'] = obj_task
        if obj_elements is None:
            obj_elements = [0]
        cfg_data['objElements'] = obj_elements
        return cfg_data

        # if obj_elements is None:
        #     obj_elements = [0]
        #
        # config = OrderedDict()
        # config['taskID'] = get_value(node_cfg, 'taskID', 0)
        # config['type'] = get_value(node_cfg, 'type', 'location')
        # config['description'] = get_value(node_cfg, 'description', '')
        # config['algorithm'] = get_value(node_cfg, 'algorithm', 'Infer')
        #
        # config['roiImg'] = get_value(node_cfg, 'roiImg', '')
        # config['inferROI'] = get_value(node_cfg, 'inferROI', OrderedDict())
        # infer_sub_rois = get_value(node_cfg, 'inferSubROIs', [])
        # config['inferLocations'] = infer_sub_rois
        #
        # config['minScale'] = get_value(node_cfg, 'minScale', 0.8)
        # config['maxScale'] = get_value(node_cfg, 'maxScale', 1.2)
        # config['expandWidth'] = get_value(node_cfg, 'expandWidth', 0.10)
        # config['expandHeight'] = get_value(node_cfg, 'expandHeight', 0.10)
        # config['matchCount'] = get_value(node_cfg, 'matchCount', 5)
        # config['templates'] = get_value(node_cfg, 'templates', [])
        # config['location'] = OrderedDict()
        # location = get_value(node_cfg, 'templateLocation', OrderedDict())
        # config['location']['x'] = get_value(location, 'x', 0)
        # config['location']['y'] = get_value(location, 'y', 0)
        # config['location']['w'] = get_value(location, 'w', 0)
        # config['location']['h'] = get_value(location, 'h', 0)
        #
        # config['objTask'] = obj_task
        # config['objElements'] = obj_elements
        # return config

    def init_infer_node(self, data_cfg=None):
        if data_cfg is None:
            data_cfg = OrderedDict()
        if 'taskID' not in data_cfg:
            data_cfg['taskID'] = self.task_id
        cfg_data = create_common_config(data_cfg, detect_type="location", detect_algorithm="Infer")
        update_location_config('location', 'templateLocation', cfg_data)

        cfg_data['inferROI'] = get_value(data_cfg, 'inferROI', OrderedDict())
        if not cfg_data['inferROI']:
            cfg_data['inferROI']['x'] = 0
            cfg_data['inferROI']['y'] = 0
            cfg_data['inferROI']['w'] = 0
            cfg_data['inferROI']['h'] = 0
        cfg_data['inferSubROIs'] = get_value(data_cfg, 'inferLocations', [])
        if not cfg_data['inferSubROIs']:
            infer_sub_roi = OrderedDict()
            infer_sub_roi['x'] = 0
            infer_sub_roi['y'] = 0
            infer_sub_roi['w'] = 0
            infer_sub_roi['h'] = 0
            cfg_data['inferSubROIs'].append(infer_sub_roi)

        if len(cfg_data['templates']) == 0:
            template = OrderedDict()
            template['path'] = ''
            template['threshold'] = 0.7
            cfg_data['templates'].append(template)
        cfg_data['roiImg'] = get_value(data_cfg, 'roiImg', '')

        return cfg_data

        # if data_cfg is None:
        #     data_cfg = OrderedDict()
        #
        # config = OrderedDict()
        # config['taskID'] = get_value(data_cfg, 'taskID', self.task_id)
        # config['type'] = get_value(data_cfg, 'type', 'location')
        # config['description'] = get_value(data_cfg, 'description', '')
        # config['algorithm'] = get_value(data_cfg, 'algorithm', 'Infer')
        #
        # config['roiImg'] = get_value(data_cfg, 'roiImg', '')
        # config['inferROI'] = get_value(data_cfg, 'inferROI', OrderedDict())
        # if len(config['inferROI']) == 0:
        #     config['inferROI']['x'] = 0
        #     config['inferROI']['y'] = 0
        #     config['inferROI']['w'] = 0
        #     config['inferROI']['h'] = 0
        #
        # config['inferSubROIs'] = get_value(data_cfg, 'inferLocations', [])
        # if len(config['inferSubROIs']) == 0:
        #     infer_sub_roi = OrderedDict()
        #     infer_sub_roi['x'] = 0
        #     infer_sub_roi['y'] = 0
        #     infer_sub_roi['w'] = 0
        #     infer_sub_roi['h'] = 0
        #     config['inferSubROIs'].append(infer_sub_roi)
        #
        # config['minScale'] = get_value(data_cfg, 'minScale', 0.8)
        # config['maxScale'] = get_value(data_cfg, 'maxScale', 1.2)
        # config['scaleLevel'] = get_value(data_cfg, 'scaleLevel', 9)
        # config['expandWidth'] = get_value(data_cfg, 'expandWidth', 0.1)
        # config['expandHeight'] = get_value(data_cfg, 'expandHeight', 0.1)
        # config['matchCount'] = get_value(data_cfg, 'matchCount', 5)
        # templates = get_value(data_cfg, 'templates', [])
        # config['templates'] = templates
        # if len(templates) == 0:
        #     template = OrderedDict()
        #     template['path'] = ''
        #     template['threshold'] = 0.7
        #     config['templates'].append(template)
        #
        # config['templateLocation'] = OrderedDict()
        # location = get_value(data_cfg, 'location', OrderedDict())
        # config['templateLocation']['x'] = get_value(location, 'x', 0)
        # config['templateLocation']['y'] = get_value(location, 'y', 0)
        # config['templateLocation']['w'] = get_value(location, 'w', 0)
        # config['templateLocation']['h'] = get_value(location, 'h', 0)
        #
        # return config

    @staticmethod
    def init_blood_length_data(node_cfg, obj_task=-1, obj_elements=None):
        cfg_data = create_common_config(node_cfg, detect_type="bloodlengthreg", detect_algorithm="TemplateMatch")
        update_location_config('templateLocation', 'location', cfg_data)
        cfg_data['objTask'] = obj_task
        if obj_elements is None:
            obj_elements = [0]
        cfg_data['objElements'] = obj_elements
        return cfg_data

    def init_blood_length_node(self, data_cfg=None):
        if data_cfg is None:
            data_cfg = OrderedDict()
        if 'taskID' not in data_cfg:
            data_cfg['taskID'] = self.task_id
        cfg_data = create_common_config(data_cfg, detect_type="bloodlengthreg", detect_algorithm="TemplateMatch")
        update_location_config('location', 'templateLocation', cfg_data)
        if len(cfg_data['templates']) == 0:
            template = OrderedDict()
            template['path'] = ''
            template['threshold'] = 0.7
            cfg_data['templates'].append(template)

        cfg_data['Conditions'] = get_value(data_cfg, 'Conditions', '')

        return cfg_data

    def set_refer_id(self, refer_id):
        self.task_id = refer_id
