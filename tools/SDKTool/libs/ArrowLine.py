# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import QPointF, QLineF, Qt


class ArrowLine(object):
    def __init__(self, x1, y1, x2, y2, fromNode=None, endNode=None):
        self.__source = QPointF(x1, y1)
        self.__dest = QPointF(x2, y2)
        self.__line = QLineF(self.__source, self.__dest)

        self.__arrowLen = 10
        # self.__line.setLength(self.__line.length() - self.__arrowLen)
        self.__penWidth = 2
        self.__pen = QPen()
        self.__brush = QBrush()
        self.__color = QColor(255, 0, 0)
        self.__arrowRatio = 1.0
        self.__isSolid = True
        self.__fromNode = fromNode
        self.__endNode = endNode

    def GetFromNode(self):
        return self.__fromNode

    def GetEndNode(self):
        return self.__endNode

    def SetArrowLen(self, length):
        self.__arrowLen = length

    def GetArrowLen(self):
        return self.__arrowLen

    def SetPenWidth(self, width):
        self.__penWidth = width

    def GetPenWidth(self):
        return self.__penWidth

    def SetArrowSolid(self, flag):
        self.__isSolid = flag

    def IsArrowSolid(self):
        return self.__isSolid

    def SetColor(self, color):
        self.__color = color

    def GetColor(self):
        return self.__color

    def GetLine(self):
        return self.__line

    def Paint(self, QPainter):
        # setPen
        self.__pen.setWidth(self.__penWidth)
        self.__pen.setColor(self.__color)
        QPainter.setPen(self.__pen)

        # setBrush
        if self.__isSolid:
            self.__brush.setColor(self.__color)
            self.__brush.setStyle(Qt.SolidPattern)
            QPainter.setBrush(self.__brush)

        v = self.__line.unitVector()
        v.setLength(self.__arrowLen)
        v.translate(QPointF(self.__line.dx() * self.__arrowRatio, self.__line.dy() * self.__arrowRatio))

        # width of arrow
        n = v.normalVector()
        n.setLength(n.length() * 0.5)
        n2 = n.normalVector().normalVector()

        QPainter.drawLine(self.__line)
        QPainter.drawPolygon(v.p2(), n.p2(), n2.p2())
