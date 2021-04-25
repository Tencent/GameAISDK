# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
from math import sqrt

from PyQt5.QtGui import QColor, QPainterPath, QPen, QPainter, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QPointF

DEFAULT_LINE_COLOR = QColor(255, 0, 0, 255)
# DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QColor(255, 0, 0, 155)
# DEFAULT_SELECT_FILL_COLOR = QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QColor(255, 0, 0, 255)
# DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 0, 0)
MIN_Y_LABEL = 10


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    RECT, LINE, POINT, POLYGONLINE, POLYGON, GRAPH = list(range(6))

    def __init__(self, label=None, line_color=None, difficult=False, paint_label=True, name=RECT):
        self.label = list()
        self._current_label_text = None
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paint_label = paint_label
        self.shape_name = name
        self.pointLinePath = dict()

        self._highlight_index = None
        self._highlight_mode = self.NEAR_VERTEX
        self._highlight_settings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = True

        if line_color is not None:
            self.line_color = line_color

    def close(self):
        self._closed = True

    def set_shape_name(self, name):
        self.shape_name = name

    def set_label(self, label):
        self.label.append(label)
        self._current_label_text = label

    def reach_max_points(self):
        if len(self.points) >= 4:
            return True
        return False

    def add_point(self, point):
        if not self.reach_max_points():
            self.points.append(point)

    def pop_point(self):
        if self.points:
            return self.points.pop()
        return None

    def is_closed(self):
        return self._closed

    def set_open(self):
        self._closed = False

    def paint(self, painter):
        if self.points:
            color = self.select_line_color if self.selected else self.line_color
            pen = QPen(color)
            # Try using integer sizes for smoother drawing(?)
            # pen.setWidth(max(1, int(round(2.0 / self.scale))))
            pen.setWidth(max(1, int(round(5.0 / self.scale))))
            painter.setPen(pen)

            line_path = QPainterPath()
            vrtx_path = QPainterPath()

            line_path.moveTo(self.points[0])
            # Uncommenting the following line will draw 2 paths
            # for the 1st vertex, and make it non-filled, which
            # may be desirable.
            #self.draw_vertex(vrtx_path, 0)

            for i, p in enumerate(self.points):
                line_path.lineTo(p)
                self.draw_vertex(vrtx_path, i)
            if self.is_closed():
                line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)

            # Draw text at the top-left
            if self.paint_label:
                min_x = sys.maxsize
                min_y = sys.maxsize
                for point in self.points:
                    min_x = min(min_x, point.x())
                    min_y = min(min_y, point.y())

                if min_x != sys.maxsize and min_y != sys.maxsize:
                    pen = QPen()
                    pen.setWidth(3)
                    pen.setColor(QColor(0, 0, 0))
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    painter.setPen(pen)
                    linear_grad = QLinearGradient()
                    linear_grad.setColorAt(0, QColor(255, 255, 255))

                    font = QFont()
                    font.setPointSize(25)
                    font.setBold(True)
                    font.setFamily("Microsoft YaHei")

                    min_y += MIN_Y_LABEL
                    if len(self.label) > 0:
                        text_path = QPainterPath()
                        if self._current_label_text:
                            text_path.addText(min_x, min_y, font, self._current_label_text)
                        else:
                            text_path.addText(min_x, min_y, font, self.label[0])  # 应该取最后一个比较合理
                        painter.setBrush(linear_grad)
                        painter.drawPath(text_path)
                    min_y += 25

                    painter.setBrush(Qt.NoBrush)

            if self.fill:
                color = self.select_fill_color if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def draw_vertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlight_index:
            size, shape = self._highlight_settings[self._highlight_mode]
            d *= size
        if self._highlight_index is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearest_vertex(self, point, epsilon):
        for i, p in enumerate(self.points):
            if distance(p - point) <= epsilon:
                return i
        return None

    def contains_point(self, point):
        return self.make_path().contains(point)

    def make_path(self):
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        return path

    def bounding_rect(self):
        return self.make_path().boundingRect()

    def move_by(self, offset):
        self.points = [p + offset for p in self.points]

    def move_vertex_by(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlight_vertex(self, i, action):
        self._highlight_index = i
        self._highlight_mode = action

    def highlight_clear(self):
        self._highlight_index = None

    def _set_closed(self, closed):
        self._closed = closed

    def copy(self):
        shape = Shape("%s" % self.label)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._set_closed(self._closed)
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.difficult = self.difficult
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value


class Point(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class Line(object):
    def __init__(self, begin_x=0, begin_y=0, end_x=0, end_y=0):
        self.begin_x = begin_x
        self.begin_y = begin_y
        self.end_x = end_x
        self.end_y = end_y


class Rect(object):
    def __init__(self, x=0, y=0, w=0, h=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


def create_shape(points=None, closed=False):
    if points is None:
        print("input points is none, please check")
        return None

    if len(points) == 1:
        shape = Shape(name=Shape.POINT)

    elif len(points) == 2:
        shape = Shape(name=Shape.LINE)

    elif len(points) == 4:
        shape = Shape(name=Shape.RECT)

    else:
        print("unknown shape type, points number is {}".format(len(points)))
        return None

    for point in points:
        shape.add_point(QPointF(point.x, point.y))
    if closed:
        shape.close()

    return shape


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())
