# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import traceback
import logging

from .agent_msg_mgr import MsgMgr, MSG_SEND_TASK_CONF, MSG_SEND_GROUP_ID, MSG_SEND_TASK_FLAG, MSG_SEND_ADD_TASK, \
    MSG_SEND_DEL_TASK, MSG_SEND_CHG_TASK

LOG = logging.getLogger('sdktool')

GAME_STATE_INVALID = -1
GAME_STATE_START = 0
GAME_STATE_RUN = 1
GAME_STATE_LOSE = 2
GAME_STATE_WIN = 3
GAME_STATE_MAX = 4

GAME_STATE = 0


# GameReg---->Agent
RECV_MSG_ID_START = 45000
MSG_RECV_RESULT = RECV_MSG_ID_START + 1

# param 'type' of func GetInfo
CUR_GROUP_TASK_INFO = 11
CUR_GROUP_INFO = 12
GAME_RESULT_INFO = 13
ALL_GROUP_INFO = 14


class AgentAPIMgr(object):
    """
    AgentAPIMgr implement for communication between Agent and GameRecognize
    """
    def __init__(self):
        self.__msg_mgr = None
        self.__param_dict = dict()
        self.__game_task_config = None
        self.__refer_task_config = None
        self.__group_dict = None
        self.__task_list = []
        self.__msg_handler = dict()

    def initialize(self, conf_file, refer_file=None, index=1, self_addr=None, cfg_path='../cfg/platform/bus.ini'):
        """
        Initialize: Initialize MsgMgr object, load and send task configure file, refer configure file
        """
        self.__msg_mgr = MsgMgr(cfg_path, index)
        self._register()

        try:
            if not self.__msg_mgr.initialize(self_addr):
                LOG.error(traceback.format_exc())
                LOG.error('msgMgr init failed')
                return False
        except Exception as e:
            LOG.error(e)
            return False

        try:
            with open(conf_file) as fd:
                self.__game_task_config = json.load(fd)
                return self.__msg_mgr.proc_msg(MSG_SEND_TASK_CONF, [conf_file, refer_file])

        except IOError:
            LOG.error('open file [{0}] failed'.format(conf_file))
            return False

    def send_cmd(self, cmd_id, cmd_value):
        """
        pack message and send message to GameRecognize
        """
        try:
            msg_set = {
                MSG_SEND_GROUP_ID,
                MSG_SEND_TASK_FLAG,
                MSG_SEND_ADD_TASK,
                MSG_SEND_DEL_TASK,
                MSG_SEND_CHG_TASK
            }
            if cmd_id not in msg_set:
                LOG.error('input cmdID [{0}] wrong, please check '.format(cmd_id))
                return False

            if cmd_value is None:
                LOG.error('input cmd value is None, please check')
                return False

            cmd_value = self.__msg_handler[cmd_id](cmd_value)
            if cmd_value is None:
                return False

            else:
                return self.__msg_mgr.proc_msg(cmd_id, cmd_value)
        except Exception as e:
            LOG.error(traceback.format_exc())
            LOG.error(e)
            return False

    def send_src_image(self, src_img_dict):
        """
        SDKTool send source image to GameRecognize.
        """
        return self.__msg_mgr.proc_src_img_msg(src_img_dict)

    def send_ui_src_image(self, src_img_dict):
        return self.__msg_mgr.proc_ui_src_img_msg(src_img_dict)

    def recv_ui_result(self):
        return self.__msg_mgr.recv_ui()

    def recv_agent(self):
        return self.__msg_mgr.recv_agent()

    def get_info(self, msg_type):
        """
        Get information(source image, recognize results, etc.).
        """
        if msg_type not in [CUR_GROUP_TASK_INFO, CUR_GROUP_INFO, GAME_RESULT_INFO, ALL_GROUP_INFO]:
            LOG.error('input type [{0}] invalid, please check'.format(type))
            return False

        if CUR_GROUP_TASK_INFO == msg_type:
            return self.__task_list

        elif ALL_GROUP_INFO == msg_type:
            task_list = self.__game_task_config.get('alltask') or self._gameTaskConfig.get('allTask')
            return task_list

        elif CUR_GROUP_INFO == msg_type:
            return self.__group_dict

        elif GAME_RESULT_INFO == msg_type:
            msg_result = self.__msg_mgr.recv()
            if msg_result is not None:
                game_rets = msg_result['value']
                self._check(game_rets)
                return game_rets

    def release(self):
        """
        exit tbus
        """
        self.__msg_mgr.release()

    def _check(self, game_rets):
        group_id = game_rets['groupID']
        result = game_rets['result']
        pop_task_id = []
        for task_id, _ in result.items():
            find = False
            for task in self.__task_list:
                if task['taskID'] == task_id:
                    find = True
                    break

            if not find:
                pop_task_id.append(task_id)
                LOG.warning('get taskID [{0}] in reg results not find in'
                            ' taskList, please check'.format(task_id))

        for task_id in pop_task_id:
            result.pop(task_id)

        if self.__group_dict['groupID'] != group_id:
            LOG.error('recv group ID [{0}] in reg results not match '
                      'self group ID [{1}], please check'.format(group_id, self.__group_dict['groupID']))

    def _register(self):
        self.__msg_handler[MSG_SEND_GROUP_ID] = self._proc_send_group_id
        self.__msg_handler[MSG_SEND_TASK_FLAG] = self._proc_send_task_flag
        self.__msg_handler[MSG_SEND_ADD_TASK] = self._proc_send_add_task
        self.__msg_handler[MSG_SEND_DEL_TASK] = self._proc_send_del_task
        self.__msg_handler[MSG_SEND_CHG_TASK] = self._proc_send_chg_task

    def _proc_send_group_id(self, cmd_value):
        group_dict = None
        group_list = self.__game_task_config.get('alltask') or self.__game_task_config.get('allTask') or []
        for group in group_list:

            if cmd_value == group.get('groupID'):
                group_dict = group
                break

        if group_dict:
            self.__group_dict = group_dict
            self.__task_list = group_dict['task']

        else:
            LOG.error('input group id [{0}] invalid, please check '.format(cmd_value))

        return group_dict

    def _proc_send_task_flag(self, cmd_value):

        del_keys = []
        for key, _ in cmd_value.items():
            find = False

            for task in self.__task_list:
                if key == task['taskID']:
                    find = True
                    break

            if not find:
                LOG.error("input task [{0}] not in taskList, please check".format(key))
                del_keys.append(key)

        for key in del_keys:
            cmd_value.pop(key)
        return cmd_value

    def _proc_send_add_task(self, cmd_value):
        for item in cmd_value:
            if item in self.__task_list:
                LOG.error('input task [{0}] already in taskList, please check'.format(item))
                cmd_value.remove(item)
            else:
                self.__task_list.append(item)

        self.__group_dict['task'] = self.__task_list

        return cmd_value

    def _proc_send_del_task(self, cmd_value):
        task_id_list = []
        for item in self.__task_list:
            task_id = item.get('taskID')
            task_id_list.append(task_id)

        for task_id in cmd_value:
            find = False
            for item in self.__task_list:
                if task_id == item['taskID']:
                    self.__task_list.remove(item)
                    find = True
                    break

            if not find:
                LOG.error('input task [{0}] not in taskList, please check'.format(task_id))
                cmd_value.remove(task_id)

        self.__group_dict['task'] = self.__task_list

        return cmd_value

    def _proc_send_chg_task(self, cmd_value):
        for item in cmd_value:
            find = False
            for task_info in self.__task_list:
                if task_info['taskID'] == item['taskID']:
                    self.__task_list.remove(task_info)
                    self.__task_list.append(item)
                    find = True
                    break
            if not find:
                LOG.error('input task [{0}]not in taskList, please check'.format(item))
                cmd_value.remove(item)

        self.__group_dict['task'] = self.__task_list
        return cmd_value
