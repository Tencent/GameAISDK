# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
import os
import json
import logging
import base64
import cv2
from cffi import FFI
import numpy as np


ffi = FFI()

if sys.platform != "win32":
    lib = ffi.dlopen(None)
else:
    try:
        logging.info("begin open UIRecognize.exe")
        __dir__ = os.path.dirname(os.path.abspath(__file__))
        lib = ffi.dlopen("{}/../../UIRecognize.exe".format(__dir__))
    except Exception as error:
        logging.error("open UIRecognize failed, error {}".format(error))

try:
    ffi.cdef("""
        bool SendScriptUIAction(char *pszPkgBuff);
        bool PyLOGD(char *pszLogContent);
        bool PyLOGI(char *pszLogContent);
        bool PyLOGW(char *pszLogContent);
        bool PyLOGE(char *pszLogContent);
    """)
except Exception as e:
    logging.error("cdef function SendScriptUIAction failed")


UI_ACTION_NONE = 0
UI_ACTION_CLICK = 1
UI_ACTION_DRAG = 2
UI_ACTION_TEXT = 3
UI_ACTION_DRAG_AND_CHECK = 4
UI_ACTION_SCRIPT = 5

actionIDDict = dict()
actionIDDict["click"] = UI_ACTION_CLICK
actionIDDict["drag"] = UI_ACTION_DRAG


class CLOG(object):
    """
    UI LOG class, define interface for UI script log
    example:
    logger = CLOG()
    logger.info("....")
    logger.debug("....")
    logger.warn("....")
    logger.error("....")
    """
    def __init__(self):
        return

    def info(self, content):
        """
        info level log
        type of content is str
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        lib.PyLOGI(content)

    def debug(self, content):
        """
        debug level log
        type of content is str
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        lib.PyLOGD(content)

    def warn(self, content):
        """
        warn level log
        type of content is str
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        lib.PyLOGW(content)

    def error(self, content):
        """
        error level log
        type of content is str
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        lib.PyLOGE(content)


logger = CLOG()


class UIControlAPI(object):
    """
    UI Control API class, define interface for UI Script
    """
    def __init__(self, args):
        self.__uiState = None
        self.__tasks = dict()
        self._Parser(args)

    def _Parser(self, args):
        try:
            self.__uiState = json.loads(args)
            taskList = self.__uiState.get("tasks")
            for task in taskList:
                taskID = task.get("taskid")
                self.__tasks[taskID] = task
            # logger.info("python:tasks {}".format(self.__tasks))
        except Exception as e:
            logger.error("Couldn't parse， Reason {}".format(e))
        return True

    def GetData(self, strKey):
        """
        get current UI info
        strKey in ["tasks", "extNum", "frameSeq", "samplePath", "image"]
        """
        try:
            if strKey in ["tasks", "extNum", "frameSeq", "samplePath"]:
                return self.__uiState.get(strKey)
            elif strKey in ["image"]:
                width = self.__uiState.get("width")
                height = self.__uiState.get("height")
                data = self.__uiState.get(strKey)
                if None in [width, height, data]:
                    print("get data failed")
                    return
                shape = (height, width, 3)
                imageB = base64.b64decode(data)
                imageArr = np.fromstring(imageB, np.uint8)
                gameFrame = np.reshape(imageArr, shape)
                return gameFrame
        except Exception as error:
            logger.error("error is {}".format(error))

    def SetData(self, strKey, value):
        """
        reset value
        strKey in ["tasks", "extNum", "frameSeq", "samplePath", "image"]
        """
        self.__uiState[strKey] = value

    def DoTask(self, taskID):
        """
        do task of recognize for future use
        """
        pass

    def _PackClick(self, unitAction, idDict, taskParams, taskType):
        unitAction["actionType"] = idDict.get(taskType)
        unitAction["point1X"] = taskParams.get("actionX")
        unitAction["point1Y"] = taskParams.get("actionY")
        unitAction["actionThreshold1"] = taskParams.get("actionThreshold")
        unitAction["actionTmplExpdWPixel1"] = taskParams.get("actionTmplExpdWPixel")
        unitAction["actionTmplExpdHPixel1"] = taskParams.get("actionTmplExpdHPixel")
        unitAction["actionROIExpdWRatio1"] = taskParams.get("actionROIExpdWRatio")
        unitAction["actionROIExpdHRatio1"] = taskParams.get("actionROIExpdHRatio")
        unitAction["duringTimeMs"] = taskParams.get("duringTimeMs") or 100
        unitAction["sleepTimeMs"] = taskParams.get("sleepTimeMs") or 50
        # print("uinit action {}".format(unitAction))
        unitAction["point2X"] = -1
        unitAction["point2Y"] = -1

    def _PackDrag(self, unitAction, idDict, taskParams, taskType):
        unitAction["actionType"] = idDict.get(taskType)
        unitAction["point1X"] = taskParams.get("actionX1")
        unitAction["point1Y"] = taskParams.get("actionY1")
        unitAction["actionThreshold1"] = taskParams.get("actionThreshold1")
        unitAction["actionTmplExpdWPixel1"] = taskParams.get("actionTmplExpdWPixel1")
        unitAction["actionTmplExpdHPixel1"] = taskParams.get("actionTmplExpdHPixel1")
        unitAction["actionROIExpdWRatio1"] = taskParams.get("actionROIExpdWRatio1")
        unitAction["actionROIExpdHRatio1"] = taskParams.get("actionROIExpdHRatio1")
        unitAction["point2X"] = taskParams.get("actionX2")
        unitAction["point2Y"] = taskParams.get("actionY2")
        unitAction["actionThreshold2"] = taskParams.get("actionThreshold2")
        unitAction["actionTmplExpdWPixel2"] = taskParams.get("actionTmplExpdWPixel2")
        unitAction["actionTmplExpdHPixel2"] = taskParams.get("actionTmplExpdHPixel2")
        unitAction["actionROIExpdWRatio2"] = taskParams.get("actionROIExpdWRatio2")
        unitAction["actionROIExpdHRatio2"] = taskParams.get("actionROIExpdHRatio2")
        unitAction["duringTimeMs"] = taskParams.get("duringTimeMs") or 100
        unitAction["sleepTimeMs"] = taskParams.get("sleepTimeMs") or 50

    def DoAction(self, actionIDList):
        """
        do UI Action
        """
        pkgDict = dict()
        pkgDict["frameSeq"] = self.__uiState.get("frameSeq")
        pkgDict["samplePath"] = self.__uiState.get("samplePath")
        pkgDict["stateID"] = self.__uiState.get("stateID")
        pkgDict["scriptActions"] = []
        logging.info("pkgDict:{}, actionList {}".format(pkgDict, actionIDList))
        for actionID in actionIDList:
            unitAction = dict()
            unitAction["actionID"] = actionID
            taskParams = self.__tasks.get(actionID)
            if taskParams is None:
                logger.error("action id is invalid {}".format(actionID))
                continue

            taskType = taskParams.get("type")

            logging.info("taskType is {}".format(taskType))

            if taskType == "click":
                self._PackClick(unitAction, actionIDDict, taskParams, taskType)

            elif taskType == "drag":
                self._PackDrag(unitAction, actionIDDict, taskParams, taskType)

            else:
                lib.PyLOGE("invalid task type {}".format(taskType))

            pkgDict["scriptActions"].append(unitAction)
        paramStr = json.dumps(pkgDict)
        logger.info("python-->c++ func: param str is {}".format(paramStr))
        logger.info("python:begin call function send script ui action")
        flag = lib.SendScriptUIAction(paramStr.encode('utf-8'))
        logger.info("python:over call function send script ui action, result is {}.".format(flag))

    def CtrlResult(self):
        """
        dump json value as string and return it
        """
        result = dict()
        result["extNum"] = self.__uiState.get("extNum") or 1
        return json.dumps(result)
