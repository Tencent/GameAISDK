# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import cv2

from .MapUtil import *

class MapRecorder(object):
    """
    Record visited point in map file
    """

    def __init__(self, mapFile, visitedUpdatePix, debugShow=False):
        self.__updateCount = 0
        self.__mapFile = mapFile
        self.__visitedUpdatePix = visitedUpdatePix
        self.__debugShow = debugShow

    def Init(self):
        """
        Init module, load path config file
        """
        self.__recordMapFile = self._GetRecordFile(self.__mapFile)
        if self.__recordMapFile is None:
            return False

        if os.path.isfile(self.__recordMapFile):
            self.__mapArr = cv2.imread(self.__recordMapFile, cv2.IMREAD_GRAYSCALE)
        else:
            self.__mapArr = cv2.imread(self.__mapFile, cv2.IMREAD_GRAYSCALE)

        self.__height = self.__mapArr.shape[0]
        self.__width = self.__mapArr.shape[1]

        return True

    def Finish(self):
        """
        Exit module, no need to do anything now
        """
        pass

    def Update(self, x, y):
        """
        Update pint (x, y) to visited
        """
        tmp = self.__visitedUpdatePix
        for i in range(x-tmp, x+tmp+1):
            for j in range(y-tmp, y+tmp+1):
                self._SetVisited(i, j)

        if self.__debugShow is True:
            cv2.imshow('MapRecorder', self.__mapArr)
            cv2.waitKey(1)

        self.__updateCount += 1
        if self.__updateCount % 50 == 0:
            cv2.imwrite(self.__recordMapFile, self.__mapArr)

    def _SetVisited(self, x, y):
        if (0 < x < self.__width - 1) and (0 < y < self.__height - 1):
            if self._IsGround(x, y):
                self.__mapArr[y][x] = MAP_VISITED

    def _IsVisited(self, x, y):
        visited = False

        for i in range(x, x+1):
            for j in range(y, y+1):
                if i < 0 or i >= self.__width or j < 0 or j >= self.__height:
                    continue

                if self.__mapArr[j][i] == MAP_VISITED:
                    visited = True
                    break

                if not self._IsGround(i, j):
                    visited = True
                    break

        return visited

    def GetUnVisitedPoint(self, curPoint):
        """
        Get unvisited nearest point from curPoint
        """
        radius = 4
        lastRadius = 1
        curRadius = lastRadius + radius

        while True:
            startX = max(curPoint[0] - curRadius, 0)
            endX = min(curPoint[0] + curRadius, self.__width)
            startY = max(curPoint[1] - curRadius, 0)
            endY = min(curPoint[1] + curRadius, self.__height)

            for x in range(startX, endX, 2):
                for y in range(startY, endY, 2):
                    if (curPoint[0] - lastRadius <= x <= curPoint[0] + lastRadius) and \
                        (curPoint[1] - lastRadius <= y <= curPoint[1] + lastRadius):
                        continue

                    if not self._IsVisited(x, y):
                        return (x, y)

            if startX == 0 and endX == self.__width and startY == 0 and endY == self.__height:
                return None

            lastRadius += radius
            curRadius += radius

    def _IsGround(self, x, y):
        return self.__mapArr[y][x] >= MAP_GROUND

    def _GetRecordFile(self, mapFile):
        recordFile = None

        if mapFile[-4:] == '.png' or mapFile[-4:] == '.bmp':
            recordFile = mapFile[:-4] + '_record' + mapFile[-4:]
        return recordFile
