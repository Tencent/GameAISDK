# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import logging
import configparser as ConfigParser

import msgpack
import msgpack_numpy
import numpy as np

from ..common.define import ACTION_ID_CLICK, ACTION_ID_DOWN, ACTION_ID_UP, ACTION_ID_MOVE, ACTION_ID_SWIPE, \
    ACTION_NAMES, ACTION_ID_SWIPEDOWN, ACTION_ID_SWIPEMOVE, SDK_BIN_PATH, WINDOW_ACTION_NAMES

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__ + "/protocol")
sys.path.append(SDK_BIN_PATH)

import tbus
from .protocol import common_pb2
from .protocol import gameregProtoc_pb2
from ..project.project_manager import g_project_manager
from ..WrappedDeviceAPI.wrappedDeviceConfig import DeviceType


MSG_SEND_ID_START = 40000
MSG_SEND_GROUP_ID = MSG_SEND_ID_START + 1
MSG_SEND_TASK_FLAG = MSG_SEND_ID_START + 2
MSG_SEND_ADD_TASK = MSG_SEND_ID_START + 3
MSG_SEND_DEL_TASK = MSG_SEND_ID_START + 4
MSG_SEND_CHG_TASK = MSG_SEND_ID_START + 5
MSG_SEND_TASK_CONF = MSG_SEND_ID_START + 6

MSG_REGER_BUTTON_TYPE = 'button'
MSG_REGER_STUCK_TYPE = 'stuck'
MSG_REGER_FIXOBJ_TYPE = 'fix object'
MSG_REGER_PIX_TYPE = 'pixel'
MSG_REGER_DEFORM_TYPE = 'deform object'
MSG_REGER_NUMBER_TYPE = 'number'
MSG_REGER_FIXBLOOD_TYPE = 'fix blood'
MSG_REGER_KING_GLORY_BOOD_TYPE = 'king glory blood'
MSG_REGER_MAPREG_TYPE = 'map'
MSG_REGER_MAPDIRECTIONREG_TYPE = 'mapDirection'
MSG_REGER_MULTCOLORVAR_TYPE = 'multcolorvar'
MSG_REGER_SHOOTGAMEBLOOD_TYPE = 'shoot game blood'
MSG_REGER_SHOOTGAMEHURT_TYPE = 'shoot game hurt'

LOG = logging.getLogger('sdktool')


class MsgMgr(object):
    """
    message manager implement
    """
    def __init__(self, cfg_path='../cfg/bus.ini', index=1):
        self.__self_addr = None
        self.__game_reg_addr = None
        self.__uirecognize_addr = None
        self.__agent_addr = None
        self.__sdk_tool_addr = None
        self.__cfg_path = cfg_path
        self.__index = index
        self.__serial_msg_handle = dict()
        self.__serial_reger_handle = dict()
        self.__unseiral_reger_handle = dict()
        self.__device_type = g_project_manager.get_device_type(DeviceType.Android.value)

    def initialize(self, self_addr=None):
        """
        Initialize message manager, parse tbus configure file and initialize tbus
        return: True or Flase
        """

        if os.path.exists(self.__cfg_path):
            self._register()

            config = ConfigParser.ConfigParser(strict=False)
            config.read(self.__cfg_path)
            game_reg_addr = "GameReg" + str(self.__index) + "Addr"
            strgame_reg_addr = config.get('BusConf', game_reg_addr)

            ui_recognize_addr = "UI" + str(self.__index) + "Addr"
            str_ui_addr = config.get('BusConf', ui_recognize_addr)

            agent_addr = "Agent"+str(self.__index) + "Addr"
            str_agent_addr = config.get('BusConf', agent_addr)

            sdktool_addr = "SDKToolAddr"
            str_tool_addr = config.get('BusConf', sdktool_addr)

            if self_addr is None:
                agent_addr = "Agent" + str(self.__index) + "Addr"
                strself_addr = config.get('BusConf', agent_addr)
            else:
                strself_addr = config.get('BusConf', self_addr)
            self.__game_reg_addr = tbus.GetAddress(strgame_reg_addr)
            self.__uirecognize_addr = tbus.GetAddress(str_ui_addr)
            self.__agent_addr = tbus.GetAddress(str_agent_addr)
            self.__sdk_tool_addr = tbus.GetAddress(str_tool_addr)
            self.__self_addr = tbus.GetAddress(strself_addr)

            LOG.info("strgameRegAddr is {0}, strUIAddr is {1}, "
                     "strAgentAddr: {2}".format(strgame_reg_addr, str_ui_addr, str_agent_addr))

            LOG.info("gamereg addr is {0}, self addr is {1}".format(self.__game_reg_addr,
                                                                    self.__self_addr))
            ret = tbus.Init(self.__self_addr, self.__cfg_path)
            if ret != 0:
                LOG.error('tbus init failed with return code[{0}]'.format(ret))
                return False

            LOG.info("*************__agent_addr {} **************".format(self.__agent_addr))

            return True

        else:
            LOG.error('tbus config file not exist in {0}'.format(self.__cfg_path))
            return False

    def proc_msg(self, msg_id, msg_value):
        """
        Process message: create message and send to GameReg
        :param msg_id: message ID which should be in [MSG_SEND_GROUP_ID, MSG_SEND_TASK_FLAG,
                      MSG_SEND_ADD_TASK,MSG_SEND_DEL_TASK, MSG_SEND_CHG_TASK, MSG_SEND_TASK_CONF]
        :param msg_value: value of message
        :return: True or False
        """
        out_buff = self._create_msg(msg_id, msg_value)

        if out_buff is None:
            LOG.error('create msg failed')
            return False

        return self._send(out_buff)

    def proc_src_img_msg(self, src_img_dict):
        """ProcSrcImgMsg: create message and send to GameReg
        
        :param src_img_dict: image information saved with dictinary format,
                           keywords is 'frameSeq', 'width', 'height''image','deviceIndex'
        :return: True or False
        """
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_SRC_IMAGE_INFO

        st_src_image_info = msg.stSrcImageInfo
        try:
            st_src_image_info.uFrameSeq = src_img_dict['frameSeq']
            st_src_image_info.nWidth = src_img_dict['width']
            st_src_image_info.nHeight = src_img_dict['height']
            st_src_image_info.byImageData = src_img_dict['image'].tobytes()
            st_src_image_info.uDeviceIndex = src_img_dict['deviceIndex']
        except:
            raise ValueError('error')

        msg_buff = msg.SerializeToString()

        if msg_buff is None:
            LOG.error('create msg failed')
            return False

        return self._send(msg_buff)

    def proc_ui_src_img_msg(self, src_img_dict):
        msg_pb = common_pb2.tagMessage()
        msg_pb.eMsgID = common_pb2.MSG_UI_STATE_IMG

        msg_pb.stUIAPIState.eUIState = common_pb2.PB_UI_STATE_NORMAL

        msg_pb.stUIAPIState.stUIImage.uFrameSeq = src_img_dict['frameSeq']
        msg_pb.stUIAPIState.stUIImage.nWidth = src_img_dict['width']
        msg_pb.stUIAPIState.stUIImage.nHeight = src_img_dict['height']
        msg_pb.stUIAPIState.stUIImage.byImageData = src_img_dict['image'].tobytes()
        msg_pb.stUIAPIState.stUIImage.uDeviceIndex = src_img_dict['deviceIndex']
        msg_pb.stUIAPIState.eGameState = common_pb2.PB_STATE_NONE

        msg = msg_pb.SerializeToString()

        if msg is None:
            LOG.error('create msg failed')
            return False

        return self._send_ui(msg)

    def recv(self):
        """
        recv: receieve message from GameReg, the value is the result of imageReg and the processed image
        :return: True or False
        """
        msg_buff_ret = None
        LOG.debug("begin receive the message from gamereg, __game_reg_addr is {0} ".format(self.__game_reg_addr))
        msg_buff = tbus.RecvFrom(self.__game_reg_addr)
        while msg_buff is not None:
            msg_buff_ret = msg_buff
            msg_buff = tbus.RecvFrom(self.__game_reg_addr)

        if msg_buff_ret:
            LOG.debug("receive the message from gamereg")
            # msg = msgpack.unpackb(msgBuffRet, object_hook=mn.decode, encoding='utf-8')
            msg = self._unserial_result_msg(msg_buff_ret)
            if msg:
                frame_seq = msg['value'].get('frameSeq')
                LOG.debug('recv frame data, frameIndex={0}'.format(frame_seq))
                return msg
            else:
                LOG.error("unserial result message failed")
                return None
        return None

    def recv_ui(self):
        msg_buff_ret = None
        msg_buff = tbus.RecvFrom(self.__uirecognize_addr)
        while msg_buff is not None:
            msg_buff_ret = msg_buff
            msg_buff = tbus.RecvFrom(self.__uirecognize_addr)

        if msg_buff_ret:
            LOG.debug("receive the message from UI")
            # msg = msgpack.unpackb(msgBuffRet, object_hook=mn.decode, encoding='utf-8')
            msg = self._unserial_ui_result_msg(msg_buff_ret)
            if msg:
                return msg
            else:
                LOG.error("unserial result message failed")
                return None
        return None

    def recv_agent(self):
        result_buff = None
        if self.__agent_addr is None:
            return result_buff

        buff = tbus.RecvFrom(self.__agent_addr)
        while buff is not None:
            result_buff = buff
            buff = tbus.RecvFrom(self.__agent_addr)

        if result_buff is not None:
            return self._unserial_agent_msg(result_buff)

    def release(self):
        """
        tbus exit
        :return: None
        """
        LOG.info('tbus exit...')
        tbus.Exit(self.__self_addr)

    def _unserial_agent_msg(self, msg):
        msgPB = common_pb2.tagMessage()
        msgPB.ParseFromString(msg)
        msg_id = msgPB.eMsgID

        # 收到agent原图像的消息
        if msg_id == common_pb2.MSG_SRC_IMAGE_INFO:
            agent_image_info = dict()
            data = np.fromstring(msgPB.stSrcImageInfo.byImageData, np.uint8)
            image = np.reshape(data, (msgPB.stSrcImageInfo.nHeight, msgPB.stSrcImageInfo.nWidth, 3))

            agent_image_info['image'] = image
            agent_image_info['uFrameSeq'] = msgPB.stSrcImageInfo.uFrameSeq

            return agent_image_info
        # 收到agent动作的消息
        elif msg_id == common_pb2.MSG_AI_ACTION:
            agent_action_info = dict()
            action_data = msgPB.stAIAction.byAIActionBuff

            action_dict = msgpack.unpackb(action_data, object_hook=msgpack_numpy.decode, encoding='utf-8')

            action_id = action_dict['action_id']
            if self.__device_type == DeviceType.Android.value:
                if action_id in ACTION_NAMES.keys():
                    action_name = ACTION_NAMES[action_id]
                else:
                    LOG.error("unkown android action id {}".format(action_id))
                    action_name = 'unkown android action id {}'.format(action_id)
            elif self.__device_type == DeviceType.Windows.value:
                if action_id in WINDOW_ACTION_NAMES.keys():
                    action_name = WINDOW_ACTION_NAMES[action_id]
                else:
                    LOG.error("unkown window action id {}".format(action_id))
                    action_name = 'unkown window action id {}'.format(action_id)

            agent_action_info['action_name'] = action_name
            if action_id in [ACTION_ID_DOWN, ACTION_ID_UP, ACTION_ID_MOVE, ACTION_ID_CLICK, ACTION_ID_SWIPEMOVE]:
                agent_action_info['px'] = action_dict['px']
                agent_action_info['py'] = action_dict['py']
            elif action_id in [ACTION_ID_SWIPE, ACTION_ID_SWIPEDOWN]:
                agent_action_info['start_x'] = action_dict['start_x']
                agent_action_info['start_y'] = action_dict['start_y']
                agent_action_info['end_x'] = action_dict['end_x']
                agent_action_info['end_y'] = action_dict['end_y']
            return agent_action_info

        else:
            LOG.error("receive wrong msg {}".format(msg_id))
            return None

    def _unserial_ui_result_msg(self, msg):
        msg_pb = common_pb2.tagMessage()
        msg_pb.ParseFromString(msg)
        msg_id = msg_pb.eMsgID
        if msg_id != common_pb2.MSG_UI_ACTION:
            LOG.error('wrong msg id: {}'.format(msg_id))
            return None

        ui_result_dict = dict()
        ui_result_dict['actions'] = []
        for ui_unit_action in msg_pb.stUIAction.stUIUnitAction:
            e_ui_action = ui_unit_action.eUIAction
            action = dict()
            action['type'] = e_ui_action
            action['points'] = []
            if action['type'] == common_pb2.PB_UI_ACTION_CLICK:
                point = {}
                point["x"] = ui_unit_action.stClickPoint.nX
                point["y"] = ui_unit_action.stClickPoint.nY
                action['points'].append(point)
            elif action['type'] == common_pb2.PB_UI_ACTION_DRAG:
                for drag_point in ui_unit_action.stDragPoints:
                    point = {}
                    point["x"] = drag_point.nX
                    point["y"] = drag_point.nY
                    action['points'].append(point)

            ui_result_dict['actions'].append(action)
        data = np.fromstring(msg_pb.stUIAction.stSrcImageInfo.byImageData, np.uint8)
        ui_result_dict['image'] = np.reshape(data,
                                             (msg_pb.stUIAction.stSrcImageInfo.nHeight,
                                              msg_pb.stUIAction.stSrcImageInfo.nWidth, 3))
        return ui_result_dict

    def _create_msg(self, msg_id, msg_value):
        msg_dict = dict()
        msg_dict['msg_id'] = msg_id
        msg_dict['value'] = msg_value
        # out_buff = msgpack.packb(msg_dict, use_bin_type=True)

        out_buff = self._serial_send_msg(msg_dict)

        return out_buff

    def _send(self, out_buff):
        ret = tbus.SendTo(self.__game_reg_addr, out_buff)
        if ret != 0:
            LOG.error('TBus Send To  GameReg Addr return code[{0}]'.format(ret))
            return False

        return True

    def _send_ui(self, out_buff):
        ret = tbus.SendTo(self.__uirecognize_addr, out_buff)
        if ret != 0:
            LOG.error('TBus Send To UI Addr return code[{0}]'.format(ret))
            return False

        return True

    def _register(self):
        """
        registe message hander
        serial message: MSG_SEND_GROUP_ID, MSG_SEND_ADD_TASK, MSG_SEND_CHG_TASK, MSG_SEND_TASK_FLAG,
                        MSG_SEND_DEL_TASK, MSG_SEND_TASK_CONF, MSG_REGER_STUCK_TYPE, MSG_REGER_FIXOBJ_TYPE,
                        MSG_REGER_PIX_TYPE, MSG_REGER_DEFORM_TYPE, MSG_REGER_NUMBER_TYPE, MSG_REGER_FIXBLOOD_TYPE,
                        MSG_REGER_KING_GLORY_BOOD_TYPE, MSG_REGER_MAPREG_TYPE, MSG_REGER_MAPDIRECTIONREG_TYPE,
                        MSG_REGER_MULTCOLORVAR_TYPE, MSG_REGER_SHOOTGAMEBLOOD_TYPE, MSG_REGER_SHOOTGAMEHURT_TYPE

        unserial message:gameregProtoc_pb2.TYPE_STUCKREG, gameregProtoc_pb2.TYPE_FIXOBJREG,
                         gameregProtoc_pb2.TYPE_PIXREG, gameregProtoc_pb2.TYPE_DEFORMOBJ,
                         gameregProtoc_pb2.TYPE_NUMBER, gameregProtoc_pb2.TYPE_FIXBLOOD,
                         gameregProtoc_pb2.TYPE_KINGGLORYBLOOD, gameregProtoc_pb2.TYPE_MAPREG,
                         gameregProtoc_pb2.TYPE_MAPDIRECTIONREG,gameregProtoc_pb2.TYPE_MULTCOLORVAR,
                         gameregProtoc_pb2.TYPE_SHOOTBLOOD, gameregProtoc_pb2.TYPE_SHOOTHURT
        :return: None
        """
        self.__serial_msg_handle[MSG_SEND_GROUP_ID] = self._serial_task
        self.__serial_msg_handle[MSG_SEND_ADD_TASK] = self._serial_add_task
        self.__serial_msg_handle[MSG_SEND_CHG_TASK] = self._serial_chg_task
        self.__serial_msg_handle[MSG_SEND_TASK_FLAG] = self._serial_flag_task
        self.__serial_msg_handle[MSG_SEND_DEL_TASK] = self._serial_del_task
        self.__serial_msg_handle[MSG_SEND_TASK_CONF] = self._serial_conf_task

        self.__serial_reger_handle[MSG_REGER_STUCK_TYPE] = self._serial_stuck_reg
        self.__serial_reger_handle[MSG_REGER_FIXOBJ_TYPE] = self._serial_fix_obj_reg
        self.__serial_reger_handle[MSG_REGER_PIX_TYPE] = self._serial_pix_reg
        self.__serial_reger_handle[MSG_REGER_DEFORM_TYPE] = self._serial_deform_reg
        self.__serial_reger_handle[MSG_REGER_NUMBER_TYPE] = self._serial_number_reg
        self.__serial_reger_handle[MSG_REGER_FIXBLOOD_TYPE] = self._serial_fix_blood_reg
        self.__serial_reger_handle[MSG_REGER_KING_GLORY_BOOD_TYPE] = self._serial_king_glory_blood
        self.__serial_reger_handle[MSG_REGER_MAPREG_TYPE] = self._serial_map_reg
        self.__serial_reger_handle[MSG_REGER_MAPDIRECTIONREG_TYPE] = self._serial_map_direction_reg
        self.__serial_reger_handle[MSG_REGER_MULTCOLORVAR_TYPE] = self._serial_mult_color_var
        self.__serial_reger_handle[MSG_REGER_SHOOTGAMEBLOOD_TYPE] = self._serial_shoot_game_blood
        self.__serial_reger_handle[MSG_REGER_SHOOTGAMEHURT_TYPE] = self._serial_shoot_game_hurt

        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_STUCKREG] = self._unserial_stuck_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_FIXOBJREG] = self._unserial_fix_obj_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_PIXREG] = self._unserial_pix_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_DEFORMOBJ] = self._unserial_deform_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_NUMBER] = self._unserial_number_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_FIXBLOOD] = self._unserial_fix_blood_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_KINGGLORYBLOOD] = self._unserial_king_glory_blood_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_MAPREG] = self._unserial_map_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_MAPDIRECTIONREG] = self._unserial_map_direction_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_MULTCOLORVAR] = self._unserial_mult_color_var
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_SHOOTBLOOD] = self._unserial_blood_reg_result
        self.__unseiral_reger_handle[gameregProtoc_pb2.TYPE_SHOOTHURT] = self._unserial_hurt_reg_result

    def _serial_send_msg(self, msg_dict):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_GAMEREG_INFO
        msg_agent = msg.stPBAgentMsg
        msg_agent.eAgentMsgID = self._get_value_from_dict(msg_dict, 'msg_id')

        self.__serial_msg_handle[msg_agent.eAgentMsgID](
            msg_agent, self._get_value_from_dict(msg_dict, 'value')
        )

        msg_buff = msg.SerializeToString()
        return msg_buff

    def _serial_task(self, msg, msg_value):
        value = msg.stPBAgentTaskValue
        value.uGroupID = self._get_value_from_dict(msg_value, 'groupID')
        for task_value in self._get_value_from_dict(msg_value, 'task'):
            task_pb = value.stPBAgentTaskTsks.add()
            self.__serial_reger_handle[self._get_value_from_dict(task_value, 'type')](task_pb, task_value)

    def _serial_chg_task(self, msg, msg_value):
        value = msg.stPBAgentTaskValue
        value.uGroupID = 1
        for task_value in msg_value:
            task_pb = value.stPBAgentTaskTsks.add()
            self.__serial_reger_handle[self._get_value_from_dict(task_value, 'type')](task_pb, task_value)

    def _serial_add_task(self, msg, msg_value):
        value = msg.stPBAgentTaskValue
        value.uGroupID = 1
        for task_value in msg_value:
            task_pb = value.stPBAgentTaskTsks.add()
            self.__serial_reger_handle[self._get_value_from_dict(task_value, 'type')](task_pb, task_value)

    def _serial_flag_task(self, msg, msg_value):
        for task_id in msg_value:
            value = msg.stPBTaskFlagMaps.add()
            value.nTaskID = int(task_id)
            value.bFlag = msg_value[task_id]

    def _serial_del_task(self, msg, msg_value):
        for key in msg_value:
            msg.nDelTaskIDs.append(key)

    def _serial_conf_task(self, msg, msg_value):
        for file_name in msg_value:
            if file_name is not None:
                msg.strConfFileName.append(file_name)

    def _set_map_reg_elements_from_dict(self, task_pb, task_value, is_direction=True):
        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            rect.nX = self._get_value_from_dict(self._get_value_from_dict(element, 'ROI'), 'x')
            rect.nY = self._get_value_from_dict(self._get_value_from_dict(element, 'ROI'), 'y')
            rect.nW = self._get_value_from_dict(self._get_value_from_dict(element, 'ROI'), 'w')
            rect.nH = self._get_value_from_dict(self._get_value_from_dict(element, 'ROI'), 'h')

            element_pb.strMyLocCondition = self._get_value_from_dict(element, 'myLocCondition')
            element_pb.strViewLocCondition = self._get_value_from_dict(element, 'viewLocCondition')
            element_pb.strMaskPath = element.get('mapMaskPath') or str()
            element_pb.nMaxPointNum = self._get_value_from_dict(element, 'maxPointNum')
            element_pb.nFilterSize = self._get_value_from_dict(element, 'filterSize')

            if is_direction:
                element_pb.nDilateSize = self._get_value_from_dict(element, 'dilateSize')
                element_pb.nErodeSize = self._get_value_from_dict(element, 'erodeSize')
                element_pb.nRegionSize = self._get_value_from_dict(element, 'regionSize')
            else:
                element_pb.strFriendsCondition = self._get_value_from_dict(element, 'friendsLocCondition')
                element_pb.strMapPath = self._get_value_from_dict(element, 'mapTempPath')

    def _serial_map_reg(self, task_pb, task_value):
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_MAPREG
        self._set_map_reg_elements_from_dict(task_pb, task_value, is_direction=False)

    def _serial_map_direction_reg(self, task_pb, task_value):
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_MAPDIRECTIONREG
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')
        self._set_map_reg_elements_from_dict(task_pb, task_value, is_direction=True)

    def _serial_mult_color_var(self, task_pb, task_value):
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_MULTCOLORVAR
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()
            element_pb.strImgFilePath = self._get_value_from_dict(element, 'imageFilePath')

    def _serial_shoot_game_blood(self, task_pb, task_value):
        """
        ShootGameBlood, this recongnizer method only used by ShootGame
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_SHOOTBLOOD
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.nFilterSize = self._get_value_from_dict(element, 'filterSize')
            element_pb.nBloodLength = self._get_value_from_dict(element, 'bloodLength')
            element_pb.nMaxPointNum = self._get_value_from_dict(element, 'maxPointNum')
            element_pb.fMinScale = self._get_value_from_dict(element, 'minScale')
            element_pb.fMaxScale = self._get_value_from_dict(element, 'maxScale')
            element_pb.nScaleLevel = self._get_value_from_dict(element, 'scaleLevel')

            templates = element_pb.stPBTemplates
            for templ in self._get_value_from_dict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._serial_template(template, templ)

    def _serial_shoot_game_hurt(self, task_pb, task_value):
        """
        ShootGameHurt, this recongnizer method only used by ShootGame
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_SHOOTHURT
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.fThreshold = self._get_value_from_dict(element, 'threshold')

    def _set_element_for_blood(self, task_pb, task_value, is_deform=True):
        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.fThreshold = self._get_value_from_dict(element, 'threshold')
            element_pb.strCfgPath = self._get_value_from_dict(element, 'cfgPath')
            element_pb.strWeightPath = self._get_value_from_dict(element, 'weightPath')
            element_pb.strNamePath = self._get_value_from_dict(element, 'namePath')
            element_pb.strMaskPath = element.get('maskPath') or str()
            if not is_deform:
                element_pb.nBloodLength = self._get_value_from_dict(element, 'bloodLength')
                element_pb.nMaxPointNum = self._get_value_from_dict(element, 'maxPointNum')
                element_pb.nFilterSize = self._get_value_from_dict(element, 'filterSize')
                element_pb.fMinScale = self._get_value_from_dict(element, 'minScale')
                element_pb.fMaxScale = self._get_value_from_dict(element, 'maxScale')
                element_pb.nScaleLevel = self._get_value_from_dict(element, 'scaleLevel')

                templates = element_pb.stPBTemplates
                for templ in self._get_value_from_dict(element, 'templates'):
                    template = templates.stPBTemplates.add()
                    self._serial_template(template, templ)

    def _serial_king_glory_blood(self, task_pb, task_value):
        """
        KingGloryBlood, this recongnizer method only used by KingGlory
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_KINGGLORYBLOOD
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        self._set_element_for_blood(task_pb, task_value, is_deform=False)

    def _serial_fix_blood_reg(self, task_pb, task_value):
        """
        FixBloodReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_FIXBLOOD
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.strCondition = self._get_value_from_dict(element, 'condition')
            element_pb.nFilterSize = self._get_value_from_dict(element, 'filterSize')
            element_pb.nBloodLength = self._get_value_from_dict(element, 'bloodLength')
            element_pb.nMaxPointNum = self._get_value_from_dict(element, 'maxPointNum')

    def _serial_stuck_reg(self, task_pb, task_value):
        """
        StuckReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_STUCKREG
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.fIntervalTime = self._get_value_from_dict(element, 'intervalTime')
            element_pb.fThreshold = self._get_value_from_dict(element, 'threshold')

    def _serial_fix_obj_reg(self, task_pb, task_value):
        """
        FixObjReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_FIXOBJREG
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.strAlgorithm = self._get_value_from_dict(element, 'algorithm')
            element_pb.fMinScale = self._get_value_from_dict(element, 'minScale')
            element_pb.fMaxScale = self._get_value_from_dict(element, 'maxScale')
            element_pb.nScaleLevel = self._get_value_from_dict(element, 'scaleLevel')
            element_pb.nMaxBBoxNum = element.get('maxBBoxNum') or 1

            templates = element_pb.stPBTemplates
            for templ in self._get_value_from_dict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._serial_template(template, templ)

    def _serial_pix_reg(self, task_pb, task_value):
        """
        PixReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_PIXREG
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.strCondition = self._get_value_from_dict(element, 'condition')
            element_pb.nFilterSize = self._get_value_from_dict(element, 'filterSize')

    def _serial_deform_reg(self, task_pb, task_value):
        """
        DeformReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_DEFORMOBJ
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')
        self._set_element_for_blood(task_pb, task_value, is_deform=True)

    def _serial_number_reg(self, task_pb, task_value):
        """
        NumberReg: common recongnizer method
        """
        task_pb.nTaskID = self._get_value_from_dict(task_value, 'taskID')
        task_pb.eType = gameregProtoc_pb2.TYPE_NUMBER
        # task_pb.nSkipFrame = self._get_value_from_dict(task_value, 'skipFrame')

        for element in self._get_value_from_dict(task_value, 'elements'):
            element_pb = task_pb.stPBAgentTaskElements.add()

            rect = element_pb.stPBRect
            self._serial_rect(rect, self._get_value_from_dict(element, 'ROI'))

            element_pb.strAlgorithm = self._get_value_from_dict(element, 'algorithm')
            element_pb.fMinScale = self._get_value_from_dict(element, 'minScale')
            element_pb.fMaxScale = self._get_value_from_dict(element, 'maxScale')
            element_pb.nScaleLevel = self._get_value_from_dict(element, 'scaleLevel')

            templates = element_pb.stPBTemplates
            for templ in self._get_value_from_dict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._serial_template(template, templ)

    def _unserial_result_msg(self, msg):
        result = gameregProtoc_pb2.tagPBAgentMsg()
        result.ParseFromString(msg)
        res_dict = dict()
        res_dict['msg_id'] = result.eAgentMsgID
        res_dict['value'] = {}
        res_dict['value']['frameSeq'] = result.stPBResultValue.nFrameSeq
        res_dict['value']['deviceIndex'] = result.stPBResultValue.nDeviceIndex
        res_dict['value']['strJsonData'] = result.stPBResultValue.strJsonData
        res_dict['value']['groupID'] = 1  # for test
        data = np.fromstring(result.stPBResultValue.byImgData, np.uint8)
        res_dict['value']['image'] = np.reshape(
            data, (result.stPBResultValue.nHeight, result.stPBResultValue.nWidth, 3)
        )

        res_dict['value']['result'] = {}
        for result in result.stPBResultValue.stPBResult:
            res_dict['value']['result'][result.nTaskID] = self.__unseiral_reger_handle[result.eRegType](result)
        return res_dict

    def _parse_fix_obj_box(self, res, res_single_dict):
        for boxe in res.stPBBoxs:
            res_boxe = {}
            res_boxe['tmplName'] = boxe.strTmplName
            res_boxe['score'] = boxe.fScore
            res_boxe['scale'] = boxe.fScale
            res_boxe['classID'] = boxe.nClassID
            res_boxe['x'] = boxe.stPBRect.nX
            res_boxe['y'] = boxe.stPBRect.nY
            res_boxe['w'] = boxe.stPBRect.nW
            res_boxe['h'] = boxe.stPBRect.nH
            res_single_dict['boxes'].append(res_boxe)

    def _unserial_fix_obj_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['ROI'] = {}
            res_single_dict['ROI']['x'] = res.stPBROI.nX
            res_single_dict['ROI']['y'] = res.stPBROI.nY
            res_single_dict['ROI']['w'] = res.stPBROI.nW
            res_single_dict['ROI']['h'] = res.stPBROI.nH
            res_single_dict['boxes'] = []
            self._parse_fix_obj_box(res, res_single_dict)
            res_list.append(res_single_dict)

        return res_list

    def _unserial_king_glory_blood_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['ROI'] = {}
            res_single_dict['ROI']['x'] = res.stPBROI.nX
            res_single_dict['ROI']['y'] = res.stPBROI.nY
            res_single_dict['ROI']['w'] = res.stPBROI.nW
            res_single_dict['ROI']['h'] = res.stPBROI.nH

            res_single_dict['bloods'] = []

            for blood in res.stPBBloods:
                res_blood = {}
                res_blood['level'] = blood.nLevel
                res_blood['score'] = blood.fScore
                res_blood['percent'] = blood.fPercent
                res_blood['classID'] = blood.nClassID
                res_blood['name'] = blood.strName
                res_blood['x'] = blood.stPBRect.nX
                res_blood['y'] = blood.stPBRect.nY
                res_blood['w'] = blood.stPBRect.nW
                res_blood['h'] = blood.stPBRect.nH
                res_single_dict['bloods'].append(res_blood)

            res_list.append(res_single_dict)

        return res_list

    def _unserial_map_reg_result_element(self, res, is_direction=True):
        res_single_dict = {}
        res_single_dict['flag'] = bool(res.nFlag)

        res_single_dict['ROI'] = {}
        res_single_dict['ROI']['x'] = res.stPBROI.nX
        res_single_dict['ROI']['y'] = res.stPBROI.nY
        res_single_dict['ROI']['w'] = res.stPBROI.nW
        res_single_dict['ROI']['h'] = res.stPBROI.nH

        res_single_dict['viewAnglePoint'] = {}
        res_single_dict['viewAnglePoint']['x'] = res.stPBViewAnglePoint.nX
        res_single_dict['viewAnglePoint']['y'] = res.stPBViewAnglePoint.nY

        res_single_dict['myLocPoint'] = {}
        res_single_dict['myLocPoint']['x'] = res.stPBMyLocPoint.nX
        res_single_dict['myLocPoint']['y'] = res.stPBMyLocPoint.nY
        if is_direction:
            res_single_dict['friendsLocPoints'] = []
            for point in res.stPBPoints:
                res_point = {}
                res_point['x'] = point.nX
                res_point['y'] = point.nY
                res_single_dict['friendsLocPoints'].append(res_point)
        return res_single_dict

    def _unserial_map_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = self._unserial_map_reg_result_element(res, is_direction=True)
            res_list.append(res_single_dict)
        return res_list

    def _unserial_map_direction_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = self._unserial_map_reg_result_element(res, is_direction=False)
            res_list.append(res_single_dict)
        return res_list

    def _unserial_mult_color_var(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)

            res_single_dict['colorMeanVar'] = []
            for value in res.fColorMeanVars:
                res_single_dict['colorMeanVar'].append(value)

            res_list.append(res_single_dict)

        return res_list

    def _unserial_blood_reg_result_element(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['percent'] = res.fNum
            res_single_dict['ROI'] = {}
            res_single_dict['ROI']['x'] = res.stPBROI.nX
            res_single_dict['ROI']['y'] = res.stPBROI.nY
            res_single_dict['ROI']['w'] = res.stPBROI.nW
            res_single_dict['ROI']['h'] = res.stPBROI.nH

            res_single_dict['box'] = {}
            res_single_dict['box']['x'] = res.stPBRect.nX
            res_single_dict['box']['y'] = res.stPBRect.nY
            res_single_dict['box']['w'] = res.stPBRect.nW
            res_single_dict['box']['h'] = res.stPBRect.nH

            res_list.append(res_single_dict)
        return res_list

    def _unserial_blood_reg_result(self, result):
        """ Shoot game

        :param result:
        :return:
        """
        return self._unserial_blood_reg_result_element(result)

    def _unserial_hurt_reg_result(self, result):
        """ Shoot game

        :param result:
        :return:
        """
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['ROI'] = {}
            res_single_dict['ROI']['x'] = res.stPBROI.nX
            res_single_dict['ROI']['y'] = res.stPBROI.nY
            res_single_dict['ROI']['w'] = res.stPBROI.nW
            res_single_dict['ROI']['h'] = res.stPBROI.nH

            res_list.append(res_single_dict)

        return res_list

    def _unserial_fix_blood_reg_result(self, result):
        return self._unserial_blood_reg_result_element(result)

    def _unserial_pix_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['points'] = []
            for point in res.stPBPoints:
                res_point = {}
                res_point['x'] = point.nX
                res_point['y'] = point.nY
                res_single_dict['points'].append(res_point)

            res_list.append(res_single_dict)

        return res_list

    def _unserial_stuck_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['x'] = res.stPBRect.nX
            res_single_dict['y'] = res.stPBRect.nY
            res_single_dict['w'] = res.stPBRect.nW
            res_single_dict['h'] = res.stPBRect.nH
            res_list.append(res_single_dict)

        return res_list

    def _unserial_deform_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['boxes'] = []

            self._parse_fix_obj_box(res, res_single_dict)
            res_list.append(res_single_dict)

        return res_list

    def _unserial_number_reg_result(self, result):
        res_list = []
        for res in result.stPBResultRes:
            res_single_dict = {}
            res_single_dict['flag'] = bool(res.nFlag)
            res_single_dict['num'] = res.fNum
            res_single_dict['x'] = res.stPBRect.nX
            res_single_dict['y'] = res.stPBRect.nY
            res_single_dict['w'] = res.stPBRect.nW
            res_single_dict['h'] = res.stPBRect.nH
            res_list.append(res_single_dict)

        return res_list

    def _serial_rect(self, pb_rect, value_rect):
        pb_rect.nX = self._get_value_from_dict(value_rect, 'x')
        pb_rect.nY = self._get_value_from_dict(value_rect, 'y')
        pb_rect.nW = self._get_value_from_dict(value_rect, 'w')
        pb_rect.nH = self._get_value_from_dict(value_rect, 'h')

    def _serial_template(self, pb_template, value_template):
        pb_template.strPath = self._get_value_from_dict(value_template, 'path')
        pb_template.strName = self._get_value_from_dict(value_template, 'name')
        hrect = pb_template.stPBRect
        self._serial_rect(hrect, self._get_value_from_dict(value_template, 'location'))
        pb_template.fThreshold = self._get_value_from_dict(value_template, 'threshold')
        pb_template.nClassID = self._get_value_from_dict(value_template, 'classID')

    def _get_value_from_dict(self, dic, key):
        if key not in dic.keys():
            LOG.error("{} is needed".format(key))
            raise Exception('{} is needed'.format(key))

        return dic[key]
