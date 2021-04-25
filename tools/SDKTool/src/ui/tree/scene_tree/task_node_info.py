# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging
import os
from collections import OrderedDict

from ....config_manager.task.task_manager import TaskManager
from ....common.define import ELEMENT_TEMPLATE_JSON, REFER_TEMPLATE_JSON, SUB_ITEM_TEMPLATE_JSON, \
    TASK_TYPE_FIXOBJ, TASK_TYPE_REFER_LOCATION, TASK_TYPE_REFER_BLOODLENGTHREG, path_keys, refer_type_list, \
    task_type_list
from ...dialog.label_dialog import LabelDialog
from ...utils import get_value, get_sub_nodes, valid_number_value
from ...tree.scene_tree.refer_node_info import ReferNodeInfo
from ...tree.project_data_manager import ProjectDataManager

logger = logging.getLogger("sdktool")


class TaskNodeInfo(object):
    def __init__(self):
        self._node_cfg = OrderedDict()
        self.mgr = TaskManager()
        self.mgr.init()
        self.task = self.mgr.get_task()
        self._tmpl_element = None
        self._tmpl_refer = None
        self._location_infer = None
        self._tmpl_sub_item = None
        self.__refer_params = ReferNodeInfo()
        self.__refer_id = -1

    def init(self):
        if not self._init_tmpl_element():
            return False
        if not self._init_refer_task():
            return False
        if not self._int_sub_item():
            return False
        return True

    def set_refer_id(self, refer_id):
        self.__refer_params.set_refer_id(refer_id)

    def init_location_node(self, text, config=None):
        return self.__refer_params.node_location_func[text](config)

    def init_location_data(self, text, config=None):
        return self.__refer_params.data_location_func[text](config)

    def new_task_cfg(self, task_name='', task_type=None):
        if task_type is None:
            task_type = TASK_TYPE_FIXOBJ

        config = OrderedDict()
        config['taskName'] = task_name
        config['taskID'] = str(self.task.alloc_id())
        config['type'] = task_type
        config['description'] = ''
        config['elements'] = []
        element = self._tmpl_element.get(task_type)
        config['elements'].append(element)

        logger.debug("alloc id is %s", config['taskID'])
        return config

    def load_task_cfg(self, task_id):
        task_config, refer_tasks = self.task.get(task_id)
        self.change_config_path(task_config)
        for refer_task in refer_tasks:
            self.change_config_path(refer_task)
        refer_tasks_dict = dict()
        for refer_task in refer_tasks:
            obj_elements = refer_task.get('objElements')
            for obj_element in obj_elements:
                if obj_element not in refer_tasks_dict.keys():
                    refer_tasks_dict[obj_element] = []
                refer_tasks_dict[obj_element].append(refer_task)

        for index, element in enumerate(task_config.get('elements') or []):
            if index in refer_tasks_dict.keys():
                refer_task = refer_tasks_dict.get(index)[0]
                refer_type = refer_task.get('type')
                algorithm_type = refer_task.get('algorithm')
                refer_config = self.__refer_params.node_func[refer_type][algorithm_type](refer_task)
                logger.debug("refer type %s algorithm type %s", refer_type, algorithm_type)
                logger.debug("refer config %s", refer_config)

                element['refer'] = refer_config
        return task_config

    def save_task_elements(self, config, elements_node):
        if not isinstance(config, (dict, OrderedDict)):
            logger.error("input config is not dict, type is %", type(config))
            return False
        config["elements"] = []
        # 计算有多少个elements
        element_nodes = get_sub_nodes(elements_node)
        for ele_index, element in enumerate(element_nodes):
            # 每个element计算有多少项
            element_param = OrderedDict()
            nodes = get_sub_nodes(element)
            for node in nodes:
                key = node.text(0)
                count = node.childCount()
                if count == 0:
                    element_param[node.text(0)] = node.text(1)
                else:
                    if key == 'ROI':
                        self._save_roi_param(element_param, node)
                    if key == 'template':
                        self._save_list_node(element_param, node)
                    if key == "refer":
                        self._save_refer_node(config, node, ele_index)
            config["elements"].append(element_param)
        return True

    def change_config_path(self, config):
        if not isinstance(config, (dict, OrderedDict)):
            return

        for key, value in config.items():
            if key in path_keys:
                # 当前路径下不存在图像文件时，需要更改图像文件路径
                if not os.path.exists(value):
                    config[key] = ProjectDataManager().change_to_tool_path(value)
                    logger.debug("change config path %s--->%s", value, config[key])
            elif isinstance(value, (dict, OrderedDict)):
                self.change_config_path(value)
            elif isinstance(value, list):
                for sub_item in value:
                    self.change_config_path(sub_item)

    def change_scene_path(self, config):
        if not isinstance(config, (dict, OrderedDict)):
            return
        for key, value in config.items():
            if key in path_keys:
                config[key] = ProjectDataManager().change_to_sdk_path(value)
                logger.debug("change scene path %s--->%s", value, config[key])
            elif isinstance(value, (dict, OrderedDict)):
                self.change_scene_path(value)
            elif isinstance(value, list):
                for sub_item in value:
                    self.change_scene_path(sub_item)

    def save_task_node(self, right_tree):
        if right_tree is None:
            logger.info("input right tree is None")
            return None

        config = OrderedDict()
        # for index in range(right_tree.childCount()):
        node_count = right_tree.topLevelItemCount()
        if node_count == 0:
            return None

        for index in range(node_count):
            cur_item = right_tree.topLevelItem(index)
            key = cur_item.text(0)
            value = cur_item.text(1)
            count = cur_item.childCount()

            if count == 0:
                config[key] = value
            else:
                if key == 'elements':
                    self.save_task_elements(config, cur_item)
                else:
                    logger.error("unknown key %s", key)

        if None in [config.get('taskID')]:
            return None

        save_confg = OrderedDict()
        save_confg['task_id'] = config.get('taskID')
        save_confg['task_name'] = config.get('taskName')
        save_confg['type'] = config.get('type')
        save_confg['description'] = config.get('description')
        save_confg['elements'] = config.get('elements')
        save_confg['refer_tasks'] = config.get('refer')

        valid_number_value(save_confg)

        self.change_scene_path(save_confg)

        result, str_reason = self.task.update(**save_confg)
        if not result:
            dlg = LabelDialog(text=str_reason)
            dlg.pop_up()
        return config

    def new_refer_cfg(self, refer_type=TASK_TYPE_REFER_LOCATION):
        if refer_type not in refer_type_list:
            return dict()
        if refer_type == TASK_TYPE_REFER_LOCATION:
            return self.__refer_params.init_detect_node()
        if refer_type == TASK_TYPE_REFER_BLOODLENGTHREG:
            return self.__refer_params.init_blood_length_node()
        return None

    def new_sub_item_cfg(self, key='template'):
        if key not in self._tmpl_sub_item.keys():
            logger.error("%s not in sub item config %s", key, self._tmpl_sub_item.keys())
            return dict()
        return self._tmpl_sub_item.get(key)

    def new_element_cfg(self, task_type=None):
        if task_type is None:
            task_type = TASK_TYPE_FIXOBJ
        if task_type not in task_type_list:
            return dict()

        return self._tmpl_element.get(task_type)

    def change_to_data_cfg(self):
        raise NotImplementedError()

    def get_config(self):
        return self._node_cfg

    @staticmethod
    def int_roi(value=None):
        if value is None:
            value = dict()

        item = OrderedDict()
        item["x"] = get_value(value, 'x', 0)
        item["y"] = get_value(value, 'y', 0)
        item["w"] = value.get('width') or value.get('w') or 0
        item["h"] = value.get('height') or value.get('h') or 0
        return item

    def delete_task(self, task_id):
        self.task.delete(task_id)

    def load_config(self, config_file, refer_config):
        if config_file is None:
            logger.error("ui_node file is None")
            return

        success = self.mgr.load_config(config_file, refer_config)
        if not success:
            logger.error("load ui_node ui_node %s failed", config_file)
            return dict()

        return self.task.get_all()

    def clear_config(self):
        self.mgr.clear_config()

    def _save_refer_node(self, config, node, element_index=0):
        if 'refer' not in config.keys():
            config['refer'] = []

        refer_param = OrderedDict()
        sub_nodes = get_sub_nodes(node)
        for sub_node in sub_nodes:
            sub_key = sub_node.text(0)
            sub_value = sub_node.text(1)
            if sub_node.childCount() == 0:
                refer_param[sub_key] = sub_value
            else:
                if sub_key in ['templateLocation', 'inferROI']:
                    self._save_roi_param(refer_param, sub_node)
                elif sub_key in ['template', 'inferSubROI']:
                    self._save_list_node(refer_param, sub_node)
                else:
                    logger.error("unknown key %s", sub_key)

        # 转换refer 的参数为保存的参数
        task_id = config.get('taskID')
        obj_elements = [element_index]
        refer_type = refer_param.get('type')
        if refer_type == TASK_TYPE_REFER_BLOODLENGTHREG:
            refer_param = self.__refer_params.init_blood_length_data(node_cfg=refer_param,
                                                                     obj_task=task_id,
                                                                     obj_elements=obj_elements)
        elif refer_type == TASK_TYPE_REFER_LOCATION:
            algorithm_key = refer_param.get('algorithm')
            refer_param = self.__refer_params.data_location_func[algorithm_key](node_cfg=refer_param,
                                                                                obj_task=task_id,
                                                                                obj_elements=obj_elements)
        config['refer'].append(refer_param)

    @staticmethod
    def _save_roi_param(config, node):
        if not isinstance(config, (dict, OrderedDict)):
            logger.error("config is not dict, please check")
            return False
        key = node.text(0)
        config[key] = OrderedDict()
        childs = get_sub_nodes(node)
        for child in childs:
            sub_key = child.text(0)
            sub_value = child.text(1)
            config[key][sub_key] = sub_value

    def _save_list_node(self, config, node):
        if not isinstance(config, (dict, OrderedDict)):
            logger.error("config is not dict, please check")
            return False

        key = node.text(0)
        new_key = "{}s".format(key)
        if new_key not in config.keys():
            config[new_key] = []

        template_param = OrderedDict()
        sub_nodes = get_sub_nodes(node)
        for sub_node in sub_nodes:
            sub_key = sub_node.text(0)
            sub_value = sub_node.text(1)
            if sub_node.childCount() == 0:
                template_param[sub_key] = sub_value
            elif sub_key == 'location':
                self._save_roi_param(template_param, sub_node)
        config[new_key].append(template_param)

    def _init_tmpl_element(self, file=ELEMENT_TEMPLATE_JSON):
        try:
            with open(file, encoding='utf8') as f:
                self._tmpl_element = json.load(f, object_pairs_hook=OrderedDict)
                return True
        except IOError as err:
            logger.error("err is %s", err)
            return False

    def _init_refer_task(self, file=REFER_TEMPLATE_JSON):
        try:
            with open(file, encoding='utf8') as f:
                self._tmpl_refer = json.load(f, object_pairs_hook=OrderedDict)
                return True
        except IOError as err:
            logger.error("err is %s", err)
            return False

    def _int_sub_item(self, file=SUB_ITEM_TEMPLATE_JSON):
        try:
            with open(file, encoding='utf8') as f:
                self._tmpl_sub_item = json.load(f, object_pairs_hook=OrderedDict)
                self._location_infer = self._tmpl_sub_item.get("Infer")
                return True

        except IOError as err:
            logger.error("err is %s", err)
            return False
