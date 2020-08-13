# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import numpy as np

from .MapUtil import *

STEP_COST = 10
OBLIQUE_COST = 14

class WayPoint(object):
    """
    Way point in the map definition
    """

    def __init__(self, x, y):
        self.X = x
        self.Y = y
        self.G = 0
        self.H = 0
        self.F = 0
        self.parentPoint = None

    def CalcF(self):
        """
        G: cost from start to sub point
        H: cost from sub point to end
        F = G + H, totol cost
        """
        self.F = self.G + self.H


class WayPointList(object):
    """
    Way point list definition
    """

    def __init__(self):
        self.__pointList = []

    def Exists(self, x, y):
        """
        Check whether (x, y) in point list or not
        """
        for p in self.__pointList:
            if p.X == x and p.Y == y:
                return True

        return False

    def PopMinPoint(self):
        """
        Pop minimum F point out from point list
        """
        if len(self.__pointList) == 0:
            return None

        minIndex = 0
        minF = self.__pointList[0].F

        for i in range(1, len(self.__pointList)):
            tempF = self.__pointList[i].F
            if tempF < minF:
                minF = tempF
                minIndex = i

        return self.__pointList.pop(minIndex)

    def Add(self, point):
        """
        Add new point to point list
        """
        self.__pointList.append(point)

    def Clear(self):
        """
        Clear point list when find a new path
        """
        del self.__pointList[:]

    def AllElements(self):
        """
        Return point list
        """
        return self.__pointList

    def Get(self, point):
        """
        Find point in point list
        """
        for p in self.__pointList:
            if p.X == point.X and p.Y == point.Y:
                return p

        return None

    def Dump(self):
        """
        Dump all point G/H/F value in point list
        """
        for p in self.__pointList:
            print('({0}, {1}), G: {2}  H: {3} F: {4}'.format(p.X, p.Y, p.G, p.H, p.F))


class AStarNavigation(object):
    """
    AStar path navigation algorithm
    """

    def __init__(self, mapArray):
        self.__mapArray = mapArray
        self.__openList = WayPointList()
        self.__closeList = WayPointList()

    def FindPath(self, startRow, startCol, endRow, endCol):
        """
        Find path from start to end
        startRow, startCol :  start point
        endRow, endCol : end point
        """
        #start point same as end point
        if startRow == endRow and startCol == endCol:
            return []

        if startRow >= self.__mapArray.shape[0] or \
                endRow >= self.__mapArray.shape[0] or \
                startCol >= self.__mapArray.shape[1] or \
                endCol >= self.__mapArray.shape[1]:
            return []

        #start point or end point is obstacle
        if self._IsObstacle(startRow, startCol) is True or self._IsObstacle(endRow, endCol) is True:
            return []

        self.__openList.Clear()
        self.__closeList.Clear()

        startPoint = WayPoint(startRow, startCol)
        endPoint = WayPoint(endRow, endCol)
        pathEndPoint = None

        self.__openList.Add(startPoint)
        while len(self.__openList.AllElements()) != 0:
            tempStart = self.__openList.PopMinPoint()
            self.__closeList.Add(tempStart)

            #get neighbor of tempStart
            neighborPoints = self._GetReachableNeighbor(tempStart)
            for point in neighborPoints.AllElements():

                #if point is in openlist, update its G,H,F,Parent
                #else add point to the openlist
                existPoint = self.__openList.Get(point)
                if existPoint != None:
                    self._UpdateExistPoint(tempStart, existPoint)
                else:
                    self._UpdateOpenList(tempStart, endPoint, point)

            #check endpoint in the openlist
            pathEndPoint = self.__openList.Get(endPoint)
            if pathEndPoint != None:
                break

        return self._MakePathPoint(pathEndPoint)

    def _UpdateExistPoint(self, tempStartPoint, existPoint):
        step = abs(tempStartPoint.X - existPoint.X) + abs(tempStartPoint.Y - existPoint.Y)
        tempG = (STEP_COST if step == 1 else OBLIQUE_COST)
        G = tempG + tempStartPoint.G
        if G < existPoint.G:
            existPoint.parentPoint = tempStartPoint
            existPoint.G = G
            existPoint.CalcF()

    def _UpdateOpenList(self, tempStartPoint, endPoint, point):
        point.parentPoint = tempStartPoint
        point.G = self._CalcG(point.parentPoint, point)
        point.H = self._CalcH(endPoint, point)
        point.CalcF()
        self.__openList.Add(point)


    def _CalcG(self, startPoint, point):
        step = abs(startPoint.X - point.X) + abs(startPoint.Y - point.Y)
        tempG = (STEP_COST if step == 1 else OBLIQUE_COST)
        parentG = (0 if point.parentPoint is None else point.parentPoint.G)
        return tempG + parentG


    def _CalcH(self, endPoint, point):
        step = abs(endPoint.X - point.X) + abs(endPoint.Y - point.Y)
        return step * STEP_COST

    def _GetReachableNeighbor(self, point):
        neighborPoints = WayPointList()

        for x in range(point.X - 1, point.X + 2):
            for y in range(point.Y - 1, point.Y + 2):
                if x == point.X and y == point.Y:
                    continue
                if x < 0 or x >= self.__mapArray.shape[0]:
                    continue
                if y < 0 or y >= self.__mapArray.shape[1]:
                    continue

                if self._IsReachable(point, x, y):
                    neighborPoints.Add(WayPoint(x, y))

        return neighborPoints

    def _IsObstacle(self, x, y):
        ret = (True if self.__mapArray[x][y] < MAP_GROUND else False)
        return ret

    def _IsReachable(self, point, x, y):
        if self._IsObstacle(x, y) is True:
            return False

        if self.__closeList.Exists(x, y):
            return False

        if abs(point.X - x) + abs(point.Y - y) == 1:
            return True
        else:
            if self._IsObstacle(point.X, y) or self._IsObstacle(x, point.Y):
                return False
            else:
                return True

    def _MakePathPoint(self, pathEndPoint):
        points = []
        curPoint = pathEndPoint
        while curPoint != None:
            # print('({0},{1})'.format(curPoint.X, curPoint.Y))
            points.append((curPoint.X, curPoint.Y))
            curPoint = curPoint.parentPoint
        return points


if __name__ == '__main__':
    maparr = np.array([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                       [1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1],
                       [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1],
                       [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1],
                       [1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1],
                       [1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
                       [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                       [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], np.uint8) + 255
    nav = AStarNavigation(maparr)
    path = nav.FindPath(4, 10, 1, 1)
    print(path)
