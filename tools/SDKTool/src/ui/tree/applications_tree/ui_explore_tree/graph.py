# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from math import sqrt
import math
import cv2

from PyQt5.QtGui import QColor, QImage, QPixmap, QPen, QPainterPath
from PyQt5.QtCore import Qt
import networkx as nx

from ....utils import set_log_text
from .arrow_line import ArrowLine

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

# DEFAULT_CELL_X = 67
DEFAULT_CELL_X = 100
DEFAULT_CELL_Y = 55

DEFAULT_IMAGE_SCALE = 0.045


class UIGraph(object):
    def __init__(self):
        self.__graph = nx.DiGraph()
        self.__node_pos = dict()
        self.__node_sub_graph = dict()
        self.__node_images = dict()
        self.__node_pix_map = dict()
        self.__node_neighbors = dict()
        self.__node_buttons = dict()

        self.__scale = 1.0
        self.__high_light_node = None
        self.__select_node = None
        self.__show_image_flag = False
        self.__show_path_flag = False
        self.__edge_lines = list()
        self.__high_light_edge = None
        self.__select_edge = None
        self.__text_edit = None
        self.__text_content = None
        self.__windows_scale = (1.0, 1.0)
        self.__canvas_scale = 1
        self.__painter_width = 0
        self.__painter_height = 0

        self.__logger = logging.getLogger('sdktool')

    def process(self):
        # save direct neighbors for each node
        try:
            self._neighbors2()

            # position each node
            self._pos_nodes()

            # scale for each node image
            self.__scale = DEFAULT_IMAGE_SCALE
        except RuntimeError as e:
            self.__logger.error("graph process error:%s, please reload graph", e)

    def _pos_nodes(self):
        nodes = self.__graph.nodes
        groups = {}
        for node in nodes:
            # node name is groupXX_sceneXX.jpg, like: group0_scene0.jpg
            name = str(node)
            # groupXX_sceneXX
            base_name = name[:-4]
            sub_names = base_name.split('_')
            group_id = int(sub_names[0][5:])
            if groups.get(group_id) is None:
                groups[group_id] = []

            groups[group_id].append(node)

        group_ids = groups.keys()
        # number of group_id

        # max number of scene in all groups
        length_list = [len(groups.get(gid)) for gid in group_ids]
        length_list.append(1)

        cell_x = int(DEFAULT_CELL_X * self.__canvas_scale)
        cell_y = int(DEFAULT_CELL_Y * self.__canvas_scale)
        col = 1

        self.__painter_width = 0
        self.__painter_height = 0

        for gid in group_ids:
            cur_pos_x = col * cell_x
            cur_pos_y = HEIGHT / 2
            cur_pos_y = cur_pos_y * self.__canvas_scale

            space = cell_y
            index = 0
            for node in groups.get(gid):
                cur_pos_y = cur_pos_y + space * index
                space = -space
                index += 1

                if cur_pos_x > self.__painter_width:
                    self.__painter_width = cur_pos_x
                if cur_pos_y > self.__painter_height:
                    self.__painter_height = cur_pos_y
                self.__node_pos[node] = (cur_pos_x, cur_pos_y)
            col += 1

        self.__painter_width = int(self.__painter_width + cell_x * 2)
        self.__painter_height = int(self.__painter_height + cell_y * 2)

    def get_painter_size(self):
        return self.__painter_width, self.__painter_height

    def add_node_button(self, from_node, button, to_node, click_num):
        if self.__node_buttons.get(from_node) is None:
            self.__node_buttons[from_node] = []

        next_ui = dict()
        next_ui["button"] = button
        next_ui["end_node"] = to_node
        next_ui["click_num"] = click_num
        self.__node_buttons[from_node].append(next_ui)

    # def ResizePixMap(self, scale):
    def add_edge(self, from_node, end_node):
        self.__graph.add_edge(from_node, end_node)

    def add_node_image(self, node, img_path):
        old_path = self.__node_images.get(node)
        if old_path is not None:
            self.__logger.warning("%s old path is %s", node, old_path)

        self.__node_images[node] = img_path

    def nodes(self):
        return list(self.__graph.nodes())

    def edges(self):
        return list(self.__graph.edges())

    def nearest_node(self, x, y, epsilon):
        minDis = WIDTH
        retNode = None
        for node, pos in self.__node_pos.items():
            disX = pos[0] - x
            disY = pos[1] - y
            distance = int(sqrt(disX * disX + disY * disY))
            if minDis > distance and distance <= epsilon:
                minDis = distance
                retNode = node

        return retNode

    def set_show_node_image(self, flag):
        self.__show_image_flag = flag

    def set_canvas_scale(self, scale):
        self.__canvas_scale = scale

    def paint(self, painter):
        self.__text_content = None
        self._paint_group(painter)
        self._paint_high_light_node(painter)
        self._paint_select_node(painter)
        self._paint_high_light_edge(painter)
        self._paint_select_edge(painter)
        self._update_text_edit(self.__text_content)

    def _paint_group(self, painter):
        for node in self.nodes():
            x, y = self.__node_pos.get(node)
            pixmap = self.__node_pix_map.get(node)
            if pixmap is None:
                path = self.__node_images.get(node)
                image = QImage(path)
                newImg = image.scaled(int(image.width() * self.__scale), int(image.height() * self.__scale))
                pixmap = QPixmap.fromImage(newImg)
                self.__node_pix_map[node] = pixmap

            painter.drawPixmap(int((x - pixmap.width() / 2)), int(y - pixmap.height() / 2), pixmap)

            node_buttons = self.__node_buttons.get(node) or []

            leak_click = False
            for button in node_buttons:
                click_num = button["click_num"]
                if click_num == 0:
                    leak_click = True

            if leak_click:
                pen = QPen()
                pen.setColor(QColor(255, 0, 0))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawRect(int((x - pixmap.width() / 2)), int(y - pixmap.height() / 2),
                                 pixmap.width(), pixmap.height())

        self.__text_content = None
        self.__text_content = 'ui graph images number is {}.\n'.format(len(self.nodes()))

    def intersect_line(self, arrow_lines):
        degree_dict = dict()
        for arrow in arrow_lines:
            angle = arrow.get_line().angle()
            angle = angle % 180
            if degree_dict.get(angle) is None:
                degree_dict[angle] = []

            degree_dict[angle].append(arrow)

        ret_arrows = []
        for angle, arrows in degree_dict.items():
            size = len(arrows)
            if size == 1:
                ret_arrows.append(arrows[0])
            else:
                # Horizontal parallel, adjust y coordinate
                space_x = 0
                space_y = 0
                if angle == 90:
                    space_x = DEFAULT_CELL_X / (size * 2 + 1) * self.__canvas_scale
                else:
                    space_y = DEFAULT_CELL_Y / (size * 2 + 1) * self.__canvas_scale

                index = 0
                for arrow in arrows:
                    line = arrow.get_line()
                    pt1 = line.p1()
                    p1x = pt1.x()
                    p1y = pt1.y()
                    pt2 = line.p2()
                    p2x = pt2.x()
                    p2y = pt2.y()

                    offset_x = space_x * index
                    offset_y = space_y * index
                    p1x += offset_x
                    p1y += offset_y
                    p2x += offset_x
                    p2y += offset_y
                    space_x = -space_x
                    space_y = -space_y

                    index += 1
                    from_node = arrow.get_from_node()
                    end_node = arrow.get_end_node()
                    ret_arrows.append(ArrowLine((p1x, p1y), (p2x, p2y), from_node, end_node))

        return ret_arrows

    def _paint_select_node(self, painter):
        self.__edge_lines.clear()
        if self.__select_node is not None:
            sub_graph = self.__node_neighbors.get(self.__select_node)
            if sub_graph is not None:
                arrows = []
                for from_node, to_node in sub_graph.edges():
                    x1, y1 = self.__node_pos.get(from_node)
                    x2, y2 = self.__node_pos.get(to_node)
                    arrow = ArrowLine((x1, y1), (x2, y2), from_node, to_node)
                    arrows.append(arrow)

                ret_arrows = self.intersect_line(arrows)
                for arrow in ret_arrows:
                    arrow.paint(painter)
                    line = arrow.get_line()
                    edge = dict()
                    edge['line'] = line
                    edge['from'] = arrow.get_from_node()
                    edge['to'] = arrow.get_end_node()
                    self.__edge_lines.append(edge)

            if self.__show_image_flag is True:
                self._paint_node_image(painter, self.__select_node, DEFAULT_PAINT_NODE_IMG_SCALE)

            self.__text_content = 'selected: {}'.format(self.__select_node)

    def _paint_high_light_node(self, painter):
        if self.__high_light_node is not None:
            x, y = self.__node_pos.get(self.__high_light_node)
            pixMap = self.__node_pix_map.get(self.__high_light_node)
            line_path = QPainterPath()
            width = pixMap.width()
            height = pixMap.height()

            line_path.moveTo(x - width / 2, y - height / 2)
            line_path.lineTo(x - width / 2, y + height / 2)
            line_path.lineTo(x + width / 2, y + height / 2)
            line_path.lineTo(x + width / 2, y - height / 2)
            line_path.lineTo(x - width / 2, y - height / 2)
            painter.fillPath(line_path, DEFAULT_SELECT_IMG_FILL_COLOR)

            self.__text_content = 'highlight: {}'.format(self.__high_light_node)

    def _paint_edge_image(self, painter, node1, node2, scale):
        path1 = self.__node_images.get(node1)
        cv_image = cv2.imread(path1)
        button_list = self.__node_buttons.get(node1)
        for button in button_list:
            node = button.get("end_node")
            if node is node2:
                x, y, w, h = button.get("button")
                cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 5)

        img_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2BGRA)
        QtImg1 = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QImage.Format_RGB32)

        _, y1 = self.__node_pos.get(node1)
        _, y2 = self.__node_pos.get(node2)
        pixmap1 = QPixmap.fromImage(QtImg1)

        # pixmap = QPixmap.fromImage(QImage(path))
        width1 = int(scale * pixmap1.width())
        height1 = int(scale * pixmap1.height())
        pixmap1 = pixmap1.scaled(width1, height1, Qt.KeepAspectRatio)
        x1 = int(WIDTH * 0.15)
        # y1 = int(HEIGHT * 0.25)
        painter.drawPixmap(x1, int( (y1 + y2) / 2), pixmap1)

        path2 = self.__node_images.get(node2)
        pixmap2 = QPixmap.fromImage(QImage(path2))

        width2 = int(scale * pixmap2.width())
        height2 = int(scale * pixmap2.height())
        pixmap2 = pixmap2.scaled(width2, height2, Qt.KeepAspectRatio)

        x2 = int(WIDTH * 0.55)
        # y2 = int(HEIGHT * 0.25)
        painter.drawPixmap(x2, int((y1 + y2) / 2), pixmap2)

    def _paint_node_image(self, painter, node, scale):
        path = self.__node_images.get(node)
        cv_image = cv2.imread(path)
        # buttonList = []
        button_list = self.__node_buttons.get(node) or []
        for button in button_list:
            x, y, w, h = button.get("button")
            click_num = button.get("click_num")
            if click_num == 0:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            cv2.rectangle(cv_image, (x, y), (x + w, y + h), color, 5)

        img_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2BGRA)
        QtImg = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QImage.Format_RGB32)

        x, y = self.__node_pos.get(node)
        # pixmap = QPixmap.fromImage(QImage(path))
        pixmap = QPixmap.fromImage(QtImg)
        width = int(scale * pixmap.width())
        height = int(scale * pixmap.height())
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)
        painter.drawPixmap(x, y, pixmap)

    def _paint_high_light_edge(self, painter):
        if self.__high_light_edge:
            x1 = self.__high_light_edge['line'].p1().x()
            y1 = self.__high_light_edge['line'].p1().y()
            x2 = self.__high_light_edge['line'].p2().x()
            y2 = self.__high_light_edge['line'].p2().y()
            pen = QPen()
            pen.setWidth(DEFAULT_SELECT_EDGE_PEN_WIDTH)
            pen.setColor(DEFAULT_SELECT_EDGE_FILL_COLOR)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)
            self.__text_content = 'highlight: {} ---> {}'.format(self.__high_light_edge.get("from"),
                                                                 self.__high_light_edge.get("to"))

    def _paint_select_edge(self, painter):
        if self.__select_edge is not None:
            from_node = self.__select_edge.get("from")
            to_node = self.__select_edge.get("to")
            self._paint_edge_image(painter, from_node, to_node, DEFAULT_PAINT_EDGE_IMG_SCALE)
            self.__text_content = 'selected: {} ---> {}'.format(from_node, to_node)

    def set_select_node(self, node):
        self.__select_node = node

    def clear_select_node(self):
        self.__select_node = None

    def set_high_light_node(self, node):
        self.__high_light_node = node

    def clear_highlight_node(self):
        self.__high_light_node = None

    def nearest_edge(self, x, y, epsilon):
        min_dis = WIDTH
        ret_edge = None
        for item in self.__edge_lines:
            x1 = item['line'].p1().x()
            y1 = item['line'].p1().y()
            x2 = item['line'].p2().x()
            y2 = item['line'].p2().y()
            distance = self._point_to_line(x, y, x1, y1, x2, y2)
            if min_dis > distance and distance <= epsilon:
                min_dis = distance
                ret_edge = item

        return ret_edge

    def set_select_edge(self, edge):
        self.__select_edge = edge

    def clear_select_edge(self):
        self.__select_edge = None

    def set_highlight_edge(self, edge):
        self.__high_light_edge = edge

    def clear_high_light_edge(self):
        self.__high_light_edge = None

    @staticmethod
    def _point_to_line(x, y, x1, y1, x2, y2):
        # given point A（x1, y1），B(x2, y2), computer  distance of  point C (x, y) to |AB|
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

    def find_longest_path(self, dst_node):
        path = dict(nx.all_pairs_shortest_path(self.__graph))
        max_len = 0
        path_nodes = []
        for src_node in self.__graph.nodes:
            node_list = path[src_node].get(dst_node) or []
            if len(node_list) > max_len:
                max_len = len(node_list)
                path_nodes = node_list
        return path_nodes

    def _neighbors2(self):
        path = dict(nx.all_pairs_shortest_path(self.__graph))
        root_node = DEFAULT_ROOT_NODE
        if root_node not in path.keys():
            self.__logger.error("rootNode is not keys")
            return

        sum_no_path = 0
        for node in self.__graph.nodes:
            node_list = path[root_node].get(node)
            if node_list is None:
                self.__logger.error("there is no path %s---->%s", root_node, node)
                sum_no_path += 1
                node_list = self.find_longest_path(node)

            graph = nx.DiGraph()
            pre_node = None
            for subNode in node_list:
                if pre_node is None:
                    pre_node = subNode
                    continue
                else:
                    graph.add_edge(pre_node, subNode)
                pre_node = subNode

            self.__node_neighbors[node] = graph
        self.__logger.error("sum number of no path from root is %s", sum_no_path)

    def set_text_edit(self, text_edit):
        self.__text_edit = text_edit

    @staticmethod
    def _update_text_edit(text):
        # print(text)
        set_log_text(text)
