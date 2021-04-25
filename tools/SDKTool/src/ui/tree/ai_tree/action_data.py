# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from abc import abstractmethod
from collections import OrderedDict

from ....project.project_manager import g_project_manager
from ...dialog.tip_dialog import show_warning_tips
from ....config_manager.ai.ai_manager import AIManager, AIType
from ....config_manager.task.task_manager import TaskManager

from ...utils import get_value, valid_number_value, set_log_text, tool_to_sdk_path, sdk_to_tool_path

logger = logging.getLogger("sdktool")


class ActionData(object):

    @abstractmethod
    def new_game_action(self, action_name, game_action):
        pass

    @abstractmethod
    def game_action_extend_param(self):
        pass

    @abstractmethod
    def get_game_action_type_param(self):
        pass

    @abstractmethod
    def get_type_param(self):
        pass

    @staticmethod
    def new_game_none_action(action_name, game_action):
        action_value = OrderedDict()
        action_value['id'] = game_action.alloc_id()
        action_value['name'] = action_name
        action_value['type'] = 'none'
        return action_value

    @staticmethod
    def new_sample_action_roi(action_roi=None):
        if action_roi is None:
            action_roi = OrderedDict()
        out_params = OrderedDict()
        out_params['path'] = get_value(action_roi, 'path', '')
        action_roi = get_value(action_roi, 'region', OrderedDict())
        out_params['region'] = OrderedDict()
        out_params['region']['x'] = get_value(action_roi, 'x', 0)
        out_params['region']['y'] = get_value(action_roi, 'y', 0)
        out_params['region']['w'] = get_value(action_roi, 'w', 0)
        out_params['region']['h'] = get_value(action_roi, 'h', 0)
        return out_params

    @staticmethod
    def new_sample_action_param(in_param=None):
        if in_param is None:
            in_param = OrderedDict()
        out_params = OrderedDict()

        out_params['prior'] = get_value(in_param, 'prior', '1')
        out_params['task'] = get_value(in_param, 'task', [0])
        return out_params

    @abstractmethod
    def init_swipe_params(self, params=None):
        pass

    @staticmethod
    def init_joy_stick_params(params=None):
        if params is None:
            params = OrderedDict()

        joy_stick_param = OrderedDict()
        joy_stick_param['path'] = ''
        joy_stick_param['quantizeNumber'] = get_value(params, 'quantize_number', 1)

        joy_stick_param['center'] = OrderedDict()
        joy_stick_param['center']['x'] = get_value(params, 'centerx', 0)
        joy_stick_param['center']['y'] = get_value(params, 'centery', 0)
        joy_stick_param['inner'] = OrderedDict()
        joy_stick_param['inner']['x'] = get_value(params, 'x', 0)
        joy_stick_param['inner']['y'] = get_value(params, 'y', 0)
        joy_stick_param['inner']['w'] = get_value(params, 'w', 0)
        joy_stick_param['inner']['h'] = get_value(params, 'h', 0)
        joy_stick_param['outer'] = OrderedDict()
        joy_stick_param['outer']['x'] = get_value(params, 'x', 0)
        joy_stick_param['outer']['y'] = get_value(params, 'y', 0)
        joy_stick_param['outer']['w'] = get_value(params, 'w', 0)
        joy_stick_param['outer']['h'] = get_value(params, 'h', 0)
        return joy_stick_param

    @staticmethod
    def init_key_params():
        out_params = OrderedDict()
        out_params['path'] = ''
        out_params['region'] = OrderedDict()
        out_params['region']['x'] = 0
        out_params['region']['y'] = 0
        out_params['region']['w'] = 0
        out_params['region']['h'] = 0

        out_params['alphabet'] = ''
        out_params['actionType'] = 'down'
        out_params['text'] = ''
        return out_params

    @staticmethod
    def _research_task(action_parameter):
        # 根据task_name 查找 task id
        if 'sceneTask' in action_parameter.keys():
            scene_task_name = action_parameter['sceneTask']
            multi_resolution = g_project_manager.get_multi_resolution(True)

            scene_task_id = -1
            task_manager = TaskManager()
            task = task_manager.get_task()
            for sub_task in task.get_all():
                task_id, task_name = sub_task
                if task_name == scene_task_name:
                    scene_task_id = int(task_id)
            if scene_task_id != -1:
                action_parameter['sceneTask'] = scene_task_id
            else:
                # 如果'sceneTask'对应的scene_task_id无效，说明动作无对应的识别任务，对此字段值置空
                if multi_resolution:
                    # 多分辨率下，需要提醒用户设定
                    show_warning_tips("action(%s)未选择对应的sceneTask" % action_parameter.get('id', 'none'))
                action_parameter['sceneTask'] = ""

    @staticmethod
    def save_game_action(action_parameter, game_action):
        if len(action_parameter) == 0:
            logger.info("action parameter is none")
            return

        if 'id' not in action_parameter.keys() or 'name' not in action_parameter.keys():
            return

        # 使数据有效str-->(int/float)
        valid_number_value(action_parameter)
        parameter = OrderedDict()
        for key, value in action_parameter.items():
            if key == 'id':
                parameter['action_id'] = value
            elif key == 'name':
                parameter['action_name'] = value
            else:
                parameter[key] = value

        logger.debug("parameters %s", parameter)
        tool_to_sdk_path(parameter)
        ActionData._research_task(parameter)
        flag, err = game_action.update(**parameter)
        if not flag:
            logger.error("update game action failed, reason %s", err)
            set_log_text(err)

    @staticmethod
    def get_game_action(action_id: int, game_action):
        parameter = game_action.get(action_id)
        action = OrderedDict()
        for key, value in parameter.items():
            if key == 'action_id':
                action['id'] = value
            elif key == 'action_name':
                action['name'] = value
            else:
                action[key] = value

        sdk_to_tool_path(action)
        return action

    @staticmethod
    def delete_game_action(action_id: int, game_action):
        game_action.delete(action_id)

    def new_ai_action(self, action_name, ai_action):
        action_value = OrderedDict()
        action_value['id'] = ai_action.alloc_id()
        action_value['name'] = action_name

        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()
        if ai_type == AIType.IMITATION_AI.value:
            action_parameter = self.new_sample_action_param()
            for key, value in action_parameter.items():
                action_value[key] = value

        action_value['actionIDGroup'] = ai_action.get_all()
        return action_value

    @staticmethod
    def save_ai_action(action_parameter, ai_action):
        # 使数据有效str-->(int/float)
        if len(action_parameter) == 0:
            logger.info("action parameter is none")
            return

        valid_number_value(action_parameter)

        parameter = OrderedDict()
        for key, value in action_parameter.items():
            if key == 'id':
                parameter['action_id'] = value
            elif key == 'name':
                parameter['action_name'] = value
            # elif key == 'group':
            #     parameter['action_id_group'] = value
            elif key == 'task':
                # task需要转成整型列表
                str_sub_tasks = value.split(',')
                int_sub_tasks = []
                for str_sub_task in str_sub_tasks:
                    int_sub_tasks.append(int(str_sub_task))
                parameter[key] = int_sub_tasks
            else:
                parameter[key] = value

        tool_to_sdk_path(parameter)
        try:
            flag, err = ai_action.update(**parameter)
        finally:
            logger.debug("parameters %s",  parameter)
            logger.debug('ai_action: %s',  ai_action)

        if not flag:
            logger.error("update ai action failed, reason %s", err)
            set_log_text(err)

    @staticmethod
    def get_ai_action(action_id: int, ai_action):
        parameter = ai_action.get(action_id)
        action = OrderedDict()
        for key, value in parameter.items():
            if key == 'action_id':
                action['id'] = value
            elif key == 'action_name':
                action['name'] = value
            elif key == 'action_id_group':
                action['actionIDGroup'] = value
            else:
                action[key] = value

        sdk_to_tool_path(action)
        return action

    @staticmethod
    def delete_ai_action(action_id: int, ai_action):
        ai_action.delete(action_id)
