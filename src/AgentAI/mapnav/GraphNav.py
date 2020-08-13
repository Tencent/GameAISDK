# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import logging
import json
import math
import random

from util import util
from .MapUtil import *

MAX_PIX_DIST = 12

class GraphNavigation(object):
    """
    Graph navigation according to graph path cfg file
    """

    def __init__(self):
        self.__pointDict = {}
        self.__pathDict = {}
        self.__prevPointIndex = -1
        self.__curPointIndex = -1
        self.__curAngle = -1
        self.__logger = logging.getLogger('agent')

    def Init(self, graphPathFile):
        """
        Init module, load graph path config file
        """
        if not self._LoadGraphPath(graphPathFile):
            self.__logger.error('Load graph path file failed!')
            return False

        self.__logger.info('Graph point: {}'.format(self.__pointDict))
        self.__logger.info('Graph path: {}'.format(self.__pathDict))
        if len(self.__pointDict) < 1 or len(self.__pathDict) < 1:
            self.__logger.error('Graph path is invalid')
            return False

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
        if self.__curPointIndex == -1:
            self.__curPointIndex = self._GetNearestPoint(agentPoint)
            self.__curAngle = GetDestAngle(agentPoint, self.__pointDict[self.__curPointIndex])
            self.__logger.info('Agent: {}, Dest id: {}, point: {}'.format(agentPoint,
                                                                          self.__curPointIndex,
                                                                          self.__pointDict[self.__curPointIndex]))
            return False, self.__curAngle

        if IsReachDest(agentPoint, self.__pointDict[self.__curPointIndex], MAX_PIX_DIST) is True:
            prevIndex = self.__curPointIndex
            self.__curPointIndex = self._ChooseDestPoint()
            self.__prevPointIndex = prevIndex
            self.__curAngle = GetDestAngle(agentPoint, self.__pointDict[self.__curPointIndex])
        else:
            self.__curAngle = GetDestAngle(agentPoint, self.__pointDict[self.__curPointIndex])

        self.__logger.info('Agent: {}, Dest id: {}, point: {}'.format(agentPoint,
                                                                      self.__curPointIndex,
                                                                      self.__pointDict[self.__curPointIndex]))

        return False, self.__curAngle

    def _GetNearestPoint(self, agentPoint):
        nearestIndex = -1
        nearestDist = sys.maxsize

        for index, point in self.__pointDict.items():
            distX = point[0] - agentPoint[0]
            distY = point[1] - agentPoint[1]

            dist = math.sqrt(distX * distX + distY * distY)
            if dist < nearestDist:
                nearestIndex = index
                nearestDist = dist

        if nearestIndex == -1:
            nearestIndex = 0

        return nearestIndex

    def _ChooseDestPoint(self):
        destPointSet = self.__pathDict[self.__curPointIndex].copy()
        if len(destPointSet) > 1:
            destPointSet.discard(self.__prevPointIndex)

        if len(destPointSet) == 0:
            return 0

        return random.sample(destPointSet, 1)[0]

    def _LoadGraphPath(self, graphPathFile):
        pathCfgFile = util.ConvertToSDKFilePath(graphPathFile)
        if not os.path.exists(pathCfgFile):
            self.__logger.error('Graph path cfg file {} not exists!'.format(pathCfgFile))
            return False

        try:
            with open(pathCfgFile, 'rb') as file:
                jsonstr = file.read()
                pathCfg = json.loads(str(jsonstr, encoding='utf-8'))
                self.__pointDict = self._LoadPints(pathCfg['points'])
                self.__pathDict = self._LoadPaths(pathCfg['paths'])
        except Exception as e:
            self.__logger.error('Load graph path file {} failed, error: {}.'.format(pathCfgFile, e))
            return False

        return True

    def _LoadPints(self, pointList):
        pointDict = {}

        for item in pointList:
            index = item['id']
            point = item['point']

            pointDict[index] = point

        return pointDict

    def _LoadPaths(self, pathList):
        pathDict = {}

        for path in pathList:
            peer1 = path['from']
            peer2List = path['to']
            for peer2 in peer2List:
                if pathDict.get(peer1) is None:
                    pathDict[peer1] = set()
                pathDict[peer1].add(peer2)

                if pathDict.get(peer2) is None:
                    pathDict[peer2] = set()
                pathDict[peer2].add(peer1)

        return pathDict
