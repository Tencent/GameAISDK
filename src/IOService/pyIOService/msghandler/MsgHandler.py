# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from common.CommonContext import IO_SERVICE_CONTEXT
from common.Define import BASE_64_DECODE_IMG_SEND_TYPE, MSG_ID_UI_ACTION, ACTION_ID_NONE, UI_ACTION_CONTACT, \
    ACTION_ID_CLICK, ACTION_ID_SWIPE, GAME_STATE_START, GAME_STATE_OVER, GAME_STATE_MATCH_WIN, GAME_STATE_UI, \
    GAME_STATE_NONE, TASK_STATUS_NONE, TASK_STATUS_INIT_SUCCESS, TASK_STATUS_INIT_FAILURE, MSG_ID_CONTROL_REP, \
    MSG_ID_CLIENT_REP, CLIENT_REP_CODE_OK, CLIENT_REP_CODE_INVALID_KEY, MSG_ID_SOURCE_RES, RESTART_RESULT_SUCCESS, \
    RESTART_RESULT_FAILURE, MSG_ID_REPORT, MSG_ID_REGISTER, MSG_ID_UNREGISTER, MSG_ID_GAME_STATE, \
    MSG_ID_AGENT_STATE, MSG_ID_AI_SERVICE_STATE, MSG_ID_NEW_TASK, MSG_ID_CONTROL_REQ, MSG_ID_CLIENT_DATA,\
    MSG_ID_CLIENT_REQ, MSG_ID_CHANGE_GAME_STATE, MSG_ID_PAUSE, MSG_ID_RESTORE, MSG_ID_RESTART, MSG_ID_SOURCE_REQ, \
    MSG_ID_CLIENT_UI_REQ, MSG_ID_RESTART_RESULT, MSG_ID_AI_TRAIN_SCHEDULE, ACTION_ID_RESET
from protocol import common_pb2
from tools.SpeedCheck import IOSpeedCheck

LOG = logging.getLogger('IOService')


class MsgHandler(object):
    """
    IOService MsgHandler implementation for handling all messages
    """
    def __init__(self, commMgr, clientSocket, httpClientConnect, controlSocket):
        self.__commMgr = commMgr
        self.__clientSocket = clientSocket
        self.__controlSocket = controlSocket
        self.__httpClientConnect = httpClientConnect
        self.__innerMsgDict = {}
        self.__controlMsgDict = {}
        self.__clientMsgDict = {}
        self.__httpClientMsgDict = {}
        self.__speedCheck = IOSpeedCheck()

    def Initialize(self):
        """
        Initialize the message handler dictionary(map)
        :return: True
        """
        # Initialize the message handler dictionary(map)
        self._RegisterInnerMsgHandler(common_pb2.MSG_UI_ACTION, self._OnUIAction)
        self._RegisterInnerMsgHandler(common_pb2.MSG_SERVICE_REGISTER, self._OnServiceRegister)
        self._RegisterInnerMsgHandler(common_pb2.MSG_TASK_REPORT, self._OnTaskReport)
        self._RegisterInnerMsgHandler(common_pb2.MSG_AI_ACTION, self._OnAIAction)
        self._RegisterInnerMsgHandler(common_pb2.MSG_SERVICE_STATE, self._OnServiceState)
        self._RegisterInnerMsgHandler(common_pb2.MSG_AGENT_STATE, self._OnAgentState)
        self._RegisterInnerMsgHandler(common_pb2.MSG_RESTART_RESULT, self._OnRestartResult)
        self._RegisterInnerMsgHandler(common_pb2.MSG_IM_TRAIN_STATE, self._OnIMTrainState)
        self._RegisterInnerMsgHandler(common_pb2.MSG_PROJECT_SOURCE_RES, self._get_source_response)

        self._RegisterControlMsgHandler(MSG_ID_NEW_TASK, self._OnNewTask)
        self._RegisterControlMsgHandler(MSG_ID_CONTROL_REQ, self._OnControlReq)

        self._RegisterClientMsgHandler(MSG_ID_CLIENT_DATA, self._OnClientData)
        self._RegisterClientMsgHandler(MSG_ID_CLIENT_REQ, self._OnClientReq)
        self._RegisterClientMsgHandler(MSG_ID_CHANGE_GAME_STATE, self._OnChangeGameState)
        self._RegisterClientMsgHandler(MSG_ID_PAUSE, self._OnPause)
        self._RegisterClientMsgHandler(MSG_ID_RESTORE, self._OnRestore)
        self._RegisterClientMsgHandler(MSG_ID_RESTART, self._OnRestart)

        # 接收来自aiclient的获取source请求，处理完毕后返回信息给aiclient
        self._RegisterClientMsgHandler(MSG_ID_SOURCE_REQ, self._get_source_info)


        self._RegisterHttpClientMsgHandler(MSG_ID_CLIENT_UI_REQ, self._OnHttpClietUIRequest)

        return True

    def _RegisterInnerMsgHandler(self, msgID, msgFuncHandler):
        self.__innerMsgDict[msgID] = msgFuncHandler

    def _RegisterControlMsgHandler(self, cmdID, msgFuncHandler):
        self.__controlMsgDict[cmdID] = msgFuncHandler

    def _RegisterClientMsgHandler(self, cmdID, msgFuncHandler):
        self.__clientMsgDict[cmdID] = msgFuncHandler

    def _RegisterHttpClientMsgHandler(self, cmdID, msgFuncHandler):
        self.__httpClientMsgDict[cmdID] = msgFuncHandler

    def Update(self):
        """
        Update the msg handler, handle the msgs from MC(Inner), ASM and AIClient
        :return:
        """
        self._UpdateInnerMsg()
        self._UpdateControlMsg()
        self._UpdateClientMsg()
        self._UpdateHttpClientMsg()

    def SendFrameMsgToMC(self, frameSeq, frame, extend):
        """
        Send GameFrame to MC
        :param frameSeq: Frame sequence
        :param frame: GameFrame
        :param extend: extend GameData
        :return:
        """
        msgBuff = self._CreatePBSrcImgMsg(frameSeq, frame, extend)
        LOG.debug('send frame data, frameIndex=%s', frameSeq)
        self.__commMgr.SendToMC(msgBuff)

    def SendAIServiceStateToAIControl(self, serviceState):
        """
        Send ServiceState to ASM
        :param serviceState: service state
        :return:
        """
        msg_data = self._CreateAIServiceStateMsg(serviceState)
        LOG.info('Send AIServiceState to AIControl, msg_data[%s]', msg_data)
        self.__controlSocket.Send(msg_data)

    def SendIMTrainStateToAIControl(self, progress):
        """
        Send IM Train State to ASM
        :param progress: IM Train progress
        :return:
        """
        msg_data = self._CreateIMTrainStateMsg(progress)
        LOG.info('Send IMTrainState to AIControl, msg_data[%s]', msg_data)
        self.__controlSocket.Send(msg_data)

    def SendAIServiceStateToClient(self, serviceState):
        """
        Send ServiceState to AIClient
        :param serviceState: service state
        :return:
        """
        msg_data = self._CreateAIServiceStateMsg(serviceState)
        LOG.info('Send AIServiceState to Client, msg_data[%s]', msg_data)
        self.__clientSocket.Send(msg_data)

    def SendRegisterToAIControl(self):
        """
        Send Register to ASM
        :return:
        """
        msg_data = self._CreateServerRegisterMsg()
        LOG.info('Send Register to AIControl, msg_data[%s]', msg_data)
        self.__controlSocket.Send(msg_data)

    def SendUnregisterToAIControl(self):
        """
        Send Unregister to ASM
        :return:
        """
        msg_data = self._CreateServiceUnregisterMsg()
        LOG.info('Send Unregister to AIControl, msg_data[%s]', msg_data)
        self.__controlSocket.Send(msg_data)

    def _UpdateInnerMsg(self):
        # Recv the message
        msgBuffList = self.__commMgr.RecvMsg()

        # if recv nothing, then exit
        if len(msgBuffList) == 0:
            return

        # parse the message and call handler function
        for msgBuff in msgBuffList:
            # Deserialize message
            msg = self._ParsePBMsg(msgBuff)
            # Call message handler function
            handleFunc = self.__innerMsgDict.get(msg.eMsgID)
            if handleFunc is not None:
                handleFunc(msg)
            else:
                LOG.warning('Unhandled MsgID[%s]', msg.eMsgID)

    @staticmethod
    def _ParsePBMsg(msgBuff):
        msg = common_pb2.tagMessage()
        msg.ParseFromString(msgBuff)
        return msg

    def _UpdateControlMsg(self):
        msgList = self.__controlSocket.Recv()

        for msg in msgList:
            # Deserialize message
            msgID = msg['msg_id']
            # Call message handler function
            handleFunc = self.__controlMsgDict.get(msgID)
            if handleFunc is not None:
                handleFunc(msg)
            else:
                LOG.warning('Unhandled CONTROL msgID[%s]', msgID)

    def _UpdateClientMsg(self):
        ret = False
        msgList = self.__clientSocket.Recv()

        if len(msgList) > 0:
            ret = True

        for msg in msgList:
            # Deserialize message
            msgID = msg['msg_id']
            # Call message handler function
            handleFunc = self.__clientMsgDict.get(msgID)
            if handleFunc is not None:
                handleFunc(msg)
            else:
                LOG.warning('Unhandled CLIENT msgID[%s]', msgID)
                ret = False

        return ret

    def _UpdateHttpClientMsg(self):
        ret = False
        msgList = self.__httpClientConnect.Recv()

        if len(msgList) > 0:
            ret = True

        for msg in msgList:
            # Deserialize message
            msgID = msg['msg_id']
            # Call message handler function
            handleFunc = self.__httpClientMsgDict.get(msgID)
            if handleFunc is not None:
                handleFunc(msg)
            else:
                LOG.warning('Unhandled Http Client msgID[%s]', msgID)
                ret = False

        return ret

    @staticmethod
    def _OnHttpClietUIRequest(msg):
        try:
            key = msg['key']
            frameData = msg['image_data']
            frameSeq = msg['img_id']
            extend = msg.get('extend', 'null')
            frameType = BASE_64_DECODE_IMG_SEND_TYPE
        except KeyError:
            LOG.error('Wrong client data, {0}'.format(msg))
            return

        LOG.debug('recv frame data, frameIndex=%s', frameSeq)

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            IO_SERVICE_CONTEXT['frame'] = frameData
            IO_SERVICE_CONTEXT['frame_type'] = frameType
            IO_SERVICE_CONTEXT['frame_seq'] = frameSeq
            IO_SERVICE_CONTEXT['extend'] = extend
        else:
            LOG.warning('Recv invalid frame, wrong key[%s]', key)

    def _OnAIAction(self, msg):
        frameSeq = msg.stAIAction.nFrameSeq
        actionData = msg.stAIAction.byAIActionBuff

        LOG.debug('send action data, frameIndex=%s', frameSeq)
        self.__speedCheck.AddSendAction(frameSeq)
        self.__clientSocket.Send(actionData)

    def _OnUIAction(self, msg):
        if IO_SERVICE_CONTEXT['io_service_type'] == 'HTTP':
            self._OnHttpClientUIAction(msg)
        else:
            self._OnClientUIAction(msg)

    def _OnClientUIAction(self, msg):
        gameState = msg.stUIAction.eGameState

        msg_data = dict()
        msg_data['img_id'] = msg.stUIAction.stSrcImageInfo.uFrameSeq
        msg_data['msg_id'] = MSG_ID_UI_ACTION
        msg_data['ui_id'] = msg.stUIAction.nUIID
        msg_data['actions'] = self._CreateUIActionList(msg)

        LOG.info('Send UI action to ai client:%s', msg_data)
        self.__clientSocket.Send(msg_data)

        self._RecordGameState(gameState)

        # report game state to asm
        msg_data = self._CreateTaskReportMsg()
        self.__controlSocket.Send(msg_data)

        # report game state to aiclient
        msg_data = self._CreateGameStateMsg()
        self.__clientSocket.Send(msg_data)

    def _OnHttpClientUIAction(self, msg):
        gameState = msg.stUIAction.eGameState

        msg_data = dict()
        msg_data['img_id'] = msg.stUIAction.stSrcImageInfo.uFrameSeq
        msg_data['msg_id'] = MSG_ID_UI_ACTION
        msg_data['ui_id'] = msg.stUIAction.nUIID
        msg_data['actions'] = self._CreateUIActionList(msg)

        self._RecordGameState(gameState)
        msg_data['game_state'] = IO_SERVICE_CONTEXT['game_state']

        LOG.info('Send UI action to http client:%s', msg_data)
        self.__httpClientConnect.Send(msg_data)

        # report game state to asm
        msg_data = self._CreateTaskReportMsg()
        self.__controlSocket.Send(msg_data)

    def _CreateUIActionList(self, msg):
        actionList = list()

        # when ui detect game over, add a reset action
        # if IO_SERVICE_CONTEXT['io_service_type'] != 'HTTP':
        gameState = msg.stUIAction.eGameState
        if gameState in [common_pb2.PB_STATE_OVER, common_pb2.PB_STATE_MATCH_WIN]:
            LOG.info('fork Reset action')
            action = self._ForkResetAction()
            actionList.append(action)

        uiActions = msg.stUIAction.stUIUnitAction
        for uiAction in uiActions:
            uiActionType = uiAction.eUIAction
            if uiActionType == common_pb2.PB_UI_ACTION_NONE:
                action = dict()
                action['action_id'] = ACTION_ID_NONE
            elif uiActionType == common_pb2.PB_UI_ACTION_CLICK:
                action = self._SinglePointOp(px=uiAction.stClickPoint.nX,
                                             py=uiAction.stClickPoint.nY,
                                             contact=UI_ACTION_CONTACT,
                                             action_id=ACTION_ID_CLICK,
                                             during_time=uiAction.nDuringTimeMs,
                                             wait_time=uiAction.nSleepTimeMs)
            elif uiActionType == common_pb2.PB_UI_ACTION_DRAG:
                action = self._DoublePointOp(start_x=uiAction.stDragPoints[0].nX,
                                             start_y=uiAction.stDragPoints[0].nY,
                                             end_x=uiAction.stDragPoints[1].nX,
                                             end_y=uiAction.stDragPoints[1].nY,
                                             contact=UI_ACTION_CONTACT,
                                             action_id=ACTION_ID_SWIPE,
                                             during_time=uiAction.nDuringTimeMs,
                                             wait_time=uiAction.nSleepTimeMs)
            else:
                LOG.warning('Unhandled uiActionType[%s]', uiActionType)
                continue

            actionList.append(action)

        return actionList

    @staticmethod
    def _RecordGameState(gameState):
        if gameState == common_pb2.PB_STATE_START:
            LOG.info('GameState START')
            IO_SERVICE_CONTEXT['game_state'] = GAME_STATE_START
        elif gameState == common_pb2.PB_STATE_OVER:
            LOG.info('GameState OVER')
            IO_SERVICE_CONTEXT['game_state'] = GAME_STATE_OVER
        elif gameState == common_pb2.PB_STATE_MATCH_WIN:
            LOG.info('GameState WIN')
            IO_SERVICE_CONTEXT['game_state'] = GAME_STATE_MATCH_WIN
        elif gameState == common_pb2.PB_STATE_UI:
            LOG.info('GameState UI')
            IO_SERVICE_CONTEXT['game_state'] = GAME_STATE_UI
        elif gameState == common_pb2.PB_STATE_NONE:
            LOG.info('GameState NONE')
            IO_SERVICE_CONTEXT['game_state'] = GAME_STATE_NONE
        else:
            LOG.warning('Unhandled GameState[%s]', gameState)
            return

    def _OnServiceRegister(self, msg):
        regType = msg.stServiceRegister.eRegisterType
        LOG.info('Recv ServiceRegister, regType[%s]', regType)
        if regType == common_pb2.PB_SERVICE_REGISTER:
            pass
            # msg_data = self._CreateServerRegisterMsg()
        elif regType == common_pb2.PB_SERVICE_UNREGISTER:
            IO_SERVICE_CONTEXT['task_state'] = TASK_STATUS_NONE

    def _OnTaskReport(self, msg):
        taskStatus = msg.stTaskReport.eTaskStatus
        LOG.info('Recv TaskReport, taskStatus[%s]', taskStatus)
        if taskStatus == common_pb2.PB_TASK_INIT_SUCCESS:
            IO_SERVICE_CONTEXT['task_state'] = TASK_STATUS_INIT_SUCCESS
        else:
            IO_SERVICE_CONTEXT['task_state'] = TASK_STATUS_INIT_FAILURE

        if IO_SERVICE_CONTEXT['task_id'] is not None:
            msg_data = self._CreateTaskReportMsg()
            LOG.info('Send TaskReport to AIControl, msg_data[%s]', msg_data)
            self.__controlSocket.Send(msg_data)
        else:
            LOG.info('Waiting for NewTask')

    def _OnServiceState(self, msg):
        serviceState = msg.stServiceState.nServiceState
        self.SendAIServiceStateToAIControl(serviceState)
        self.SendAIServiceStateToClient(serviceState)

    def _OnAgentState(self, msg):
        stateID = msg.stAgentState.eAgentState
        stateStr = msg.stAgentState.strAgentState
        LOG.info('Recv MSG_AGENT_STATE msg, AgentState:'
                 '%s/%s', msg.stAgentState.eAgentState, msg.stAgentState.strAgentState)
        msg_data = self._CreateAgentStateMsg(stateID, stateStr)
        self.__clientSocket.Send(msg_data)

    def _OnIMTrainState(self, msg):
        progress = msg.stIMTrainState.nProgress
        LOG.info('Recv MSG_IM_TRAIN_STATE msg, progress: %s', progress)
        self.SendIMTrainStateToAIControl(progress)

    def _OnNewTask(self, msg_data):
        IO_SERVICE_CONTEXT['task_id'] = msg_data['task_id']
        IO_SERVICE_CONTEXT['seesion_key'] = msg_data['key']

        LOG.info('Recv NewTask, task_id[%s]', msg_data['task_id'])
        LOG.info('IO_SERVICE_CONTEXT Update task_id=%s', msg_data['task_id'])
        LOG.info('IO_SERVICE_CONTEXT Update seesion_key=%s', msg_data['key'])

        if IO_SERVICE_CONTEXT['task_id'] is not None:
            msgBuff = self._CreatePBNewTaskMsg()
            self.__commMgr.SendToMC(msgBuff)

        if IO_SERVICE_CONTEXT['task_state'] != TASK_STATUS_NONE or IO_SERVICE_CONTEXT['test_mode']:
            msg_data = self._CreateTaskReportMsg()
            LOG.info('Send TaskReport to AIControl, msg_data[%s]', msg_data)
            self.__controlSocket.Send(msg_data)
        else:
            LOG.info('Waiting for TaskReport')

    def _OnClientData(self, msg_data):
        try:
            key = msg_data['key']
            frameData = msg_data['frame']
            frameSeq = msg_data['frame_seq']
            frameType = msg_data.get('frame_decode_type', None)
            if frameType is None:
                frameType = msg_data['send_img_type']
        except KeyError:
            LOG.error('recv wrong client data, %s', msg_data)
            return

        extend = msg_data.get('extend', 'null')

        LOG.debug('recv frame data, frameIndex=%s', frameSeq)

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            IO_SERVICE_CONTEXT['frame'] = frameData
            IO_SERVICE_CONTEXT['frame_type'] = frameType
            IO_SERVICE_CONTEXT['extend'] = extend
            IO_SERVICE_CONTEXT['frame_seq'] = frameSeq
            self.__speedCheck.AddRecvImg(frameSeq)
        else:
            LOG.warning('Recv invalid frame, wrong key[%s]', key)

    def _OnControlReq(self, msg_data):
        LOG.info('Recv control req msg[%s]', msg_data)

        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_CONTROL_REP
        self.__controlSocket.Send(msg_data)

    def _OnClientReq(self, msg_data):
        LOG.info('Recv client req msg[%s]', msg_data)
        key = msg_data['key']
        testID = msg_data.get('test_id', None)
        gameID = msg_data.get('game_id', None)
        gameVersion = msg_data.get('game_version', None)

        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_CLIENT_REP
        if key == IO_SERVICE_CONTEXT['seesion_key']:
            msg_data['code'] = CLIENT_REP_CODE_OK
            if not isinstance(testID, str):
                LOG.error('testID[%s] is not str', testID)
            elif not isinstance(gameID, int):
                LOG.error('gameID[%s] is not int', gameID)
            elif not isinstance(gameVersion, str):
                LOG.error('gameVersion[%s] is not str', gameVersion)
            else:
                msgBuff = self._CreatePBTestIDMsg(testID, gameID, gameVersion)
                LOG.info('Send testID[%s] gameID[%s] gameVersion[%s] to MC', testID, gameID, gameVersion)
                self.__commMgr.SendToMC(msgBuff)
        else:
            msg_data['code'] = CLIENT_REP_CODE_INVALID_KEY
            LOG.warning('Recv invalid req, wrong key[%s]', key)
        LOG.info("send the response to the ai client, msg_data:%s", msg_data)
        self.__clientSocket.Send(msg_data)

    def _OnChangeGameState(self, msg_data):
        LOG.info('Recv client Change GameState msg[%s]', msg_data)
        key = msg_data['key']

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            IO_SERVICE_CONTEXT['game_state'] = msg_data['game_state']
            msgBuff = self._CreatePBChangeGameStateMsg()
            self.__commMgr.SendToMC(msgBuff)
        else:
            LOG.warning('Recv invalid msg, wrong key[%s]', key)

    def _get_source_info(self, msg_data):
        """ 发送source的信息给aiclient, 告诉当前环境信息
        """
        LOG.info('receive message from ai client msg[%s]', msg_data)
        msg_buffer = self._create_pb_get_source_msg()
        self.__commMgr.SendToMC(msg_buffer)

    def _get_source_response(self, msg):
        LOG.info('receive the source response from mc msg[%s]', msg)
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_SOURCE_RES
        msg_data['device_type'] = msg.stSource.deviceType
        msg_data['long_edge'] = msg.stSource.longEdge
        msg_data['platform'] = msg.stSource.platform
        msg_data['window_size'] = msg.stSource.windowsSize
        msg_data['query_path'] = msg.stSource.queryPath
        LOG.info('send the source response to ai client msg[%s]', msg_data)
        self.__clientSocket.Send(msg_data)

    def _OnPause(self, msg_data):
        LOG.info('Recv Pause msg[%s]', msg_data)
        key = msg_data['key']

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            msgBuff = self._CreatePBPauseAgentMsg()
            self.__commMgr.SendToMC(msgBuff)
        else:
            LOG.warning('Recv invalid msg, wrong key[%s]', key)

    def _OnRestore(self, msg_data):
        LOG.info('Recv Restore msg[%s]', msg_data)
        key = msg_data['key']

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            msgBuff = self._CreatePBRestoreAgentMsg()
            self.__commMgr.SendToMC(msgBuff)
        else:
            LOG.warning('Recv invalid msg, wrong key[%s]', key)

    def _OnRestart(self, msg_data):
        LOG.info('Recv Restart msg[%s]', msg_data)
        key = msg_data['key']

        if key == IO_SERVICE_CONTEXT['seesion_key']:
            msgBuff = self._CreatePBRestartMsg()
            self.__commMgr.SendToMC(msgBuff)
        else:
            LOG.warning('Recv invalid msg, wrong key[%s]', key)

    def _OnRestartResult(self, msg):
        result = msg.stRestartResult.eRestartResult
        LOG.info('Recv MSG_RESTART_RESULT msg, Result:%s', result)

        if result == common_pb2.PB_RESTART_RESULT_SUCCESS:
            msg_data = self._CreateRestartResultMsg(RESTART_RESULT_SUCCESS)
        elif result == common_pb2.PB_RESTART_RESULT_FAILURE:
            msg_data = self._CreateRestartResultMsg(RESTART_RESULT_FAILURE)
        self.__clientSocket.Send(msg_data)

    @staticmethod
    def _CreateTaskReportMsg():
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_REPORT
        msg_data['task_id'] = IO_SERVICE_CONTEXT['task_id']
        msg_data['task_state'] = IO_SERVICE_CONTEXT['task_state']
        msg_data['game_state'] = IO_SERVICE_CONTEXT['game_state']
        return msg_data

    @staticmethod
    def _CreateServerRegisterMsg():
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_REGISTER
        msg_data['source_server_id'] = IO_SERVICE_CONTEXT['source_server_id']
        return msg_data

    @staticmethod
    def _CreateServiceUnregisterMsg():
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_UNREGISTER
        msg_data['source_server_id'] = IO_SERVICE_CONTEXT['source_server_id']
        return msg_data

    @staticmethod
    def _CreateGameStateMsg():
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_GAME_STATE
        msg_data['game_state'] = IO_SERVICE_CONTEXT['game_state']
        return msg_data

    @staticmethod
    def _CreateAgentStateMsg(stateID, stateStr):
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_AGENT_STATE
        msg_data['agent_state_id'] = stateID
        msg_data['agent_state_str'] = stateStr
        return msg_data

    @staticmethod
    def _create_source_info_message(content: dict):
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_SOURCE_RES
        msg_data['source'] = content['source']
        return msg_data

    @staticmethod
    def _CreatePBSrcImgMsg(frameSeq, frame, extend, deviceIndex=0):
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_SRC_IMAGE_INFO
        msg.stSrcImageInfo.uFrameSeq = frameSeq
        msg.stSrcImageInfo.nHeight = frame.shape[0]
        msg.stSrcImageInfo.nWidth = frame.shape[1]
        msg.stSrcImageInfo.byImageData = frame.tobytes()
        msg.stSrcImageInfo.uDeviceIndex = deviceIndex
        msg.stSrcImageInfo.strJsonData = extend

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _create_pb_get_source_msg():
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_PROJECT_SOURCE
        msg_buff = msg.SerializeToString()
        return msg_buff

    @staticmethod
    def _CreatePBChangeGameStateMsg():
        gameState = IO_SERVICE_CONTEXT['game_state']

        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_CHANGE_GAME_STATE
        if gameState == GAME_STATE_NONE:
            msg.stChangeGameState.eGameState = common_pb2.PB_STATE_NONE
        elif gameState == GAME_STATE_UI:
            msg.stChangeGameState.eGameState = common_pb2.PB_STATE_UI
        elif gameState == GAME_STATE_START:
            msg.stChangeGameState.eGameState = common_pb2.PB_STATE_START
        elif gameState == GAME_STATE_OVER:
            msg.stChangeGameState.eGameState = common_pb2.PB_STATE_OVER
        elif gameState == GAME_STATE_MATCH_WIN:
            msg.stChangeGameState.eGameState = common_pb2.PB_STATE_MATCH_WIN
        else:
            LOG.warning('Unhandled GameState[%s]', gameState)
            return

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _CreateAIServiceStateMsg(serviceState):
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_AI_SERVICE_STATE
        msg_data['source_server_id'] = IO_SERVICE_CONTEXT['source_server_id']
        msg_data['ai_service_state'] = serviceState
        return msg_data

    @staticmethod
    def _CreateIMTrainStateMsg(progress):
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_AI_TRAIN_SCHEDULE
        msg_data['source_server_id'] = IO_SERVICE_CONTEXT['source_server_id']
        msg_data['train_schedule'] = progress
        return msg_data

    @staticmethod
    def _CreatePBPauseAgentMsg():
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_PAUSE_AGENT

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _CreatePBRestoreAgentMsg():
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_RESTORE_AGENT

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _CreatePBRestartMsg():
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_RESTART

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _CreateRestartResultMsg(result):
        msg_data = dict()
        msg_data['msg_id'] = MSG_ID_RESTART_RESULT
        msg_data['restart_result'] = result
        return msg_data

    @staticmethod
    def _CreatePBNewTaskMsg():
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_NEW_TASK

        msg.stNewTask.strTaskID = IO_SERVICE_CONTEXT['task_id']

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _CreatePBTestIDMsg(testID, gameID, gameVersion):
        msg = common_pb2.tagMessage()
        # Fill the message
        msg.eMsgID = common_pb2.MSG_TEST_ID

        msg.stTestID.strTestID = testID
        msg.stTestID.nGameID = gameID
        msg.stTestID.strGameVersion = gameVersion

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    @staticmethod
    def _SinglePointOp(px, py, contact, action_id, during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['px'] = px
        msg_data['py'] = py
        msg_data['contact'] = contact
        msg_data['action_id'] = action_id
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data

    @staticmethod
    def _DoublePointOp(start_x, start_y, end_x, end_y, contact, action_id,
                       during_time=0, wait_time=0):
        msg_data = dict()
        msg_data['start_x'] = start_x
        msg_data['start_y'] = start_y
        msg_data['end_x'] = end_x
        msg_data['end_y'] = end_y
        msg_data['contact'] = contact
        msg_data['action_id'] = action_id
        if during_time > 0:
            msg_data['during_time'] = during_time
        if wait_time > 0:
            msg_data['wait_time'] = wait_time
        return msg_data

    @staticmethod
    def _ForkResetAction():
        msg_data = dict()
        msg_data['action_id'] = ACTION_ID_RESET
        return msg_data
