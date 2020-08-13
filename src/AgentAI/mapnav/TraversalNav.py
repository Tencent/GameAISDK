# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time
import math
import logging

import cv2

from .AStarNav import AStarNavigation
from .MapUtil import *

MAX_PIX_DIST = 8

TRAVERSAL_FINISHED = 0
TRAVERSAL_FIND_NO_PATH = 1
TRAVERSAL_FIND_PATH = 2

class TraversalNavigation(object):
    """
    Traversal navigation according to map file
    """

    def __init__(self, mapFile, mapRecorder, debugShow=False):
        self.__mapFile = mapFile
        self.__mapRecorder = mapRecorder
        self.__debugShow = debugShow
        self.__curDestPoint = None
        self.__curDestAngle = -1
        self.__logger = logging.getLogger('agent')

    def Init(self):
        """
        Init module, load map image file and create astar nav object
        """
        self.__mapArr = cv2.imread(self.__mapFile, cv2.IMREAD_GRAYSCALE)
        self.__astarNav = AStarNavigation(self.__mapArr)
        return True

    def Finish(self):
        """
        Exit module, no need to do anything now
        """
        pass

    def Reset(self):
        """
        Reset destnation point
        """
        self.__curDestPoint = None

    def GetMoveAngle(self, agentPoint):
        """
        According to agent point, unvisited point, get move angle by astar nav
        """
        if (self.__curDestPoint is not None) and \
           (IsReachDest(agentPoint, self.__curDestPoint, MAX_PIX_DIST) is True):
            self.__curDestPoint = None

        timeBegin = time.time()
        if self.__curDestPoint is None:
            self.__curDestPoint = self.__mapRecorder.GetUnVisitedPoint(agentPoint)
            if self.__curDestPoint is None:
                return TRAVERSAL_FINISHED, -1

        pathPoints = self.__astarNav.FindPath(agentPoint[1], \
                                              agentPoint[0], \
                                              self.__curDestPoint[1], \
                                              self.__curDestPoint[0])
        timeEnd = time.time()
        if timeEnd - timeBegin > 1:
            self.__logger.warning('Get path cost time: {}s'.format(timeEnd - timeBegin))

        if len(pathPoints) < 2:
            self.__logger.warning('Astar not find path, path is {}'.format(pathPoints))
            return TRAVERSAL_FIND_NO_PATH, self.__curDestAngle

        if self.__debugShow is True:
            image = cv2.imread(self.__mapFile)
            for point in pathPoints:
                cv2.circle(image, (point[1], point[0]), 1, (0, 255, 0), 1)
            cv2.circle(image, (agentPoint[0], agentPoint[1]), 2, (255, 0, 0), 2)
            cv2.circle(image, (self.__curDestPoint[0], self.__curDestPoint[1]), 2, (0, 0, 255), 2)
            cv2.imshow('astar_path', image)
            cv2.waitKey(1)

        point = pathPoints[-2]
        destPoint = (point[1], point[0])

        destAngle = GetDestAngle(agentPoint, destPoint)

        if self.__curDestAngle == -1:
            self.__curDestAngle = destAngle
            return TRAVERSAL_FIND_PATH, self.__curDestAngle

        if IsSameDirection(destAngle, self.__curDestAngle, 20):
            return TRAVERSAL_FIND_PATH, -1
        else:
            self.__curDestAngle = destAngle
            return TRAVERSAL_FIND_PATH, self.__curDestAngle
