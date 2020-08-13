# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

"""
Module: manage message between Agent and GameRecognize.
send message type from Agent to GameRecognize  in
[MSG_SEND_GROUP_ID,
MSG_SEND_TASK_FLAG,
MSG_SEND_ADD_TASK,
MSG_SEND_DEL_TASK,
MSG_SEND_CHG_TASK,
MSG_SEND_TASK_CONF]

recv message from GameRecognize to Agent contained the recognize results and the processed image.

all messages are packed with PB(Google Protocol Buff)
"""

import os
import sys
import logging
import numpy as np

if sys.version_info < (3, 0):
    import ConfigParser as ConfigParser
else:
    import configparser as ConfigParser

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__ + "/protocol")

import tbus
from .protocol import common_pb2
from .protocol import gameregProtoc_pb2


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

LOG = logging.getLogger('agent')


class MsgMgr(object):
    """
    message manager implement
    """
    def __init__(self, cfgPath='../cfg/bus.ini', initParamFile='../cfg/param.file', index=1):
        self.__selfAddr = None
        self.__gameRegAddr = None
        self.__cfgPath = cfgPath
        self.__initParamFile = initParamFile
        self.__index = index
        self.__serialMsgHandle = dict()
        self.__serialRegerHandle = dict()
        self.__unSeiralRegerHandle = dict()

    def Initialize(self, selfAddr=None):
        """
        Initialize message manager, parse tbus configure file and initialize tbus
        return: True or Flase
        """
        if os.path.exists(self.__cfgPath):
            self._Register()

            config = ConfigParser.ConfigParser(strict=False)
            config.read(self.__cfgPath)
            gameRegAddr = "GameReg" + str(self.__index) + "Addr"
            strgameRegAddr = config.get('BusConf', gameRegAddr)

            if selfAddr is None:
                AgentAddr = "Agent" + str(self.__index) + "Addr"
                strselfAddr = config.get('BusConf', AgentAddr)
            else:
                strselfAddr = config.get('BusConf', selfAddr)
            self.__gameRegAddr = tbus.GetAddress(strgameRegAddr)
            self.__selfAddr = tbus.GetAddress(strselfAddr)
            LOG.info("gamereg addr is {0}, self addr is {1}" \
                     .format(self.__gameRegAddr, self.__selfAddr))
            ret = tbus.Init(self.__selfAddr, self.__cfgPath)
            if ret != 0:
                LOG.error('tbus init failed with return code[{0}]'.format(ret))
                return False

            return True

        else:
            LOG.error('tbus config file not exist in {0}'.format(self.__cfgPath))
            return False

    def ProcMsg(self, msgID, msgValue):
        """
        Process message: create message and send to GameReg
        :param msgID: message ID which should be in [MSG_SEND_GROUP_ID, MSG_SEND_TASK_FLAG,
                      MSG_SEND_ADD_TASK,MSG_SEND_DEL_TASK, MSG_SEND_CHG_TASK, MSG_SEND_TASK_CONF]
        :param msgValue: value of message
        :return: True or False
        """
        outBuff = self._CreateMsg(msgID, msgValue)

        if outBuff is None:
            LOG.error('create msg failed')
            return False

        return self._Send(outBuff)

    def ProcSrcImgMsg(self, srcImgDict):
        """
        ProcSrcImgMsg: create message and send to GameReg
        :param srcImgDict: image information saved with dictinary format,
                           keywords is 'frameSeq', 'width', 'height''image','deviceIndex'
        :return: True or False
        """
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_SRC_IMAGE_INFO

        stSrcImageInfo = msg.stSrcImageInfo
        stSrcImageInfo.uFrameSeq = srcImgDict['frameSeq']
        stSrcImageInfo.nWidth = srcImgDict['width']
        stSrcImageInfo.nHeight = srcImgDict['height']
        stSrcImageInfo.byImageData = srcImgDict['image'].tobytes()
        stSrcImageInfo.uDeviceIndex = srcImgDict['deviceIndex']

        msgBuff = msg.SerializeToString()

        if msgBuff is None:
            LOG.error('create msg failed')
            return False

        return self._Send(msgBuff)

    def Recv(self):
        """
        Recv: receieve message from GameReg,
        the value is the result of imageReg and the processed image
        :return: True or False
        """
        msgBuffRet = None
        msgBuff = tbus.RecvFrom(self.__gameRegAddr)
        while msgBuff is not None:
            msgBuffRet = msgBuff
            msgBuff = tbus.RecvFrom(self.__gameRegAddr)

        if msgBuffRet is not None:
            # msg = msgpack.unpackb(msgBuffRet, object_hook=mn.decode, encoding='utf-8')
            msg = self._UnSerialResultMsg(msgBuffRet)

            frameSeq = msg['value'].get('frameSeq')
            LOG.debug('recv frame data, frameIndex={0}'.format(frameSeq))
            return msg

        else:
            return None

    def Release(self):
        """
        tbus exit
        :return: None
        """
        LOG.info('tbus exit...')
        tbus.Exit(self.__selfAddr)

    def _CreateMsg(self, msgID, msgValue):
        msgDic = dict()
        msgDic['msgID'] = msgID
        msgDic['value'] = msgValue
        # outBuff = msgpack.packb(msgDic, use_bin_type=True)

        outBuff = self._SerialSendMsg(msgDic)

        return outBuff

    def _Send(self, outBuff):
        ret = tbus.SendTo(self.__gameRegAddr, outBuff)
        if ret != 0:
            LOG.error('TBus Send To UI Anuto Addr return code[{0}]'.format(ret))
            return False

        return True

    def _Register(self):
        """
        registe message hander
        serial message: MSG_SEND_GROUP_ID,MSG_SEND_ADD_TASK,
                        MSG_SEND_CHG_TASK, MSG_SEND_TASK_FLAG,
                        MSG_SEND_DEL_TASK, MSG_SEND_TASK_CONF,
                        MSG_REGER_STUCK_TYPE,MSG_REGER_FIXOBJ_TYPE,MSG_REGER_PIX_TYPE,
                        MSG_REGER_DEFORM_TYPE,MSG_REGER_NUMBER_TYPE,
                        MSG_REGER_FIXBLOOD_TYPE,MSG_REGER_KING_GLORY_BOOD_TYPE,
                        MSG_REGER_MAPREG_TYPE, MSG_REGER_MAPDIRECTIONREG_TYPE,
                        MSG_REGER_MULTCOLORVAR_TYPE, MSG_REGER_SHOOTGAMEBLOOD_TYPE,
                        MSG_REGER_SHOOTGAMEHURT_TYPE

        unserial message:gameregProtoc_pb2.TYPE_STUCKREG, gameregProtoc_pb2.TYPE_FIXOBJREG,
                         gameregProtoc_pb2.TYPE_PIXREG, gameregProtoc_pb2.TYPE_DEFORMOBJ,
                         gameregProtoc_pb2.TYPE_NUMBER, gameregProtoc_pb2.TYPE_FIXBLOOD,
                         gameregProtoc_pb2.TYPE_KINGGLORYBLOOD,gameregProtoc_pb2.TYPE_MAPREG,
                         gameregProtoc_pb2.TYPE_MAPDIRECTIONREG,gameregProtoc_pb2.TYPE_MULTCOLORVAR,
                         gameregProtoc_pb2.TYPE_SHOOTBLOOD, gameregProtoc_pb2.TYPE_SHOOTHURT
        :return: None
        """
        self.__serialMsgHandle[MSG_SEND_GROUP_ID] = self._SerialTask
        self.__serialMsgHandle[MSG_SEND_ADD_TASK] = self._SerialAddTask
        self.__serialMsgHandle[MSG_SEND_CHG_TASK] = self._SerialChgTask
        self.__serialMsgHandle[MSG_SEND_TASK_FLAG] = self._SerialFlagTask
        self.__serialMsgHandle[MSG_SEND_DEL_TASK] = self._SerialDelTask
        self.__serialMsgHandle[MSG_SEND_TASK_CONF] = self._SerialConfTask

        self.__serialRegerHandle[MSG_REGER_STUCK_TYPE] = self._SerialStuckReg
        self.__serialRegerHandle[MSG_REGER_FIXOBJ_TYPE] = self._SerialFixObjReg
        self.__serialRegerHandle[MSG_REGER_PIX_TYPE] = self._SerialPixReg
        self.__serialRegerHandle[MSG_REGER_DEFORM_TYPE] = self._SerialDeformReg
        self.__serialRegerHandle[MSG_REGER_NUMBER_TYPE] = self._SerialNumberReg
        self.__serialRegerHandle[MSG_REGER_FIXBLOOD_TYPE] = self._SerialFixBloodReg
        self.__serialRegerHandle[MSG_REGER_KING_GLORY_BOOD_TYPE] =\
            self._SerialKingGloryBlood
        self.__serialRegerHandle[MSG_REGER_MAPREG_TYPE] = self._SerialMapReg
        self.__serialRegerHandle[MSG_REGER_MAPDIRECTIONREG_TYPE] = \
            self._SerialMapDirectionReg
        self.__serialRegerHandle[MSG_REGER_MULTCOLORVAR_TYPE] = \
            self._SerialMultColorVar
        self.__serialRegerHandle[MSG_REGER_SHOOTGAMEBLOOD_TYPE] = \
            self._SerialShootGameBlood
        self.__serialRegerHandle[MSG_REGER_SHOOTGAMEHURT_TYPE] = \
            self._SerialShootGameHurt

        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_STUCKREG] = \
            self._UnSerialStuckRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_FIXOBJREG] = \
            self._UnSerialFixObjRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_PIXREG] = \
            self._UnSerialPixRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_DEFORMOBJ] = \
            self._UnSerialDeformRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_NUMBER] = \
            self._UnSerialNumberRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_FIXBLOOD] = \
            self._UnSerialFixBloodRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_KINGGLORYBLOOD] = \
            self._UnSerialKingGloryBloodResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_MAPREG] = \
            self._UnSerialMapRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_MAPDIRECTIONREG] = \
            self._UnSerialMapDirectionRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_MULTCOLORVAR] = \
            self._UnSerialMultColorVar
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_SHOOTBLOOD] = \
            self._UnSerialShootGameBloodRegResult
        self.__unSeiralRegerHandle[gameregProtoc_pb2.TYPE_SHOOTHURT] = \
            self._UnSerialShootGameHurtRegResult

    def _SerialSendMsg(self, msgDic):
        msg = common_pb2.tagMessage()
        msg.eMsgID = common_pb2.MSG_GAMEREG_INFO
        msgAgent = msg.stPBAgentMsg
        msgAgent.eAgentMsgID = self._GetValueFromDict(msgDic, 'msgID')

        self.__serialMsgHandle[msgAgent.eAgentMsgID](
            msgAgent, self._GetValueFromDict(msgDic, 'value')
        )

        msgBuff = msg.SerializeToString()
        return msgBuff

    def _SerialTask(self, msg, msgValue):
        value = msg.stPBAgentTaskValue
        value.uGroupID = self._GetValueFromDict(msgValue, 'groupID')
        for taskVal in self._GetValueFromDict(msgValue, 'task'):
            taskPB = value.stPBAgentTaskTsks.add()
            self.__serialRegerHandle[self._GetValueFromDict(taskVal, 'type')](taskPB, taskVal)

    def _SerialChgTask(self, msg, msgValue):
        value = msg.stPBAgentTaskValue
        value.uGroupID = 1
        for taskVal in msgValue:
            taskPB = value.stPBAgentTaskTsks.add()
            self.__serialRegerHandle[self._GetValueFromDict(taskVal, 'type')](taskPB, taskVal)

    def _SerialAddTask(self, msg, msgValue):
        value = msg.stPBAgentTaskValue
        value.uGroupID = 1
        for taskVal in msgValue:
            taskPB = value.stPBAgentTaskTsks.add()
            self.__serialRegerHandle[self._GetValueFromDict(taskVal, 'type')](taskPB, taskVal)

    def _SerialFlagTask(self, msg, msgValue):
        for taskID in msgValue:
            value = msg.stPBTaskFlagMaps.add()
            value.nTaskID = int(taskID)
            value.bFlag = msgValue[taskID]

    def _SerialDelTask(self, msg, msgValue):
        for key in msgValue:
            msg.nDelTaskIDs.append(key)

    def _SerialConfTask(self, msg, msgValue):
        for filename in msgValue:
            if filename is not None:
                msg.strConfFileName.append(filename)

    def _SerialMapReg(self, taskPB, taskVal):
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_MAPREG
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            mapElePB = taskPB.stPBAgentTaskElements.add()

            mapEleRect = mapElePB.stPBRect
            mapEleRect.nX = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'x')
            mapEleRect.nY = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'y')
            mapEleRect.nW = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'w')
            mapEleRect.nH = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'h')

            mapElePB.strMyLocCondition = self._GetValueFromDict(element, 'myLocCondition')
            mapElePB.strFriendsCondition = self._GetValueFromDict(element, 'friendsLocCondition')
            mapElePB.strViewLocCondition = self._GetValueFromDict(element, 'viewLocCondition')
            mapElePB.strMapPath = self._GetValueFromDict(element, 'mapTempPath')
            mapElePB.strMaskPath = element.get('mapMaskPath') or str()
            mapElePB.nMaxPointNum = self._GetValueFromDict(element, 'maxPointNum')
            mapElePB.nFilterSize = self._GetValueFromDict(element, 'filterSize')

    def _SerialMapDirectionReg(self, taskPB, taskVal):
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_MAPDIRECTIONREG
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            mapDirElePB = taskPB.stPBAgentTaskElements.add()

            mapDirRect = mapDirElePB.stPBRect
            mapDirRect.nX = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'x')
            mapDirRect.nY = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'y')
            mapDirRect.nW = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'w')
            mapDirRect.nH = self._GetValueFromDict(self._GetValueFromDict(element, 'ROI'), 'h')

            mapDirElePB.strMyLocCondition = self._GetValueFromDict(element, 'myLocCondition')
            mapDirElePB.strViewLocCondition = self._GetValueFromDict(element, 'viewLocCondition')
            mapDirElePB.strMaskPath = element.get('mapMaskPath') or str()
            mapDirElePB.nMaxPointNum = self._GetValueFromDict(element, 'maxPointNum')
            mapDirElePB.nFilterSize = self._GetValueFromDict(element, 'filterSize')
            mapDirElePB.nDilateSize = self._GetValueFromDict(element, 'dilateSize')
            mapDirElePB.nErodeSize = self._GetValueFromDict(element, 'erodeSize')
            mapDirElePB.nRegionSize = self._GetValueFromDict(element, 'regionSize')

    def _SerialMultColorVar(self, taskPB, taskVal):
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_MULTCOLORVAR
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            elementPB.strImgFilePath = self._GetValueFromDict(element, 'imageFilePath')

    def _SerialShootGameBlood(self, taskPB, taskVal):
        """
        ShootGameBlood, this recongnizer method only used by ShootGame
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_SHOOTBLOOD
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.nFilterSize = self._GetValueFromDict(element, 'filterSize')
            elementPB.nBloodLength = self._GetValueFromDict(element, 'bloodLength')
            elementPB.nMaxPointNum = self._GetValueFromDict(element, 'maxPointNum')
            elementPB.fMinScale = self._GetValueFromDict(element, 'minScale')
            elementPB.fMaxScale = self._GetValueFromDict(element, 'maxScale')
            elementPB.nScaleLevel = self._GetValueFromDict(element, 'scaleLevel')

            templates = elementPB.stPBTemplates
            for templ in self._GetValueFromDict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._SerialTemplate(template, templ)

    def _SerialShootGameHurt(self, taskPB, taskVal):
        """
        ShootGameHurt, this recongnizer method only used by ShootGame
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_SHOOTHURT
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.fThreshold = self._GetValueFromDict(element, 'threshold')

    def _SerialKingGloryBlood(self, taskPB, taskVal):
        """
        KingGloryBlood, this recongnizer method only used by KingGlory
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_KINGGLORYBLOOD
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            KGElePB = taskPB.stPBAgentTaskElements.add()

            KGRect = KGElePB.stPBRect
            self._SerialRect(KGRect, self._GetValueFromDict(element, 'ROI'))

            KGElePB.fThreshold = self._GetValueFromDict(element, 'threshold')
            KGElePB.strCfgPath = self._GetValueFromDict(element, 'cfgPath')
            KGElePB.strWeightPath = self._GetValueFromDict(element, 'weightPath')
            KGElePB.strNamePath = self._GetValueFromDict(element, 'namePath')
            KGElePB.strMaskPath = element.get('maskPath') or str()
            KGElePB.nBloodLength = self._GetValueFromDict(element, 'bloodLength')
            KGElePB.nMaxPointNum = self._GetValueFromDict(element, 'maxPointNum')
            KGElePB.nFilterSize = self._GetValueFromDict(element, 'filterSize')
            KGElePB.fMinScale = self._GetValueFromDict(element, 'minScale')
            KGElePB.fMaxScale = self._GetValueFromDict(element, 'maxScale')
            KGElePB.nScaleLevel = self._GetValueFromDict(element, 'scaleLevel')

            templates = KGElePB.stPBTemplates
            for templ in self._GetValueFromDict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._SerialTemplate(template, templ)

    def _SerialFixBloodReg(self, taskPB, taskVal):
        """
        FixBloodReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_FIXBLOOD
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.strCondition = self._GetValueFromDict(element, 'condition')
            elementPB.nFilterSize = self._GetValueFromDict(element, 'filterSize')
            elementPB.nBloodLength = self._GetValueFromDict(element, 'bloodLength')
            elementPB.nMaxPointNum = self._GetValueFromDict(element, 'maxPointNum')

    def _SerialStuckReg(self, taskPB, taskVal):
        """
        StuckReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_STUCKREG
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.fIntervalTime = self._GetValueFromDict(element, 'intervalTime')
            elementPB.fThreshold = self._GetValueFromDict(element, 'threshold')

    def _SerialFixObjReg(self, taskPB, taskVal):
        """
        FixObjReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_FIXOBJREG
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.strAlgorithm = self._GetValueFromDict(element, 'algorithm')
            elementPB.fMinScale = self._GetValueFromDict(element, 'minScale')
            elementPB.fMaxScale = self._GetValueFromDict(element, 'maxScale')
            elementPB.nScaleLevel = self._GetValueFromDict(element, 'scaleLevel')
            elementPB.nMaxBBoxNum = element.get('maxBBoxNum') or 1

            templates = elementPB.stPBTemplates
            for templ in self._GetValueFromDict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._SerialTemplate(template, templ)

    def _SerialPixReg(self, taskPB, taskVal):
        """
        PixReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_PIXREG
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.strCondition = self._GetValueFromDict(element, 'condition')
            elementPB.nFilterSize = self._GetValueFromDict(element, 'filterSize')

    def _SerialDeformReg(self, taskPB, taskVal):
        """
        DeformReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_DEFORMOBJ
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            deformElePB = taskPB.stPBAgentTaskElements.add()

            deformRect = deformElePB.stPBRect
            self._SerialRect(deformRect, self._GetValueFromDict(element, 'ROI'))

            deformElePB.fThreshold = self._GetValueFromDict(element, 'threshold')
            deformElePB.strCfgPath = self._GetValueFromDict(element, 'cfgPath')
            deformElePB.strWeightPath = self._GetValueFromDict(element, 'weightPath')
            deformElePB.strNamePath = self._GetValueFromDict(element, 'namePath')
            deformElePB.strMaskPath = element.get('maskPath') or str()

    def _SerialNumberReg(self, taskPB, taskVal):
        """
        NumberReg: common recongnizer method
        """
        taskPB.nTaskID = self._GetValueFromDict(taskVal, 'taskID')
        taskPB.eType = gameregProtoc_pb2.TYPE_NUMBER
        # taskPB.nSkipFrame = self._GetValueFromDict(taskVal, 'skipFrame')

        for element in self._GetValueFromDict(taskVal, 'elements'):
            elementPB = taskPB.stPBAgentTaskElements.add()

            rect = elementPB.stPBRect
            self._SerialRect(rect, self._GetValueFromDict(element, 'ROI'))

            elementPB.strAlgorithm = self._GetValueFromDict(element, 'algorithm')
            elementPB.fMinScale = self._GetValueFromDict(element, 'minScale')
            elementPB.fMaxScale = self._GetValueFromDict(element, 'maxScale')
            elementPB.nScaleLevel = self._GetValueFromDict(element, 'scaleLevel')

            templates = elementPB.stPBTemplates
            for templ in self._GetValueFromDict(element, 'templates'):
                template = templates.stPBTemplates.add()
                self._SerialTemplate(template, templ)

    def _UnSerialResultMsg(self, msg):
        Result = gameregProtoc_pb2.tagPBAgentMsg()
        Result.ParseFromString(msg)

        ResDict = {}
        ResDict['msgID'] = Result.eAgentMsgID
        ResDict['value'] = {}
        ResDict['value']['frameSeq'] = Result.stPBResultValue.nFrameSeq
        ResDict['value']['deviceIndex'] = Result.stPBResultValue.nDeviceIndex
        ResDict['value']['strJsonData'] = Result.stPBResultValue.strJsonData
        ResDict['value']['groupID'] = 1 # for test
        data = np.fromstring(Result.stPBResultValue.byImgData, np.uint8)
        ResDict['value']['image'] = np.reshape(
            data, (Result.stPBResultValue.nHeight, Result.stPBResultValue.nWidth, 3)
        )

        ResDict['value']['result'] = {}
        for result in Result.stPBResultValue.stPBResult:
            if result.eRegType == gameregProtoc_pb2.TYPE_PIXREG:
                ResDict['value']['result'][result.nTaskID] = \
                    self.__unSeiralRegerHandle[result.eRegType] \
                        (result, Result.stPBResultValue.nHeight, Result.stPBResultValue.nWidth)
            else:
                ResDict['value']['result'][result.nTaskID] = \
                    self.__unSeiralRegerHandle[result.eRegType](result)

        return ResDict

    def _UnSerialFixObjRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            fixObjSingleDict = {}
            fixObjSingleDict['flag'] = bool(res.nFlag)
            fixObjSingleDict['ROI'] = {}
            fixObjSingleDict['ROI']['x'] = res.stPBROI.nX
            fixObjSingleDict['ROI']['y'] = res.stPBROI.nY
            fixObjSingleDict['ROI']['w'] = res.stPBROI.nW
            fixObjSingleDict['ROI']['h'] = res.stPBROI.nH
            fixObjSingleDict['boxes'] = []
            for boxe in res.stPBBoxs:
                fixObjResBox = {}
                fixObjResBox['tmplName'] = boxe.strTmplName
                fixObjResBox['score'] = boxe.fScore
                fixObjResBox['scale'] = boxe.fScale
                fixObjResBox['classID'] = boxe.nClassID
                fixObjResBox['x'] = boxe.stPBRect.nX
                fixObjResBox['y'] = boxe.stPBRect.nY
                fixObjResBox['w'] = boxe.stPBRect.nW
                fixObjResBox['h'] = boxe.stPBRect.nH
                fixObjSingleDict['boxes'].append(fixObjResBox)

            ResList.append(fixObjSingleDict)

        return ResList

    def _UnSerialKingGloryBloodResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            ResSingleDict = {}
            ResSingleDict['flag'] = bool(res.nFlag)
            ResSingleDict['ROI'] = {}
            ResSingleDict['ROI']['x'] = res.stPBROI.nX
            ResSingleDict['ROI']['y'] = res.stPBROI.nY
            ResSingleDict['ROI']['w'] = res.stPBROI.nW
            ResSingleDict['ROI']['h'] = res.stPBROI.nH

            ResSingleDict['bloods'] = []

            for blood in res.stPBBloods:
                ResBlood = {}
                ResBlood['level'] = blood.nLevel
                ResBlood['score'] = blood.fScore
                ResBlood['percent'] = blood.fPercent
                ResBlood['classID'] = blood.nClassID
                ResBlood['name'] = blood.strName
                ResBlood['x'] = blood.stPBRect.nX
                ResBlood['y'] = blood.stPBRect.nY
                ResBlood['w'] = blood.stPBRect.nW
                ResBlood['h'] = blood.stPBRect.nH
                ResSingleDict['bloods'].append(ResBlood)

            ResList.append(ResSingleDict)

        return ResList

    def _UnSerialMapRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            mapSingleDict = {}
            mapSingleDict['flag'] = bool(res.nFlag)

            mapSingleDict['ROI'] = {}
            mapSingleDict['ROI']['x'] = res.stPBROI.nX
            mapSingleDict['ROI']['y'] = res.stPBROI.nY
            mapSingleDict['ROI']['w'] = res.stPBROI.nW
            mapSingleDict['ROI']['h'] = res.stPBROI.nH

            mapSingleDict['viewAnglePoint'] = {}
            mapSingleDict['viewAnglePoint']['x'] = res.stPBViewAnglePoint.nX
            mapSingleDict['viewAnglePoint']['y'] = res.stPBViewAnglePoint.nY

            mapSingleDict['myLocPoint'] = {}
            mapSingleDict['myLocPoint']['x'] = res.stPBMyLocPoint.nX
            mapSingleDict['myLocPoint']['y'] = res.stPBMyLocPoint.nY

            mapSingleDict['friendsLocPoints'] = []
            for point in res.stPBPoints:
                ResPoint = {}
                ResPoint['x'] = point.nX
                ResPoint['y'] = point.nY
                mapSingleDict['friendsLocPoints'].append(ResPoint)

            ResList.append(mapSingleDict)

        return ResList

    def _UnSerialMapDirectionRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            mapDirSingleDict = {}
            mapDirSingleDict['flag'] = bool(res.nFlag)

            mapDirSingleDict['ROI'] = {}
            mapDirSingleDict['ROI']['x'] = res.stPBROI.nX
            mapDirSingleDict['ROI']['y'] = res.stPBROI.nY
            mapDirSingleDict['ROI']['w'] = res.stPBROI.nW
            mapDirSingleDict['ROI']['h'] = res.stPBROI.nH

            mapDirSingleDict['viewAnglePoint'] = {}
            mapDirSingleDict['viewAnglePoint']['x'] = res.stPBViewAnglePoint.nX
            mapDirSingleDict['viewAnglePoint']['y'] = res.stPBViewAnglePoint.nY

            mapDirSingleDict['myLocPoint'] = {}
            mapDirSingleDict['myLocPoint']['x'] = res.stPBMyLocPoint.nX
            mapDirSingleDict['myLocPoint']['y'] = res.stPBMyLocPoint.nY

            ResList.append(mapDirSingleDict)

        return ResList

    def _UnSerialMultColorVar(self, result):
        ResList = []
        for res in result.stPBResultRes:
            ResSingleDict = {}
            ResSingleDict['flag'] = bool(res.nFlag)

            ResSingleDict['colorMeanVar'] = []
            for value in res.fColorMeanVars:
                ResSingleDict['colorMeanVar'].append(value)

            ResList.append(ResSingleDict)

        return ResList

    def _UnSerialShootGameBloodRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            SGSingleDict = {}
            SGSingleDict['flag'] = bool(res.nFlag)
            SGSingleDict['percent'] = res.fNum
            SGSingleDict['ROI'] = {}
            SGSingleDict['ROI']['x'] = res.stPBROI.nX
            SGSingleDict['ROI']['y'] = res.stPBROI.nY
            SGSingleDict['ROI']['w'] = res.stPBROI.nW
            SGSingleDict['ROI']['h'] = res.stPBROI.nH

            SGSingleDict['box'] = {}
            SGSingleDict['box']['x'] = res.stPBRect.nX
            SGSingleDict['box']['y'] = res.stPBRect.nY
            SGSingleDict['box']['w'] = res.stPBRect.nW
            SGSingleDict['box']['h'] = res.stPBRect.nH

            ResList.append(SGSingleDict)

        return ResList

    def _UnSerialShootGameHurtRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            SGHurtSingleDict = {}
            SGHurtSingleDict['flag'] = bool(res.nFlag)
            SGHurtSingleDict['ROI'] = {}
            SGHurtSingleDict['ROI']['x'] = res.stPBROI.nX
            SGHurtSingleDict['ROI']['y'] = res.stPBROI.nY
            SGHurtSingleDict['ROI']['w'] = res.stPBROI.nW
            SGHurtSingleDict['ROI']['h'] = res.stPBROI.nH

            ResList.append(SGHurtSingleDict)

        return ResList

    def _UnSerialFixBloodRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            fixBloodSingleDict = {}
            fixBloodSingleDict['flag'] = bool(res.nFlag)
            fixBloodSingleDict['percent'] = res.fNum
            fixBloodSingleDict['ROI'] = {}
            fixBloodSingleDict['ROI']['x'] = res.stPBROI.nX
            fixBloodSingleDict['ROI']['y'] = res.stPBROI.nY
            fixBloodSingleDict['ROI']['w'] = res.stPBROI.nW
            fixBloodSingleDict['ROI']['h'] = res.stPBROI.nH

            fixBloodSingleDict['box'] = {}
            fixBloodSingleDict['box']['x'] = res.stPBRect.nX
            fixBloodSingleDict['box']['y'] = res.stPBRect.nY
            fixBloodSingleDict['box']['w'] = res.stPBRect.nW
            fixBloodSingleDict['box']['h'] = res.stPBRect.nH

            ResList.append(fixBloodSingleDict)

        return ResList

    def _UnSerialPixRegResult(self, result, height, width):
        ResList = []
        for res in result.stPBResultRes:
            pixSingleDict = {}
            pixSingleDict['flag'] = bool(res.nFlag)
            pixSingleDict['points'] = []
            for point in res.stPBPoints:
                ResPoint = {}
                ResPoint['x'] = point.nX
                ResPoint['y'] = point.nY
                pixSingleDict['points'].append(ResPoint)

            # data = np.fromstring(res.byImage, np.uint8)
            # ResSingleDict['dstImage'] = np.reshape(
            #    data, (height, width, 1)
            #)
            ResList.append(pixSingleDict)

        return ResList

    def _UnSerialStuckRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            stuckSingleDict = {}
            stuckSingleDict['flag'] = bool(res.nFlag)
            stuckSingleDict['x'] = res.stPBRect.nX
            stuckSingleDict['y'] = res.stPBRect.nY
            stuckSingleDict['w'] = res.stPBRect.nW
            stuckSingleDict['h'] = res.stPBRect.nH
            ResList.append(stuckSingleDict)

        return ResList

    def _UnSerialDeformRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            deformSingleDict = {}
            deformSingleDict['flag'] = bool(res.nFlag)
            deformSingleDict['boxes'] = []
            for boxe in res.stPBBoxs:
                deformResBox = {}
                deformResBox['tmplName'] = boxe.strTmplName
                deformResBox['score'] = boxe.fScore
                deformResBox['scale'] = boxe.fScale
                deformResBox['classID'] = boxe.nClassID
                deformResBox['x'] = boxe.stPBRect.nX
                deformResBox['y'] = boxe.stPBRect.nY
                deformResBox['w'] = boxe.stPBRect.nW
                deformResBox['h'] = boxe.stPBRect.nH
                deformSingleDict['boxes'].append(deformResBox)

            ResList.append(deformSingleDict)

        return ResList

    def _UnSerialNumberRegResult(self, result):
        ResList = []
        for res in result.stPBResultRes:
            numberSingleDict = {}
            numberSingleDict['flag'] = bool(res.nFlag)
            numberSingleDict['num'] = res.fNum
            numberSingleDict['x'] = res.stPBRect.nX
            numberSingleDict['y'] = res.stPBRect.nY
            numberSingleDict['w'] = res.stPBRect.nW
            numberSingleDict['h'] = res.stPBRect.nH
            ResList.append(numberSingleDict)

        return ResList

    def _SerialRect(self, PBRect, valueRect):
        PBRect.nX = self._GetValueFromDict(valueRect, 'x')
        PBRect.nY = self._GetValueFromDict(valueRect, 'y')
        PBRect.nW = self._GetValueFromDict(valueRect, 'w')
        PBRect.nH = self._GetValueFromDict(valueRect, 'h')

    def _SerialTemplate(self, PBTemplate, valueTemplate):
        PBTemplate.strPath = self._GetValueFromDict(valueTemplate, 'path')
        PBTemplate.strName = self._GetValueFromDict(valueTemplate, 'name')
        hrect = PBTemplate.stPBRect
        self._SerialRect(hrect, self._GetValueFromDict(valueTemplate, 'location'))
        PBTemplate.fThreshold = self._GetValueFromDict(valueTemplate, 'threshold')
        PBTemplate.nClassID = self._GetValueFromDict(valueTemplate, 'classID')

    def _GetValueFromDict(self, dic, key):
        if key not in dic.keys():
            LOG.error("{} is needed".format(key))
            raise Exception('{} is needed'.format(key))

        return dic[key]
