# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import QPointF, QLineF, Qt


class ArrowLine(object):
    def __init__(self, pos1, pos2, from_node=None, end_node=None):
        self.__source = QPointF(pos1[0], pos1[1])
        self.__dest = QPointF(pos2[0], pos2[1])
        self.__line = QLineF(self.__source, self.__dest)

        self.__arrowLen = 10
        # self.__line.setLength(self.__line.length() - self.__arrowLen)
        self.__penWidth = 2
        self.__pen = QPen()
        self.__brush = QBrush()
        self.__color = QColor(255, 0, 0)
        self.__arrowRatio = 1.0
        self.__isSolid = True
        self.__from_node = from_node
        self.__end_node = end_node

    def get_from_node(self):
        return self.__from_node

    def get_end_node(self):
        return self.__end_node

    def set_arrow_len(self, length):
        self.__arrowLen = length

    def get_arrow_len(self):
        return self.__arrowLen

    def set_pen_width(self, width):
        self.__penWidth = width

    def get_pen_width(self):
        return self.__penWidth

    def set_arrow_solid(self, flag):
        self.__isSolid = flag

    def is_arrow_solid(self):
        return self.__isSolid

    def set_color(self, color):
        self.__color = color

    def get_color(self):
        return self.__color

    def get_line(self):
        return self.__line

    def paint(self, QPainter):
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
