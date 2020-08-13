# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from math import sqrt
import math
import cv2

from PyQt5.QtGui import *
from PyQt5.QtCore import *


import networkx as nx

from libs.ArrowLine import ArrowLine

WIDTH = 1280
HEIGHT = 720
UIGRAPH = 1000
DEFAULT_SELECT_IMG_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_SELECT_EDGE_FILL_COLOR = QColor(128, 0, 255, 155)
DEFAULT_SELECT_EDGE_PEN_WIDTH = 5

DEFAULT_PAINT_EDGE_IMG_SCALE = 0.3
DEFAULT_PAINT_NODE_IMG_SCALE = 0.5

DEFAULT_ROOT_NODE = 'group0_scene0.jpg'

DEFAULT_CANVAS_WIDTH = 10
DEFAULT_CANVAS_HEIGHT = 10

DEFAULT_CELL_X = 67
DEFAULT_CELL_Y = 55

DEFAULT_IMAGE_SCALE = 0.045
# DEFAULT_CELL_X = 50
# DEFAULT_CELL_Y = 50
#
# DEFAULT_IMAGE_SCALE = 0.040


class UIGraph(object):
    def __init__(self):
        self.__graph = nx.DiGraph()
        self.__nodePos = dict()
        self.__nodeSubGraph = dict()
        self.__nodeImages = dict()
        self.__nodePixMap = dict()
        self.__nodeNeighbors = dict()
        self.__nodeButtons = dict()

        self.__scale = 1.0
        self.__highLightNode = None
        self.__selectNode = None
        self.__showImageFlag = False
        self.__showPathFlag = False
        self.__edgeLines = list()
        self.__highLightEdge = None
        self.__selectEdge = None
        self.__textEdit = None
        self.__textContent = None
        self.__windowsScale = (1.0, 1.0)

        self.__logger = logging.getLogger('sdktool')

    def Process(self):
        # save direct neighbors for each node
        try:
            self._Neighbors2()

            # position each node
            self._PosNodes()

            # scale for each node image
            self.__scale = DEFAULT_IMAGE_SCALE
        except Exception as e:
            self.__logger.error("graph process error:{}, please reload graph".format(e))

    def _Neighbors(self):
        unDirGraph = self.__graph.to_undirected()
        for node in unDirGraph.nodes:
            graph = nx.DiGraph()
            neighbors = list(unDirGraph.neighbors(node))
            for neighbor in neighbors:
                if self.__graph.has_edge(node, neighbor):
                    graph.add_edge(node, neighbor)
                elif self.__graph.has_edge(neighbor, node):
                    graph.add_edge(neighbor, node)
                else:
                    self.__logger.error("error in edge({}--->{})", neighbor, node)

            self.__nodeNeighbors[node] = graph

    def _PosNodes(self):
        nodes = self.__graph.nodes
        groups = {}
        for node in nodes:
            # node name is groupXX_sceneXX.jpg, like: group0_scene0.jpg
            name = str(node)
            # groupXX_sceneXX
            baseName = name[:-4]
            subNames = baseName.split('_')
            groupID = int(subNames[0][5:])
            if groups.get(groupID) is None:
                groups[groupID] = []

            groups[groupID].append(node)

        groupIds = groups.keys()
        # number of groupID
        width = len(groupIds) + 1
        # max number of scene in all groups
        lengthList = [len(groups.get(gid)) for gid in groupIds]
        lengthList.append(1)
        height = max(lengthList)

        # each grid width(cellX), height(cell height)
        cellX = DEFAULT_CELL_X
        cellY = DEFAULT_CELL_Y
        col = 1
        for gid in groupIds:
            curPosX = col * cellX
            curPosY = HEIGHT / 2

            space = cellY
            index = 0
            for node in groups.get(gid):
                curPosY = curPosY + space * index
                space = -space
                index += 1
                self.__nodePos[node] = (curPosX, curPosY)
            col += 1

        # scaleX = width / DEFAULT_CANVAS_WIDTH
        # scaleY = height / DEFAULT_CANVAS_HEIGHT
        # self.__windowsScale = (scaleX, scaleY)
        scaleX = (width + 1) * cellX / 1280
        scaleY = (height + 1) * cellY / 720
        self.__windowsScale = (scaleX, scaleY)
        self.__logger.debug("pos Node windows scale x:{} y:{}".format(scaleX, scaleY))

    def GetWindowScale(self):
        return self.__windowsScale

    def AddNodeButton(self, fromNode, button, toNode, clickNum):
        if self.__nodeButtons.get(fromNode) is None:
            self.__nodeButtons[fromNode] = []

        nextUI = dict()
        nextUI["button"] = button
        nextUI["endNode"] = toNode
        nextUI["clickNum"] = clickNum
        self.__nodeButtons[fromNode].append(nextUI)

    # def ResizePixMap(self, scale):
    def AddEdge(self, fromNode, endNode):
        self.__graph.add_edge(fromNode, endNode)

    def AddNodeImage(self, node, imgPath):
        oldPath = self.__nodeImages.get(node)
        if oldPath is not None:
            self.__logger.warning("{} old path is {}".format(node, oldPath))

        self.__nodeImages[node] = imgPath

    def Nodes(self):
        return list(self.__graph.nodes())

    def Edges(self):
        return list(self.__graph.edges())

    def NearestNode(self, x, y, epsilon):
        minDis = WIDTH
        retNode = None
        for node, pos in self.__nodePos.items():
            disX = pos[0] - x
            disY = pos[1] - y
            distance = int(sqrt(disX * disX + disY * disY))
            if minDis > distance and distance <= epsilon:
                minDis = distance
                retNode = node

        return retNode

    def SetShowNodeImage(self, flag):
        self.__showImageFlag = flag

    def Paint(self, painter):
        self.__textContent = None
        self._PaintGroup(painter)
        self._PaintHighLightNode(painter)
        self._PaintSelectNode(painter)
        self._PaintHighLightEdge(painter)
        self._PaintSelectEdge(painter)
        self._UpdateTextEdit(self.__textContent)

    def _PaintGroup(self, painter):
        for node in self.Nodes():
            x, y = self.__nodePos.get(node)
            pixmap = self.__nodePixMap.get(node)
            if pixmap is None:
                path = self.__nodeImages.get(node)
                image = QImage(path)
                newImg = image.scaled(int(image.width() * self.__scale), int(image.height() * self.__scale))
                pixmap = QPixmap.fromImage(newImg)
                self.__nodePixMap[node] = pixmap
            # painter.drawPixmap(int((x - pixmap.width() / 2)), int(y - pixmap.height() / 2), pixmap)
            painter.drawPixmap(int((x - pixmap.width() / 2)), int(y - pixmap.height() / 2), pixmap)

            nodeButtons = self.__nodeButtons.get(node) or []

            leakClick = False
            for button in nodeButtons:
                clickNum = button["clickNum"]
                if clickNum == 0:
                    leakClick = True

            if leakClick:
                pen = QPen()
                pen.setColor(QColor(255, 0, 0))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawRect(int((x - pixmap.width() / 2)), int(y - pixmap.height() / 2),
                                 pixmap.width(), pixmap.height())

        self.__textContent = None
        self.__textContent = 'ui graph images number is {}.\n'.format(len(self.Nodes()))

    def IntersectLine(self, arrowLines):
        degreeDict = dict()
        for arrow in arrowLines:
            angle = arrow.GetLine().angle()
            angle = angle % 180
            if degreeDict.get(angle) is None:
                degreeDict[angle] = []

            degreeDict[angle].append(arrow)

        retArrows = []
        for angle, arrows in degreeDict.items():
            size = len(arrows)
            if size == 1:
                retArrows.append(arrows[0])
            else:
                # Horizontal parallel, adjust y coordinate
                spaceX = 0
                spaceY = 0
                if angle == 90:
                    spaceX = DEFAULT_CELL_X / (size * 2 + 1)
                else:
                    spaceY = DEFAULT_CELL_Y / (size * 2 + 1)

                index = 0
                for arrow in arrows:
                    line = arrow.GetLine()
                    pt1 = line.p1()
                    p1X = pt1.x()
                    p1y = pt1.y()
                    pt2 = line.p2()
                    p2x = pt2.x()
                    p2y = pt2.y()

                    offsetX = spaceX * index
                    offsetY = spaceY * index
                    p1X += offsetX
                    p1y += offsetY
                    p2x += offsetX
                    p2y += offsetY
                    spaceX = -spaceX
                    spaceY = -spaceY

                    index += 1
                    fromNode = arrow.GetFromNode()
                    endNode = arrow.GetEndNode()
                    retArrows.append(ArrowLine(p1X, p1y, p2x, p2y, fromNode, endNode))

        return retArrows

    def _PaintSelectNode(self, painter):
        self.__edgeLines.clear()
        if self.__selectNode is not None:
            subGraph = self.__nodeNeighbors.get(self.__selectNode)
            if subGraph is not None:
                arrows = []
                for fromNode, toNode in subGraph.edges():
                    x1, y1 = self.__nodePos.get(fromNode)
                    x2, y2 = self.__nodePos.get(toNode)
                    arrow = ArrowLine(x1, y1, x2, y2, fromNode, toNode)
                    arrows.append(arrow)

                retArrows = self.IntersectLine(arrows)
                for arrow in retArrows:
                    arrow.Paint(painter)
                    line = arrow.GetLine()
                    edge = dict()
                    edge['line'] = line
                    edge['from'] = arrow.GetFromNode()
                    edge['to'] = arrow.GetEndNode()
                    self.__edgeLines.append(edge)

            if self.__showImageFlag is True:
                self._PaintNodeImage(painter, self.__selectNode, DEFAULT_PAINT_NODE_IMG_SCALE)

            self.__textContent = 'selected: {}'.format(self.__selectNode)

    def _PaintHighLightNode(self, painter):
        if self.__highLightNode is not None:
            x, y = self.__nodePos.get(self.__highLightNode)
            pixMap = self.__nodePixMap.get(self.__highLightNode)
            line_path = QPainterPath()
            width = pixMap.width()
            height = pixMap.height()

            line_path.moveTo(x - width / 2, y - height / 2)
            line_path.lineTo(x - width / 2, y + height / 2)
            line_path.lineTo(x + width / 2, y + height / 2)
            line_path.lineTo(x + width / 2, y - height / 2)
            line_path.lineTo(x - width / 2, y - height / 2)
            painter.fillPath(line_path, DEFAULT_SELECT_IMG_FILL_COLOR)

            self.__textContent = 'highlight: {}'.format(self.__highLightNode)

    def _PaintEdgeImage(self, painter, node1, node2, scale):
        path1 = self.__nodeImages.get(node1)
        cvImage = cv2.imread(path1)
        ButtonList = self.__nodeButtons.get(node1)
        for button in ButtonList:
            node = button.get("endNode")
            if node is node2:
                x, y, w, h = button.get("button")
                cv2.rectangle(cvImage, (x, y), (x + w, y + h), (0, 255, 0), 5)

        img_rgb = cv2.cvtColor(cvImage, cv2.COLOR_BGR2BGRA)
        QtImg1 = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QImage.Format_RGB32)

        _, y1 = self.__nodePos.get(node1)
        _, y2 = self.__nodePos.get(node2)
        pixmap1 = QPixmap.fromImage(QtImg1)

        # pixmap = QPixmap.fromImage(QImage(path))
        width1 = int(scale * pixmap1.width())
        height1 = int(scale * pixmap1.height())
        pixmap1 = pixmap1.scaled(width1, height1, Qt.KeepAspectRatio)
        x1 = int(WIDTH * 0.15)
        # y1 = int(HEIGHT * 0.25)
        painter.drawPixmap(x1, int( (y1 + y2) / 2), pixmap1)

        path2 = self.__nodeImages.get(node2)
        pixmap2 = QPixmap.fromImage(QImage(path2))

        width2 = int(scale * pixmap2.width())
        height2 = int(scale * pixmap2.height())
        pixmap2 = pixmap2.scaled(width2, height2, Qt.KeepAspectRatio)

        x2 = int(WIDTH * 0.55)
        # y2 = int(HEIGHT * 0.25)
        painter.drawPixmap(x2, int((y1 + y2) / 2), pixmap2)

    def _PaintNodeImage(self, painter, node, scale):
        path = self.__nodeImages.get(node)
        cvImage = cv2.imread(path)
        # buttonList = []
        buttonList = self.__nodeButtons.get(node) or []
        for button in buttonList:
            x, y, w, h = button.get("button")
            clickNum = button.get("clickNum")
            if clickNum == 0:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            cv2.rectangle(cvImage, (x, y), (x + w, y + h), color, 5)

        img_rgb = cv2.cvtColor(cvImage, cv2.COLOR_BGR2BGRA)
        QtImg = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QImage.Format_RGB32)

        x, y = self.__nodePos.get(node)
        # pixmap = QPixmap.fromImage(QImage(path))
        pixmap = QPixmap.fromImage(QtImg)
        width = int(scale * pixmap.width())
        height = int(scale * pixmap.height())
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)
        # x = min(x, WIDTH - width)
        # y = min(y, HEIGHT - height)
        # x = max(x, 0)
        # y = max(y, 0)
        painter.drawPixmap(x, y, pixmap)

    def _PaintHighLightEdge(self, painter):
        if self.__highLightEdge is not None:
            # x1, y1 = self.__nodePos.get(self.__highLightEdge.get("from"))
            # x2, y2 = self.__nodePos.get(self.__highLightEdge.get("to"))
            x1 = self.__highLightEdge['line'].p1().x()
            y1 = self.__highLightEdge['line'].p1().y()
            x2 = self.__highLightEdge['line'].p2().x()
            y2 = self.__highLightEdge['line'].p2().y()
            pen = QPen()
            pen.setWidth(DEFAULT_SELECT_EDGE_PEN_WIDTH)
            pen.setColor(DEFAULT_SELECT_EDGE_FILL_COLOR)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)
            self.__textContent = 'highlight: {} ---> {}'.format(self.__highLightEdge.get("from"),
                                                                   self.__highLightEdge.get("to") )

    def _PaintSelectEdge(self, painter):
        if self.__selectEdge is not None:
            fromNode = self.__selectEdge.get("from")
            toNode = self.__selectEdge.get("to")
            self._PaintEdgeImage(painter, fromNode, toNode, DEFAULT_PAINT_EDGE_IMG_SCALE)
            self.__textContent = 'selected: {} ---> {}'.format(fromNode,
                                                                   toNode)
            # self._PaintEdgeImage(painter, toNode, DEFAULT_PAINT_EDGE_IMG_SCALE)

    def SetSelectNode(self, node):
        self.__selectNode = node

    def GetSelectNode(self):
        return self.__selectNode

    def ClearSelectNode(self):
        self.__selectNode = None

    def SetHighLightNode(self, node):
        self.__highLightNode = node

    def GetHighLightNode(self):
        return self.__highLightNode

    def ClearHighLightNode(self):
        self.__highLightNode = None

    def NearestEdge(self, x, y, epsilon):
        minDis = WIDTH
        retEdge = None
        for item in self.__edgeLines:
            x1 = item['line'].p1().x()
            y1 = item['line'].p1().y()
            x2 = item['line'].p2().x()
            y2 = item['line'].p2().y()
            distance = self._PointToLine(x, y, x1, y1, x2, y2)
            if minDis > distance and distance <= epsilon:
                minDis = distance
                retEdge = item

        return retEdge

    def SetSelectEdge(self, edge):
        self.__selectEdge = edge

    def ClearSelectEdge(self):
        self.__selectEdge = None

    def GetSelectEdge(self):
        return self.__selectEdge

    def SetHighLightEdge(self, edge):
        self.__highLightEdge = edge

    def ClearHighLightEdge(self):
        self.__highLightEdge = None

    def GetHighLightEdge(self, edge):
        return self.__highLightEdge

    # given point A（x1, y1），B(x2, y2), computer  distance of  point C (x, y) to |AB|
    def _PointToLine(self, x, y, x1, y1, x2, y2):
        # | AB | * | AC |* cos(x)
        cross = (x2 - x1) * (x - x1) + (y2 - y1) * (y - y1)
        # cos(x) < 0 , the degree of angle(AB， AC) no less than 90 degree
        # distance = |AC|
        if cross <= 0:
            return math.sqrt((x - x1) * (x - x1) + (y - y1) * (y - y1) + 0.0)

        # | AB |
        d2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
        # |AC| >= |AB|, the degree of angle((BA， BC)) no less than 90 degree
        # distance = |BC|
        if cross >= d2:
            return math.sqrt((x - x2) * (x - x2) + (y - y2) * (y - y2))

        r = cross / d2
        # D(px，py） in AB， and AD is perpendicular to AB
        px = x1 + (x2 - x1) * r
        py = y1 + (y2 - y1) * r
        return math.sqrt((x - px) * (x - px) + (y - py) * (y - py))

    def FindLongestPath(self, dstNode):
        path = dict(nx.all_pairs_shortest_path(self.__graph))
        maxLen = 0
        pathNodes = []
        for srcNode in self.__graph.nodes:
            nodeList = path[srcNode].get(dstNode) or []
            if len(nodeList) > maxLen:
                maxLen = len(nodeList)
                pathNodes = nodeList

        return pathNodes

    def _Neighbors2(self):
        path = dict(nx.all_pairs_shortest_path(self.__graph))
        rootNode = DEFAULT_ROOT_NODE
        if rootNode not in path.keys():
            self.__logger.error("rootNode is not keys")
            return

        sum = 0
        for node in self.__graph.nodes:
            nodeList = path[rootNode].get(node)
            if nodeList is None:
                self.__logger.error("there is no path {}---->{}".format(rootNode, node))
                sum += 1
                nodeList = self.FindLongestPath(node)

            graph = nx.DiGraph()
            preNode = None
            for subNode in nodeList:
                if preNode is None:
                    preNode = subNode
                    continue
                else:
                    graph.add_edge(preNode, subNode)
                preNode = subNode

            self.__nodeNeighbors[node] = graph
        self.__logger.error("sum number of no path from root is {}".format(sum))

    def SetTextEdit(self, textEdit):
        self.__textEdit = textEdit

    def _UpdateTextEdit(self, text):
        self.__textEdit.setPlainText(text)


if __name__ == "__main__":
    # g = nx.DiGraph()
    #
    # g.add_path(['b', 'c'])
    # g.add_path(['d', 'c'])

    uigraph = UIGraph()
    # uigraph.AddEdge('b', 'c')

    # sg = uigraph.SubGraph()

    # print("result is {}".format(sg))

    # for key, value in sg.items():
    #     print("key {}, nodes is {} ".format(key, value.nodes))
    #
    # # s = g.subgraph(nx.shortest_path(g.to_undirected(), 'b'))
    #
    # print(sg)

    arrows = []
    l1 = ArrowLine(0, -1, 0, 1)
    line = l1.GetLine()
    print(" test ({},{}, {}, {}))".format(
        line.p1().x(), line.p1().y(), line.p2().x(), line.p2().y()))

    arrows.append(l1)
    l2 = ArrowLine(0, 2, 0, 1)
    line = l2.GetLine()
    print(" test ({},{}, {}, {}))".format(
        line.p1().x(), line.p1().y(), line.p2().x(), line.p2().y()))

    arrows.append(l2)
    l3 = ArrowLine(1, 0, 10, 0)
    arrows.append(l3)
    l4 = ArrowLine(10, 0, 1, 0)
    arrows.append(l4)

    retArrows = uigraph.IntersectLine(arrows)

    for arrow in retArrows:
        line = arrow.GetLine()
        print("line pt1 ({}, {}), pt2 ({}, {})".format(line.p1().x(), line.p1().y(),
                                                       line.p2().x(), line.p2().y()))














