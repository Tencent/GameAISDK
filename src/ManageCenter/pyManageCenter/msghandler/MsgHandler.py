# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import numpy as np

from protocol import common_pb2
from common.Define import *

LOG = logging.getLogger('ManageCenter')


class MsgHandler(object):
    """
    MC MsgHandler implementation for handling all messages
    """
    def __init__(self, commMgr, gameMgr, serviceMgr, resultMgr, resultType, runType):
        self.__resultType = resultType
        self.__runType = runType
        self.__commMgr = commMgr
        self.__gameMgr = gameMgr
        self.__serviceMgr = serviceMgr
        self.__resultMgr = resultMgr
        self.__msgDict = {}

    def Initialize(self):
        """
        Initialize the message handler dictionary(map)
        :return: True
        """
        # Initialize the message handler dictionary(map)
        self._RegisterMsgHandler(common_pb2.MSG_SRC_IMAGE_INFO, self._OnFrameMsg)
        self._RegisterMsgHandler(common_pb2.MSG_UI_ACTION, self._OnUIAction)
        self._RegisterMsgHandler(common_pb2.MSG_AI_ACTION, self._OnAIAction)
        self._RegisterMsgHandler(common_pb2.MSG_SERVICE_REGISTER, self._OnServiceRegister)
        self._RegisterMsgHandler(common_pb2.MSG_TASK_REPORT, self._OnTaskReport)
        self._RegisterMsgHandler(common_pb2.MSG_CHANGE_GAME_STATE, self._OnChangeGameState)
        self._RegisterMsgHandler(common_pb2.MSG_PAUSE_AGENT, self._OnPauseAgent)
        self._RegisterMsgHandler(common_pb2.MSG_RESTORE_AGENT, self._OnRestoreAgent)
        self._RegisterMsgHandler(common_pb2.MSG_RESTART, self._OnRestart)
        self._RegisterMsgHandler(common_pb2.MSG_AGENT_STATE, self._OnAgentState)
        self._RegisterMsgHandler(common_pb2.MSG_NEW_TASK, self._OnNewTask)
        self._RegisterMsgHandler(common_pb2.MSG_TEST_ID, self._OnTestID)
        self._RegisterMsgHandler(common_pb2.MSG_IM_TRAIN_STATE, self._OnIMTrainState)
        return True

    def Update(self):
        """
        Update the msg handler, handle the msgs from IO, agentai, GameReg, UI
        :return:
        """
        # Recv the message
        msgBuffList = self.__commMgr.RecvMsg()

        # if recv nothing, then exit
        if len(msgBuffList) == 0:
            return

        # parse the message and call handler function
        for (addr, msgBuff) in msgBuffList:
            # Deserialize message
            msg = self._ParseMsg(msgBuff)
            # Call message handler function
            handleFunc = self.__msgDict.get(msg.eMsgID)
            if handleFunc is not None:
                handleFunc(msg, addr)
            else:
                LOG.warning('Unhandled MsgID[{0}]'.format(msg.eMsgID))

    def _RegisterMsgHandler(self, msgID, msgFuncHandler):
        self.__msgDict[msgID] = msgFuncHandler

    def _ParseMsg(self, msgBuff):
        msg = common_pb2.tagMessage()
        msg.ParseFromString(msgBuff)
        return msg

    def _CreateSrcImgMsg(self, frameSeq, frame, gameData=None, deviceIndex=0):
        msg = common_pb2.tagMessage()

        # Fill the message
        msg.eMsgID = common_pb2.MSG_SRC_IMAGE_INFO
        msg.stSrcImageInfo.uFrameSeq = frameSeq
        msg.stSrcImageInfo.nHeight = frame.shape[0]
        msg.stSrcImageInfo.nWidth = frame.shape[1]
        msg.stSrcImageInfo.byImageData = frame.tobytes()
        msg.stSrcImageInfo.uDeviceIndex = deviceIndex
        if gameData is None:
            msg.stSrcImageInfo.strJsonData = 'null'
        else:
            msg.stSrcImageInfo.strJsonData = gameData

        # Serialize the message
        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateUIAPIStateMsg(self, uiAPIState, frameSeq, uiImage, screenOri, gameState=None):
        msg = common_pb2.tagMessage()

        msg.eMsgID = common_pb2.MSG_UI_STATE_IMG
        msg.stUIAPIState.eUIState = uiAPIState

        msg.stUIAPIState.stUIImage.uFrameSeq = frameSeq
        msg.stUIAPIState.stUIImage.nHeight = uiImage.shape[0]
        msg.stUIAPIState.stUIImage.nWidth = uiImage.shape[1]
        msg.stUIAPIState.stUIImage.byImageData = uiImage.tobytes()

        if gameState is None:
            msg.stUIAPIState.eGameState = common_pb2.PB_STATE_NONE
        else:
            msg.stUIAPIState.eGameState = gameState

        if screenOri == UI_SCREEN_ORI_LANDSCAPE:
            msg.stUIAPIState.eScreenOri = common_pb2.PB_SCREEN_ORI_LANDSCAPE
        else:
            msg.stUIAPIState.eScreenOri = common_pb2.PB_SCREEN_ORI_PORTRAIT

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateServiceRegisterMsg(self, regType):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_SERVICE_REGISTER
        if regType == SERVICE_REGISTER:
            msg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_REGISTER
        elif regType == SERVICE_UNREGISTER:
            msg.stServiceRegister.eRegisterType = common_pb2.PB_SERVICE_UNREGISTER
        msg.stServiceRegister.eServiceType = common_pb2.PB_SERVICE_TYPE_MC

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateTaskReportMsg(self, taskStatus):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_TASK_REPORT
        if taskStatus == TASK_STATUS_INIT_SUCCESS:
            msg.stTaskReport.eTaskStatus = common_pb2.PB_TASK_INIT_SUCCESS
        elif taskStatus == TASK_STATUS_INIT_FAILURE:
            msg.stTaskReport.eTaskStatus = common_pb2.PB_TASK_INIT_FAILURE

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateAIServiceStateMsg(self, serviceStateResult):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_SERVICE_STATE
        msg.stServiceState.nServiceState = serviceStateResult

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateRestartResultMsg(self, result):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_RESTART_RESULT
        if result == 0:
            msg.stRestartResult.eRestartResult = common_pb2.PB_RESTART_RESULT_SUCCESS
        else:
            msg.stRestartResult.eRestartResult = common_pb2.PB_RESTART_RESULT_FAILURE

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateUIGameStartMsg(self):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_UI_GAME_START

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _CreateUIGameOverMsg(self):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_UI_GAME_OVER

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _OnFrameMsg(self, msg, addr):
        frameSeq = msg.stSrcImageInfo.uFrameSeq
        height = msg.stSrcImageInfo.nHeight
        width = msg.stSrcImageInfo.nWidth

        imgdata = np.fromstring(msg.stSrcImageInfo.byImageData, np.uint8)
        shape = (height, width, 3)
        gameFrame = np.reshape(imgdata, shape)
        LOG.debug('recv frame data, frameIndex={}'.format(frameSeq))
        jsonData = msg.stSrcImageInfo.strJsonData
        LOG.debug('recv json data={}'.format(jsonData))

        self.__gameMgr.SetGameFrame(gameFrame, frameSeq)
        self.__gameMgr.SetGameData(jsonData, frameSeq)
        self.__resultMgr.SavingVideo(gameFrame, frameSeq, self.__gameMgr.GameStarted())

    def _OnAIAction(self, msg, addr):
        ret, _ = self.__serviceMgr.IsServiceAlreadyRegistered(addr, SERVICE_TYPE_AGENT)
        if not ret:
            LOG.warning('Recv AIAction from unregistered AI addr[{}], ignore!'.format(addr))
            return

        frameSeq = msg.stAIAction.nFrameSeq
        LOG.debug('recv action data, frameIndex={}'.format(frameSeq))

        if not self.__serviceMgr.IsTaskReady():
            LOG.debug('Task not ready')
            return

        msg = self.__serviceMgr.PerformAIActionStrategy(addr, msg)

        actionBuff = msg.stAIAction.byAIActionBuff
        self.__resultMgr.SavingActionLog(actionBuff, frameSeq)

        msgBuff = msg.SerializeToString()
        LOG.debug('send action data, frameIndex={}'.format(frameSeq))
        self.__commMgr.SendMsgToIOService(msgBuff)

    def _OnUIAction(self, msg, addr):
        ret, _ = self.__serviceMgr.IsServiceAlreadyRegistered(addr, SERVICE_TYPE_UI)
        if not ret:
            LOG.warning('Recv UIAction from unregistered UI addr[{}], ignore!'.format(addr))
            return

        gameState = msg.stUIAction.eGameState
        gameStarted = self.__gameMgr.GameStarted()
        if gameState == common_pb2.PB_STATE_START:
            self.__gameMgr.SetGameState(GAME_STATE_START)
            LOG.info('GameState Start')
            self.SendUIGameStartMsgToAI()
        elif gameState == common_pb2.PB_STATE_OVER:
            if gameStarted:
                self.__gameMgr.SetGameState(GAME_STATE_OVER)
                LOG.info('GameState Over')
                self.SendUIGameOverMsgToAI()
            else:
                LOG.warning('Wrong recv PB_STATE_OVER while GameState is not started, ignore!')
        elif gameState == common_pb2.PB_STATE_MATCH_WIN:
            if gameStarted:
                self.__gameMgr.SetGameState(GAME_STATE_MATCH_WIN)
                LOG.info('GameState Win')
                self.SendUIGameOverMsgToAI()
            else:
                LOG.warning('Wrong recv PB_STATE_MATCH_WIN while GameState is not started, ignore!')
        elif gameState == common_pb2.PB_STATE_UI:
            if gameStarted:
                LOG.info('Recv PB_STATE_UI while GameState is started!')
                msg.stUIAction.eGameState = common_pb2.PB_STATE_START
            else:
                self.__gameMgr.SetGameState(GAME_STATE_UI)
        elif gameState == common_pb2.PB_STATE_NONE:
            if gameStarted:
                LOG.info('Recv PB_STATE_NONE while GameState is started!')
                msg.stUIAction.eGameState = common_pb2.PB_STATE_START
            else:
                self.__gameMgr.SetGameState(GAME_STATE_NONE)
        else:
            LOG.warning('Unhandled GameState[{0}]'.format(gameState))

        LOG.info('GameState:{} [1:UI 2:START 3:OVER 4:MATCH_WIN'
                 ' 0:NONE(Default)]'.format(self.__gameMgr.GetGameState()))

        msg = self.__serviceMgr.PerformUIActionStrategy(addr, msg)

        msgBuff = msg.SerializeToString()
        self.__commMgr.SendMsgToIOService(msgBuff)

    def _OnServiceRegister(self, msg, addr):
        regType = msg.stServiceRegister.eRegisterType
        serviceType = msg.stServiceRegister.eServiceType
        LOG.info('Recv ServiceRegister from {2}, regType[{0}],'
                 ' serviceType[{1}]'.format(regType, serviceType, addr))

        if regType == common_pb2.PB_SERVICE_REGISTER:
            if serviceType == common_pb2.PB_SERVICE_TYPE_UI:
                self.__serviceMgr.AddService(SERVICE_TYPE_UI, addr)
            elif serviceType == common_pb2.PB_SERVICE_TYPE_AI:
                self.__serviceMgr.AddService(SERVICE_TYPE_AGENT, addr)
            elif serviceType == common_pb2.PB_SERVICE_TYPE_REG:
                self.__serviceMgr.AddService(SERVICE_TYPE_REG, addr)
        elif regType == common_pb2.PB_SERVICE_UNREGISTER:
            if serviceType == common_pb2.PB_SERVICE_TYPE_UI:
                self.__serviceMgr.DelService(SERVICE_TYPE_UI, addr)
            elif serviceType == common_pb2.PB_SERVICE_TYPE_AI:
                self.__serviceMgr.DelService(SERVICE_TYPE_AGENT, addr)
            elif serviceType == common_pb2.PB_SERVICE_TYPE_REG:
                self.__serviceMgr.DelService(SERVICE_TYPE_REG, addr)

        if self.__serviceMgr.IsServiceReady():
            LOG.info('All Services already Registered, now register')
            self.SendServiceRegisterMsgToIO(SERVICE_REGISTER)

    def _OnTaskReport(self, msg, addr):
        ret, _ = self.__serviceMgr.IsServiceAlreadyRegistered(addr)
        if not ret:
            LOG.warning('Recv TaskReport from unregistered Service addr[{}], ignore!'.format(addr))
            return

        taskStatus = msg.stTaskReport.eTaskStatus

        if taskStatus == common_pb2.PB_TASK_INIT_SUCCESS:
            self.__serviceMgr.ChangeServiceStatus(addr, TASK_STATUS_INIT_SUCCESS)
            if self.__serviceMgr.IsTaskReady():
                LOG.info('All Services task status ready, now report')
                self.SendTaskReportMsgToIO(TASK_STATUS_INIT_SUCCESS)
        else:
            LOG.warning('Service[{}] init task failure, now report'.format(addr))
            self.SendTaskReportMsgToIO(TASK_STATUS_INIT_FAILURE)

    def _OnChangeGameState(self, msg, addr):
        if self.__runType in [RUN_TYPE_UI_AI, RUN_TYPE_UI]:
            LOG.warning('Reject Client Change GameState in UI+AI or UI mode')
            return

        gameState = msg.stChangeGameState.eGameState
        if gameState == common_pb2.PB_STATE_START:
            self.__gameMgr.SetGameState(GAME_STATE_START)
            self.SendUIGameStartMsgToAI()
        elif gameState == common_pb2.PB_STATE_OVER:
            self.__gameMgr.SetGameState(GAME_STATE_OVER)
            self.SendUIGameOverMsgToAI()
        elif gameState == common_pb2.PB_STATE_MATCH_WIN:
            self.__gameMgr.SetGameState(GAME_STATE_MATCH_WIN)
            self.SendUIGameOverMsgToAI()
        elif gameState == common_pb2.PB_STATE_UI:
            self.__gameMgr.SetGameState(GAME_STATE_UI)
        elif gameState == common_pb2.PB_STATE_NONE:
            self.__gameMgr.SetGameState(GAME_STATE_NONE)
        else:
            LOG.warning('Unhandled GameState[{0}]'.format(gameState))

        LOG.info('Client Change GameState:{} [1:UI 2:START 3:OVER 4:MATCH_WIN'
                 ' 0:NONE(Default)]'.format(self.__gameMgr.GetGameState()))

    def _OnPauseAgent(self, msg, addr):
        LOG.info('Recv MSG_PAUSE_AGENT msg')
        self.__serviceMgr.PauseAgent()

    def _OnRestoreAgent(self, msg, addr):
        LOG.info('Recv MSG_RESTORE_AGENT msg')
        self.__serviceMgr.RestoreAgent()

    def _OnRestart(self, msg, addr):
        LOG.info('Recv MSG_RESTART msg')
        self.__serviceMgr.Reset()
        self.__gameMgr.Reset()
        if self.__serviceMgr.RestartService() == 0:
            LOG.info('Restart Service SUCCESS')
            self.SendRestartResultToIO(0)
        else:
            LOG.error('Restart Service FAILURE')
            self.SendRestartResultToIO(1)

    def _OnAgentState(self, msg, addr):
        agentState = msg.stAgentState.eAgentState
        agentStateStr = msg.stAgentState.strAgentState
        LOG.info('Recv MSG_AGENT_STATE msg, AgentState:{0}'
                 '/{1}'.format(agentState, agentStateStr))

        # if self.__resultType == RESULT_TYPE_AI:
        #     if agentState == AGENT_STATE_PLAYING:
        #         self.__resultMgr.RoundStart()
        #     elif agentState == AGENT_STATE_OVER:
        #         self.__resultMgr.RoundOver()

        msgBuff = msg.SerializeToString()
        self.__commMgr.SendMsgToIOService(msgBuff)

    def _OnNewTask(self, msg, addr):
        strTaskID = msg.stNewTask.strTaskID

        LOG.info('Recv MSG_NEW_TASK msg, taskID[{0}]'.format(strTaskID))

        self.__resultMgr.UpdateContext(taskID=strTaskID)

    def _OnTestID(self, msg, addr):
        testID = msg.stTestID.strTestID
        nGameID = msg.stTestID.nGameID
        strGameVersion = msg.stTestID.strGameVersion

        LOG.info('Recv MSG_TEST_ID msg, testID[{0}] gameID[{1}] '
                 'gameVersion[{2}]'.format(testID, nGameID, strGameVersion))

        self.__resultMgr.UpdateContext(testID=testID, gameID=nGameID, gameVersion=strGameVersion)

    def _OnIMTrainState(self, msg, addr):
        progress = msg.stIMTrainState.nProgress
        LOG.info('Recv MSG_IM_TRAIN_STATE msg, progress: {}'.format(progress))

        msgBuff = msg.SerializeToString()
        self.__commMgr.SendMsgToIOService(msgBuff)

    def SendServiceRegisterMsgToIO(self, regType):
        """
        Send service register/unregister to IO
        :param regType: register/unregister
        :return:
        """
        msgBuff = self._CreateServiceRegisterMsg(regType)
        self.__commMgr.SendMsgToIOService(msgBuff)

    def SendTaskReportMsgToIO(self, taskStatus):
        """
        Send task status report to IO
        :param taskStatus: task status
        :return:
        """
        msgBuff = self._CreateTaskReportMsg(taskStatus)
        self.__commMgr.SendMsgToIOService(msgBuff)

    def SendGameFrameMsgTo(self, addr, gameFrame, gameData, frameSeq):
        """
        Send GameFrame To addr(service)
        :param addr: the addr of the service
        :param gameFrame: GameFrame
        :param gameData: GameData extend
        :param frameSeq: FrameSeq
        :return:
        """
        msgBuff = self._CreateSrcImgMsg(frameSeq, gameFrame, gameData)
        LOG.debug('send frame data, frameIndex={1} to addr[{0}]'.format(addr, frameSeq))
        self.__commMgr.SendTo(addr, msgBuff)

    def SendUIAPIStateMsgTo(self, addr, gameFrame, frameSeq, stucked=False):
        """
        Send UIAPI State To addr(service)
        :param addr: the addr of the service
        :param gameFrame: GameFrame
        :param frameSeq: FrameSeq
        :param stucked: whether the UI stucked
        :return:
        """
        if stucked:
            uiAPIState = common_pb2.PB_UI_STATE_STUCK
        else:
            uiAPIState = common_pb2.PB_UI_STATE_NORMAL

        gameState = self.__gameMgr.GetGameState()
        screenOri = UI_SCREEN_ORI_LANDSCAPE
        if gameFrame is None:
            return

        LOG.debug('Send UIAPIState to [{0}], frame_seq[{1}]'.format(addr, frameSeq))

        msgBuff = self._CreateUIAPIStateMsg(uiAPIState, frameSeq, gameFrame, screenOri, gameState)
        self.__commMgr.SendTo(addr, msgBuff)

    def SendAIServiceStateToIO(self, serviceStateResult):
        """
        Send Service monitor State To IO
        :param serviceStateResult: Service monitor State
        :return:
        """
        msgBuff = self._CreateAIServiceStateMsg(serviceStateResult)
        LOG.info('Send AIServiceState to IO, [{}]'.format(serviceStateResult))
        self.__commMgr.SendMsgToIOService(msgBuff)

    def SendRestartResultToIO(self, result):
        """
        Send Restart service result To IO
        :param result:
        :return:
        """
        msgBuff = self._CreateRestartResultMsg(result)
        self.__commMgr.SendMsgToIOService(msgBuff)

    def SendUIGameStartMsgToAI(self):
        """
        Send UIGameStart To agentai
        :return:
        """
        msgBuff = self._CreateUIGameStartMsg()

        addrList = self.__serviceMgr.GetAllServiceAddr(serviceType=SERVICE_TYPE_AGENT)
        for addr in addrList:
            LOG.info('Send UIGameStart to AI[{}]'.format(addr))
            self.__commMgr.SendTo(addr, msgBuff)

    def SendUIGameOverMsgToAI(self):
        """
        Send UIGameOver To agentai
        :return:
        """
        msgBuff = self._CreateUIGameOverMsg()

        addrList = self.__serviceMgr.GetAllServiceAddr(serviceType=SERVICE_TYPE_AGENT)
        for addr in addrList:
            LOG.info('Send UIGameOver to AI[{}]'.format(addr))
            self.__commMgr.SendTo(addr, msgBuff)
