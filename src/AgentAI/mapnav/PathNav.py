# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import json
import math

from util import util
from .MapUtil import *

MAX_PIX_DIST = 12
MAX_DIFF_ANGLE_THR = 25

class PathNavigation(object):
    """
    Path navigation according to path config file
    """

    def __init__(self):
        self.__pathPoints = []
        self.__curDestIndex = -1
        self.__curDestAngle = -1
        self.__logger = logging.getLogger('agent')

    def Init(self, pathFile):
        """
        Init module, load path config file
        """
        if not self._LoadPath(pathFile):
            self.__logger.error('Load path file failed!')
            return False

        self.__logger.info('Path points: {}'.format(self.__pathPoints))
        return True

    def Finish(self):
        """
        Exit module, no need to do anything now
        """
        pass

    def GetMoveAngle(self, agentPoint):
        """
        According to agent point, path point, get move angle
        """
        if self.__curDestIndex == -1:
            self.__curDestIndex = 0
            self.__curDestAngle = GetDestAngle(agentPoint, self.__pathPoints[0])
            return False, self.__curDestAngle

        if IsReachDest(agentPoint, self.__pathPoints[self.__curDestIndex], MAX_PIX_DIST) is True:
            if self.__curDestIndex + 1 == len(self.__pathPoints):
                return True, -1

            self.__curDestIndex += 1
            self.__curDestAngle = GetDestAngle(agentPoint, self.__pathPoints[self.__curDestIndex])
            return False, self.__curDestAngle

        self.__curDestAngle = GetDestAngle(agentPoint, self.__pathPoints[self.__curDestIndex])
        return False, self.__curDestAngle

        #destAngle = GetDestAngle(agentPoint, self.__pathPoints[self.__curDestIndex])
        # if not IsSameDirection(self.__curDestAngle, destAngle, MAX_DIFF_ANGLE_THR):
        #     self.__curDestAngle = destAngle
        #     return False, self.__curDestAngle
        # else:
        #     return False, -1

    def _LoadPath(self, pathFile):
        cfgFile = util.ConvertToSDKFilePath(pathFile)
        if not os.path.exists(cfgFile):
            self.__logger.error('Path config file {} not exists!'.format(cfgFile))
            return False

        try:
            with open(cfgFile, 'rb') as file:
                jsonstr = file.read()
                pathCfg = json.loads(str(jsonstr, encoding='utf-8'))
                self.__mapScene = pathCfg.get('mapScene')
                self.__pathPoints = pathCfg.get(self.__mapScene).get('Path').get('line0')
        except Exception as e:
            self.__logger.error('Load file {} failed, error: {}.'.format(cfgFile, e))
            return False

        return True
