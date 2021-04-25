# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict

from ....common.define import DEFAULT_TEMPLATE_THRESHOLD, DEFAULT_TMPL_EXPD_H_PIXEL, DEFAULT_TMPL_EXPD_W_PIXEL, \
    DEFAULT_EXPD_H_RATIO, DEFAULT_EXPD_W_RATIO, DEFAULT_UI_DURING_TIME_MS, DEFAULT_UI_SLEEP_TIME_MS, \
    TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG, DEFAULT_UI_DRAG_CHECK_LENGTH
from ....config_manager.ui.ui_manager import UIType, UIManager
from ....config_manager.ui.ui_action import PointAction, DragCheckAction, ScriptClickAction, ScriptDragAction
from ...dialog.label_dialog import LabelDialog
from ...tree.project_data_manager import ProjectDataManager
from ...utils import get_value, save_action


logger = logging.getLogger("sdktool")


class BaseNodeInfo(object):
    def __init__(self, ui_type=UIType.HALL_UI.value):
        self._node_cfg = OrderedDict()
        self.mgr = UIManager()
        self.mgr.init()
        self.ui_type = ui_type
        self.__data_cfg = self.mgr.get_ui(ui_type)

    def init(self, config_value):
        raise NotImplementedError()

    def change_to_data_cfg(self):
        raise NotImplementedError()

    def get_config(self):
        return self._node_cfg

    @staticmethod
    def init_click_action(value=None):
        if value is None:
            value = dict()
        action_item = OrderedDict()
        action_item["actionX"] = get_value(value, 'actionX', 0)
        action_item["actionY"] = get_value(value, 'actionY', 0)
        action_item["actionThreshold"] = get_value(value, 'actionThreshold', DEFAULT_TEMPLATE_THRESHOLD)
        action_item["actionTmplExpdWPixel"] = get_value(value, 'actionTmplExpdWPixel', DEFAULT_TMPL_EXPD_W_PIXEL)
        action_item["actionTmplExpdHPixel"] = get_value(value, 'actionTmplExpdHPixel', DEFAULT_TMPL_EXPD_H_PIXEL)
        action_item["actionROIExpdWRatio"] = get_value(value, 'actionROIExpdWRatio', DEFAULT_EXPD_W_RATIO)
        action_item["actionROIExpdHRatio"] = get_value(value, 'actionROIExpdHRatio', DEFAULT_EXPD_H_RATIO)
        return action_item

    @staticmethod
    def init_drag_action(value=None):
        if value is None:
            value = dict()

        action_item = OrderedDict()
        action_item["actionX1"] = get_value(value, 'actionX1', 0)
        action_item["actionY1"] = get_value(value, 'actionY1', 0)
        action_item["actionThreshold1"] = get_value(value, 'actionThreshold1', DEFAULT_TEMPLATE_THRESHOLD)
        action_item["actionTmplExpdWPixel1"] = get_value(value, 'actionTmplExpdWPixel1', DEFAULT_TMPL_EXPD_W_PIXEL)
        action_item["actionTmplExpdHPixel1"] = get_value(value, 'actionTmplExpdHPixel1', DEFAULT_TMPL_EXPD_H_PIXEL)
        action_item["actionROIExpdWRatio1"] = get_value(value, 'actionROIExpdWRatio1', DEFAULT_EXPD_W_RATIO)
        action_item["actionROIExpdHRatio1"] = get_value(value, 'actionROIExpdHRatio1', DEFAULT_EXPD_H_RATIO)
        action_item["actionX2"] = get_value(value, 'actionX2', 0)
        action_item["actionY2"] = get_value(value, 'actionY2', 0)
        action_item["actionThreshold2"] = get_value(value, 'actionThreshold2', DEFAULT_TEMPLATE_THRESHOLD)
        action_item["actionTmplExpdWPixel2"] = get_value(value, 'actionTmplExpdWPixel2', DEFAULT_TMPL_EXPD_W_PIXEL)
        action_item["actionTmplExpdHPixel2"] = get_value(value, 'actionTmplExpdHPixel2', DEFAULT_TMPL_EXPD_H_PIXEL)
        action_item["actionROIExpdWRatio2"] = get_value(value, 'actionROIExpdWRatio2', DEFAULT_EXPD_W_RATIO)
        action_item["actionROIExpdHRatio2"] = get_value(value, 'actionROIExpdHRatio2', DEFAULT_EXPD_H_RATIO)
        return action_item

    def init_script_click_action(self, task=None):
        if task is None:
            task = dict()

        task_param = OrderedDict()
        task_param['taskid'] = get_value(task, 'taskid', 0)
        task_param['duringTimeMs'] = get_value(task, 'duringTimeMs', DEFAULT_UI_DURING_TIME_MS)
        task_param['sleepTimeMs'] = get_value(task, 'sleepTimeMs', DEFAULT_UI_SLEEP_TIME_MS)
        task_param['actionType'] = get_value(task, 'type', 'click')
        task_param['action'] = self.init_click_action(task)

        return task_param

    def init_script_drag_action(self, task=None):
        if task is None:
            task = dict()

        task_param = OrderedDict()
        task_param['taskid'] = get_value(task, 'taskid', 0)
        task_param['duringTimeMs'] = get_value(task, 'duringTimeMs', DEFAULT_UI_DURING_TIME_MS)
        task_param['sleepTimeMs'] = get_value(task, 'sleepTimeMs', DEFAULT_UI_SLEEP_TIME_MS)
        task_param['actionType'] = get_value(task, 'type', 'drag')
        task_param['action'] = self.init_drag_action(task)
        return task_param

    def init_script_action(self, value=None):
        if value is None:
            value = dict()

        action_item = OrderedDict()
        tasks = list()
        for task in value.get('tasks') or []:
            action_type = get_value(task, 'type', 'click')
            if action_type == TYPE_UIACTION_CLICK:
                task_param = self.init_script_click_action(task)
            elif action_type == TYPE_UIACTION_DRAG:
                task_param = self.init_script_drag_action(task)

            tasks.append(task_param)
        action_item['scriptPath'] = get_value(value, 'scriptPath', '')
        if len(action_item['scriptPath']) > 0:
            action_item['scriptPath'] = ProjectDataManager().change_to_tool_path(action_item['scriptPath'])
        action_item['task'] = tasks
        return action_item

    @staticmethod
    def init_drag_check_action(value=None):
        if value is None:
            value = dict()

        action_item = OrderedDict()
        action_item['actionDir'] = get_value(value, 'actionDir', 'down')
        drag_point = OrderedDict()
        drag_point['actionX'] = get_value(value, 'dragX', 0)
        drag_point['actionY'] = get_value(value, 'dragY', 0)
        drag_length = get_value(value, 'dragLen', DEFAULT_UI_DRAG_CHECK_LENGTH)
        target = OrderedDict()
        target['targetImg'] = get_value(value, 'targetImg', '')
        if len(target['targetImg']) > 0:
            target['targetImg'] = ProjectDataManager().change_to_tool_path(target['targetImg'])

        roi = OrderedDict()
        roi['x'] = get_value(value, 'targetX', 0)
        roi['y'] = get_value(value, 'targetY', 0)
        roi['w'] = get_value(value, 'targetW', 0)
        roi['h'] = get_value(value, 'targetH', 0)
        target['ROI'] = roi

        action_item['dragPoint'] = drag_point
        action_item['dragLength'] = drag_length
        action_item['target'] = target
        return action_item

    @staticmethod
    def int_roi(value=None):
        if value is None:
            value = dict()

        item = OrderedDict()
        item["x"] = get_value(value, 'x', 0)
        item["y"] = get_value(value, 'y', 0)
        item["w"] = value.get('width') or value.get('w') or 0
        item["h"] = value.get('height') or value.get('h') or 0
        item["templateThreshold"] = get_value(value, 'templateThreshold', DEFAULT_TEMPLATE_THRESHOLD)
        return item

    def new_element_cfg(self, element_name=None):
        logger.info("new game item")
        config = dict()
        config['name'] = element_name
        config['id'] = self.__data_cfg.alloc_id()
        logger.info("alloc id is %s", config['id'])
        self.init(config)
        return self._node_cfg

    @staticmethod
    def save_action(node):
        return save_action(node)

    def save_task(self, node):
        params = OrderedDict()
        for index in range(node.childCount()):
            sub_node = node.child(index)
            name = sub_node.text(0)
            value = sub_node.text(1)
            if sub_node.childCount() > 0:
                if name not in params.keys():
                    params[name] = []
                params[name].append(self.save_action(sub_node))
            else:
                params[name] = value
        return params

    def check_element(self):
        pass

    def save_element(self, right_tree=None):
        if right_tree is None:
            logger.error("input right tree is None")
            return

        self._node_cfg = OrderedDict()
        # for index in range(right_tree.childCount()):
        node_count = right_tree.topLevelItemCount()
        for index in range(node_count):
            cur_item = right_tree.topLevelItem(index)
            key = cur_item.text(0)

            if cur_item.childCount() == 0:
                self._node_cfg[key] = cur_item.text(1)
            else:
                if key == 'ROI':
                    if key not in self._node_cfg.keys():
                        self._node_cfg[key] = []

                    roi_param = OrderedDict()
                    for roi_index in range(cur_item.childCount()):
                        roi_item = cur_item.child(roi_index)
                        roi_param_name = roi_item.text(0)
                        roi_param_value = roi_item.text(1)
                        roi_param[roi_param_name] = roi_param_value

                    self._node_cfg[key].append(roi_param)

                elif key in ['action']:
                    self._node_cfg[key] = self.save_action(cur_item)
                elif key in ['tasks']:
                    self._node_cfg[key] = self.save_task(cur_item)
                else:
                    logger.error("unknown key %s", key)

        data_cfg = self.change_to_data_cfg()
        if len(data_cfg) > 0:
            result, str_reason = self.__data_cfg.update(**data_cfg)
            if not result:
                dlg = LabelDialog(text=str_reason)
                dlg.pop_up()

        return self._node_cfg

    def load_element(self, element_id=-1):
        logging.info("load game item %s", element_id)
        config = self.__data_cfg.get(element_id)
        return self.init(config)

    def delete_element(self, element_id):
        self.__data_cfg.delete(element_id)

    def clear_config(self):
        self.mgr.clear_config()

    def load_config(self, config_file):
        if config_file is None:
            logger.error("ui_node file is None")
            return

        success = self.mgr.load_config(config_file)
        if not success:
            logger.error("load ui_node ui_node %s failed", config_file)
            return dict()

        return self.__data_cfg.get_all()

    def get_click_action(self, config=None):
        if config is None:
            config = self._node_cfg

        action = config.get('action') or {}
        x = int(action.get("actionX") or 0)
        y = int(action.get('actionY') or 0)
        threshold = float(action.get('actionThreshold'))
        expand_pixel_w = int(action.get('actionTmplExpdWPixel'))
        expand_pixel_h = int(action.get('actionTmplExpdHPixel'))
        roi_expand_ratio_w = float(action.get('actionROIExpdWRatio'))
        roi_expand_ratio_h = float(action.get('actionROIExpdHRatio'))
        return PointAction(x, y, threshold, expand_pixel_w, expand_pixel_h,
                           roi_expand_ratio_w, roi_expand_ratio_h)

    def get_drag_action(self, config=None):
        if config is None:
            config = self._node_cfg
        action = config.get('action') or {}

        x = int(get_value(action, "actionX1", 0))
        y = int(get_value(action, 'actionY1', 0))
        threshold = float(get_value(action, 'actionThreshold1', DEFAULT_TEMPLATE_THRESHOLD))
        expand_pixel_w = int(get_value(action, 'actionTmplExpdWPixel1', DEFAULT_TMPL_EXPD_W_PIXEL))
        expand_pixel_h = int(get_value(action, 'actionTmplExpdHPixel1', DEFAULT_TMPL_EXPD_H_PIXEL))
        roi_expand_ratio_w = float(get_value(action, 'actionROIExpdWRatio1', DEFAULT_EXPD_W_RATIO))
        roi_expand_ratio_h = float(get_value(action, 'actionROIExpdHRatio1', DEFAULT_EXPD_H_RATIO))
        start_point = PointAction(x, y, threshold, expand_pixel_w, expand_pixel_h, roi_expand_ratio_w,
                                  roi_expand_ratio_h)

        x = int(get_value(action, "actionX2", 0))
        y = int(get_value(action, 'actionY2', 0))
        threshold = float(get_value(action, 'actionThreshold2', DEFAULT_TEMPLATE_THRESHOLD))
        expand_pixel_w = int(get_value(action, 'actionTmplExpdWPixel2', DEFAULT_TMPL_EXPD_W_PIXEL))
        expand_pixel_h = int(get_value(action, 'actionTmplExpdHPixel2', DEFAULT_TMPL_EXPD_H_PIXEL))
        roi_expand_ratio_w = float(get_value(action, 'actionROIExpdWRatio2', DEFAULT_EXPD_W_RATIO))
        roi_expand_ratio_h = float(get_value(action, 'actionROIExpdHRatio2', DEFAULT_EXPD_H_RATIO))
        end_point = PointAction(x, y, threshold, expand_pixel_w, expand_pixel_h, roi_expand_ratio_w,
                                roi_expand_ratio_h)
        return start_point, end_point

    def get_drag_check_action(self, config=None):
        if config is None:
            config = self._node_cfg
        action = config.get('action') or {}
        direction = action['actionDir']
        drag_x = int(action['dragPoint']['actionX'])
        drag_y = int(action['dragPoint']['actionY'])
        drag_len = int(action['dragLength'])
        target_img = action['target']['targetImg']
        target_img = ProjectDataManager().change_to_sdk_path(target_img)
        target_x = int(action['target']['ROI']['x'])
        target_y = int(action['target']['ROI']['y'])
        target_w = int(action['target']['ROI']['w'])
        target_h = int(action['target']['ROI']['h'])
        return DragCheckAction(direction, drag_x, drag_y, drag_len, target_img, target_x, target_y, target_w, target_h)

    def get_script_action(self, config=None):
        if config is None:
            config = self._node_cfg.get('tasks')

        if config is None:
            logger.error("ui_node is None, please check")
            return

        script_path = config['scriptPath']
        tasks = []
        for task in config.get("task") or []:
            task_id = int(task['taskid'])
            during_ms = int(task['duringTimeMs'])
            sleep_ms = int(task['sleepTimeMs'])
            action_type = task['actionType']
            if action_type == 'click':
                pt_action = self.get_click_action(task)
                script_action = ScriptClickAction(task_id, during_ms, sleep_ms, action_type, pt_action)
                tasks.append(script_action)
            elif action_type == 'drag':
                start_point, end_point = self.get_drag_action(task)
                script_action = ScriptDragAction(task_id, during_ms, sleep_ms, action_type, start_point, end_point)
                tasks.append(script_action)

        return script_path, tasks
