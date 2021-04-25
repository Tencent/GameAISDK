# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time
import os
import cv2
from PyQt5.QtGui import QCursor, QPainter, QBrush, QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QPoint
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtGui import QImage, QPixmap

from .shape import Shape, create_shape, Point, distance
from ...common.define import Mode, image_path_keys, ITEM_TYPE_TEMPLATE, Drag_Key, Click_Key, Drag_Check_Key

from ..dialog.label_text_dialog import LabelTextDialog
from ..dialog.progress_bar_dialog import ProgressBarDialog
from ..tree.project_data_manager import ProjectDataManager
from ..tree.tree_manager import tree_mgr
from ..utils import qtpixmap_to_cvimg, get_sub_nodes, get_tree_top_nodes, create_tree_item, get_file_list, \
    get_item_by_type
from ..main_window.tool_window import ui
from ...context.app_context import g_app_context
from .data_source import DataSource, DeviceActionType, DeviceActionParamName
from ...project.project_manager import g_project_manager
from ...WrappedDeviceAPI.wrappedDeviceConfig import DeviceType
from .dev_toolbar import DeviceOperationToolbar
from ...subprocess_service.subprocess_service_manager import backend_service_manager as bsm

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor


logger = logging.getLogger("sdktool")


class UICanvas(QWidget):
    zoom_request = pyqtSignal(int)
    scroll_request = pyqtSignal(int, int)
    new_shape = pyqtSignal()
    selection_changed = pyqtSignal(bool)
    shape_moved = pyqtSignal()
    drawing_polygon = pyqtSignal(bool)

    CREATE, EDIT, LABEL = list(range(3))
    # RECT, LINE, POINT = list(range(3))

    epsilon = 11.0

    def __init__(self, *args, **kwargs):
        super(UICanvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        # self.mode = self.CREATE  # 画布当前的模式，create表示画图形，edit表示修改图形
        self.mode = None
        self.shapes = []
        self.current = None
        self.mouse_move_flag = False
        self.next_model = None
        self.current_model = list()  # list类型，表示当前需要执行的画图形的任务，比如如果其内容为[rect, rect, line, point]，
        # 那说明接下来需要画四个图形，分别是框，框，线，点。
        self.point_graph_index = 1
        # self.graph_prev_point_index = -1
        self.selected_shape = None  # save the selected shape here
        self.selected_shape_copy = None
        self.drawing_line_color = QColor(0, 0, 255)
        self.drawing_rect_color = QColor(0, 0, 255)
        self.line = Shape(line_color=self.drawing_line_color)
        self.prev_point = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hide_background = False
        self.hide_background = False
        self.h_shape = None
        self.h_vertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.verified = False
        self.draw_square = False
        self._sample_tree_item = None
        self.rect_tree_item = list()  # list类型，当前画图的图形（rect）与QTreeItem的对应，以便拖拽的时候实时更新item中的数据。
        self.point_tree_item = list()  # list类型，当前画图的图形（point）与QTreeItem的对应，以便拖拽的时候实时更新item中的数据。
        self.line_tree_item = list()
        self.item_rect = dict()  # rect类型的字典，{"x": int, "y", int, "w": int, "h": int}
        self.item_point = dict()  # point类型的字典，{"x": int, "y", int}
        self.item_line = dict()
        self.shape_tree = dict()  # UI标签功能用到的成员，是一个字典，key为shape类型变量，value为item
        # 表示该标签（shape）对应的是树结构中的某一个类型（类型在树结构中以item形式呈现）
        self.polygon_line_item = None
        self.btn_press_pos = QPoint()
        self.mouse_flag = False
        self.shapes_num = 0

        self.tree_icon = QIcon()
        self.tree_icon.addPixmap(QPixmap(":/menu/tree_icon.png"), QIcon.Normal, QIcon.Off)

        self.__logger = logging.getLogger('sdktool')
        self.pix_level_flag = False
        self.item_shape = dict()
        self.label_dialog = LabelTextDialog(parent=self)

        self.label_flag = False
        self.ui = None
        self.cursor_width = 10
        # self.polyRNN = PolyRNNModel()
        self.right_menu = QMenu(self)

        # 删除shape的动作，在UI标签中用到
        self.action_delete_shape = QAction(self)
        self.action_delete_shape.setText("删除")
        self.action_delete_shape.triggered.connect(self.delete_shape)
        self.ui = ui
        self.ui_graph = None
        # self.save_pixmap = False
        self.__data_source = DataSource()
        self.process_bar = None

        self.dev_toolbar = DeviceOperationToolbar(self)
        self.dev_toolbar.set_data_source(self.__data_source)
        self.__hide_background = None

    def set_dev_toolbar_position(self):
        dev_tb_w = 120
        dev_tb_h = 32
        canvas_w = self.ui.graph_view.width()
        x = canvas_w - dev_tb_w - 30
        self.dev_toolbar.setGeometry(x, 10, dev_tb_w, dev_tb_h)

    def update_dev_toolbar(self):
        device_type = g_project_manager.get_device_type()
        if device_type == DeviceType.Android.value:
            self.dev_toolbar.enable_android_buttons(True)
        else:
            self.dev_toolbar.enable_android_buttons(False)
            # self.dev_toolbar.setHidden(True)

        self.set_dev_toolbar_position()

    def resizeEvent(self, evt):
        super(UICanvas, self).resizeEvent(evt)
        if self.is_service_running():
            return
        self.update_dev_toolbar()

    def add_ui_graph(self, ui_graph):
        self.ui_graph = ui_graph

    def delete_shape(self):
        """ action_delete_shape动作的槽函数，在UI标签中用到
            删除shape（标签）时，self.shapeItem中删除对应的项
        :return:
        """
        self.shapes.remove(self.selected_shape)

        # 查找"labels" 的节点
        sub_nodes = get_tree_top_nodes(self.ui.tree_widget_right)
        label_node = None
        for sub_node in sub_nodes:
            if sub_node.text(0) == 'labels':
                label_node = sub_node
                break

        if label_node is None:
            return

        if self.selected_shape not in self.shape_tree:
            return

        shape_item = self.shape_tree[self.selected_shape]
        label_node.removeChild(shape_item)

    def get_pixmap(self):
        return self.pixmap

    def is_visible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    @staticmethod
    def is_service_running():
        """ 判断是否有服务正在运行

        :return:
        """
        return bsm.has_service_running()

    def segment(self):
        return self.mode == self.LABEL

    def editing(self):
        return self.mode == self.EDIT

    def set_editing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.un_highlight()
            self.deSelectShape()
        self.prev_point = QPointF()
        self.repaint()

    def un_highlight(self):
        if self.h_shape:
            self.h_shape.highlight_clear()
        self.h_vertex = self.h_shape = None

    def selected_vertex(self):
        return self.h_vertex is not None

    def set_samples_tree_item(self, tree_item):
        """ 设置样本树节点，用于更新实时生成的样本树

        :param tree_item:
        :return:
        """
        self._sample_tree_item = tree_item

    def set_rect_tree_item(self, tree_item):
        """ 向self.rect_tree_item添加一个rect的QTreeItem，当下次画图时，会对应修改该item的值

        :param tree_item:
        :return:
        """
        self.rect_tree_item.append(tree_item)
        # filter "threshold"
        for item_index in range(tree_item.childCount()):
            item_child = tree_item.child(item_index)
            key_text = item_child.text(0)
            if key_text in ['x', 'y', 'w', 'h', 'width', 'height']:
                # print('************test**************{}'.format(itemChild.text(1)))
                self.item_rect[item_child.text(0)] = int(item_child.text(1))
            else:
                # templateThreshold
                self.item_rect[item_child.text(0)] = float(item_child.text(1))

    def set_line_tree_item(self, tree_item):
        """ 向self.line_tree_item添加一个line的QTreeItem，当下次画图时，会对应修改该item的值

        :param tree_item:
        :return:
        """

        self.line_tree_item.append(tree_item)
        for item_index in range(tree_item.childCount()):
            item_child = tree_item.child(item_index)

            # "actionX1"(0), "actionY1"(1),"actionX2"(7), "actionY2"(8)
            if item_index % 7 < 2:
                self.item_line[item_child.text(0)] = int(item_child.text(1))
            else:
                self.item_line[item_child.text(0)] = item_child.text(1)

    def set_point_tree_item(self, tree_item):
        """ 向self.point_tree_item添加一个point的QTreeItem，当下次画图时，会对应修改该item的值

        :param tree_item:
        :return:
        """
        self.point_tree_item.append(tree_item)
        for item_index in range(tree_item.childCount()):
            item_child = tree_item.child(item_index)
            if item_index < 2:
                self.item_point[item_child.text(0)] = int(item_child.text(1))
            else:
                self.item_point[item_child.text(0)] = item_child.text(1)

    def set_item_rect(self, item_tree=None):
        """ self.item_rect保存的是事实的画布上框的坐标，将self.item_rect中的坐标写到对应的rect类型的QTreeItem中

        :param item_tree:
        :return:
        """

        if item_tree is None:
            item_tree = self.rect_tree_item[0]

        for item_index in range(item_tree.childCount()):
            item_child = item_tree.child(item_index)
            item_child.setText(1, str(self.item_rect.get(item_child.text(0))))

            # print("{} set text {}".format(itemChild.text(0), self.item_rect.get(itemChild.text(0))))
        self.update()

    def set_item_line(self, item_tree=None):
        """ self.line_tree_item保存的是事实的画布上线的起始点和结束点的坐标，将self.line_tree_item中的坐标写到对应的line类型的QTreeItem中
        :param item_tree:
        :return:
        """
        if item_tree is None:
            item_tree = self.line_tree_item[0]

        for item_index in range(item_tree.childCount()):
            item_child = item_tree.child(item_index)
            item_child.setText(1, str(self.item_line[item_child.text(0)]))

        self.update()

    def set_item_point(self, item_tree=None):
        """ self.point_tree_item保存的是事实的画布上点的坐标，将self.point_tree_item中的坐标写到对应的rect类型的QTreeItem中

        :param item_tree:
        :return:
        """
        if item_tree is None:
            item_tree = self.point_tree_item[0]

        for item_index in range(item_tree.childCount()):
            item_child = item_tree.child(item_index)
            item_child.setText(1, str(self.item_point[item_child.text(0)]))

    def get_mouse_move_flag(self):
        return self.mouse_move_flag

    def leaveEvent(self, event):
        if self.label_flag:
            self.label_flag = False
            if self.mode == self.LABEL:
                self.mode = self.EDIT

    def __check_pos_and_color(self, pos):
        color = self.drawing_line_color
        if self.out_of_pixmap(pos):
            # Don't allow the user to draw outside the pixmap.
            # Project the point to the pixmap's edges.
            pos = self.intersectionPoint(self.current[-1], pos)
        elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
            # Attract line to starting point and colorise to alert the user:
            pos = self.current[0]
            color = self.current.line_color
            self.override_cursor(CURSOR_POINT)
            self.current.highlight_vertex(0, Shape.NEAR_VERTEX)

        self.line[1] = pos

        self.line.line_color = color
        self.prev_point = QPointF()
        self.current.highlight_clear()

    def _polygon_drawing(self, pos):
        self.__check_pos_and_color(pos)

        if self.current_model[0] == Shape.RECT:
            if int(pos.x()) < int(self.btn_press_pos.x()):
                if int(pos.y()) < int(self.btn_press_pos.y()):
                    self.item_rect["x"] = int(pos.x())
                    self.item_rect["y"] = int(pos.y())
                    self.item_rect["w"] = int(self.btn_press_pos.x() - pos.x())
                    self.item_rect["h"] = int(self.btn_press_pos.y() - pos.y())
                else:
                    self.item_rect["x"] = int(pos.x())
                    self.item_rect["y"] = int(self.btn_press_pos.y())
                    self.item_rect["w"] = int(self.btn_press_pos.x() - pos.x())
                    self.item_rect["h"] = int(pos.y() - self.btn_press_pos.y())
            else:
                if int(pos.y()) < int(self.btn_press_pos.y()):
                    self.item_rect["x"] = int(self.btn_press_pos.x())
                    self.item_rect["y"] = int(pos.y())
                    self.item_rect["w"] = int(pos.x() - self.btn_press_pos.x())
                    self.item_rect["h"] = int(self.btn_press_pos.y() - pos.y())
                else:
                    self.item_rect["x"] = int(self.btn_press_pos.x())
                    self.item_rect["y"] = int(self.btn_press_pos.y())
                    self.item_rect["w"] = int(pos.x() - self.btn_press_pos.x())
                    self.item_rect["h"] = int(pos.y() - self.btn_press_pos.y())
            self.set_item_rect()

        elif self.current_model[0] == Shape.LINE:
            self.item_line["actionX1"] = int(self.btn_press_pos.x())
            self.item_line["actionY1"] = int(self.btn_press_pos.y())
            self.item_line["actionX2"] = int(pos.x())
            self.item_line["actionY2"] = int(pos.y())
            self.set_item_line()

    def _vertex_moving(self, pos):
        if self.selected_vertex():
            self.bounded_move_vertex(pos)
            self.shape_moved.emit()
            self.repaint()
        elif self.selected_shape and self.prev_point:
            self.override_cursor(CURSOR_MOVE)
            self.bounded_move_shape(self.selected_shape, pos)
            # self.shape_moved.emit()
            self.repaint()

        self.point_graph_index = 1
        if self.label_flag is True:
            return

        select_shape = self.h_shape
        if select_shape is None:
            return

        if select_shape.shape_name == Shape.RECT:
            point1 = select_shape.points[0]
            point2 = select_shape.points[1]
            point3 = select_shape.points[2]
            point4 = select_shape.points[3]

            beginPointX = min(point1.x(), point2.x(), point3.x(), point4.x())
            beginPointY = min(point1.y(), point2.y(), point3.y(), point4.y())
            endPointX = max(point1.x(), point2.x(), point3.x(), point4.x())
            endPointY = max(point1.y(), point2.y(), point3.y(), point4.y())

            self.item_rect["x"] = int(beginPointX)
            self.item_rect["y"] = int(beginPointY)
            self.item_rect["w"] = int(endPointX - beginPointX)
            self.item_rect["h"] = int(endPointY - beginPointY)

            if select_shape in self.shape_tree.keys():
                self.set_item_rect(self.shape_tree[select_shape])
        elif select_shape.shape_name == Shape.LINE:
            point1 = select_shape.points[0]
            point2 = select_shape.points[1]

            self.item_line["actionX1"] = int(point1.x())
            self.item_line["actionY1"] = int(point1.y())
            self.item_line["actionX2"] = int(point2.x())
            self.item_line["actionY2"] = int(point2.y())

            if select_shape in self.shape_tree.keys():
                self.set_item_line(self.shape_tree[select_shape])
        elif select_shape.shape_name == Shape.POINT:
            point = select_shape.points[0]
            if 'actionX' in self.item_point.keys():
                self.item_point["actionX"] = int(point.x())
                self.item_point["actionY"] = int(point.y())
            elif 'x' in self.item_point.keys():
                self.item_point["x"] = int(point.x())
                self.item_point["y"] = int(point.y())

            if select_shape in self.shape_tree.keys():
                self.set_item_point(self.shape_tree[select_shape])

    def _handle_right_button_move(self, pos):
        """ 右键按住移动

        :param pos:
        :return:
        """
        if self.selected_shape_copy and self.prev_point:
            self.override_cursor(CURSOR_MOVE)
            self.bounded_move_shape(self.selected_shape_copy, pos)
            self.repaint()
        elif self.selected_shape:
            self.selected_shape_copy = self.selected_shape.copy()
            self.repaint()

    def _draw_shape(self, pos):
        """ 绘制形状中

        :param pos:
        :return:
        """
        self.override_cursor(CURSOR_DRAW)
        if len(self.current_model) > 0 and self.current_model[0] == Shape.GRAPH:
            return
        if self.current:
            self._polygon_drawing(pos)
        else:
            self.prev_point = pos
        self.repaint()

    def _draw_label(self, pos):
        """ 绘制标签中

        :param pos:
        :return:
        """
        self.override_cursor(CURSOR_DRAW)
        if self.current:
            self.__check_pos_and_color(pos)
        else:
            self.prev_point = pos
        self.repaint()

    def _high_light_shapes(self, visible_shapes, pos):
        """ 高亮形状或顶点

        :param visible_shapes:
        :param pos:
        :return:
        """
        for shape in reversed(visible_shapes):
            # Look for a nearby vertex to highlight. If that fails,z
            # check if we happen to be inside a shape.
            index = shape.nearest_vertex(pos, self.epsilon / self.scale)
            if index is not None:
                if self.selected_vertex():
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = index, shape
                shape.highlight_vertex(index, shape.MOVE_VERTEX)
                self.override_cursor(CURSOR_POINT)
                self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.contains_point(pos):
                if self.selected_vertex():
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = None, shape
                self.setToolTip(
                    "Click & drag to move shape '%s'" % shape.label)
                self.setStatusTip(self.toolTip())
                self.override_cursor(CURSOR_GRAB)
                self.update()
                break

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        if self.is_service_running():
            return

        if self.mouse_flag is False:
            return

        self.mouse_move_flag = True

        if self.pixmap is None:
            return

        pos = self.transformPos(ev.pos())

        # Update coordinates in status bar if image is opened
        if not self.pixmap.isNull():
            self.ui.labelCoordinates.setText('X: %d; Y: %d' % (pos.x(), pos.y()))

        # segment label
        if self.segment():
            self._draw_label(pos)
            return

        # Polygon drawing.
        if self.drawing():
            self._draw_shape(pos)
            return

        # Polygon copy moving.
        if Qt.RightButton & ev.buttons():
            self._handle_right_button_move(pos)
            return

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            self._vertex_moving(pos)
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        visible_shapes = [s for s in self.shapes if self.is_visible(s)]
        if visible_shapes:
            self._high_light_shapes(visible_shapes, pos)
        else:  # Nothing found, clear highlights, reset state.
            if self.h_shape:
                self.h_shape.highlight_clear()
                self.update()
            self.h_vertex, self.h_shape = None, None
            self.override_cursor(CURSOR_DEFAULT)

        if self.ui_graph is not None:
            self._explore_result_graph(pos)

    def _explore_result_graph(self, pos):
        # first: if there is a edge nearby, highLight it and unhighLight node image
        edge = self.ui_graph.nearest_edge(pos.x(), pos.y(), self.epsilon / self.scale)
        if edge is not None:
            self.ui_graph.set_highlight_edge(edge)
            self.ui_graph.clear_highlight_node()
        else:
            self.ui_graph.clear_high_light_edge()
            # second: find UI Image
            node = self.ui_graph.nearest_node(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
            if node is not None:
                self.ui_graph.set_high_light_node(node)
            else:
                self.ui_graph.clear_highlight_node()

        self.update()

    def _dclick_save_image_event(self, ev):
        if ev.button() == Qt.LeftButton:
            if len(self.current_model) == 0 and self.mode == self.CREATE:
                self.mode = self.EDIT
                self.save_pixmap()

    def _dclick_ui_explore_event(self, ev):
        pos = self.transformPos(ev.pos())

        if self.ui_graph is not None:
            # first: if there is a  edge nearby, highLight it and show the node images
            edge = self.ui_graph.nearest_edge(pos.x(), pos.y(), self.epsilon / self.scale)
            if edge is not None:
                self.ui_graph.set_select_edge(edge)
                self.ui_graph.set_highlight_edge(edge)
            else:
                # second: if there is a node nearby, highLight it and show the node image
                node = self.ui_graph.nearest_node(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
                if node is not None:
                    self.ui_graph.set_select_node(node)
                    self.ui_graph.set_high_light_node(node)
                    self.ui_graph.set_show_node_image(True)
                else:
                    self.ui_graph.clear_select_node()
                    self.ui_graph.clear_highlight_node()
                    self.ui_graph.clear_select_edge()
                    self.ui_graph.clear_high_light_edge()

            self.repaint()

        if self.mouse_flag is False:
            return

        selected_shape = False
        for shape in self.shapes:
            if shape.selected:
                selected_shape = shape
                break

        if selected_shape:
            label_text = self.label_dialog.pop_up()
            if label_text is None or label_text == "":
                return

            if selected_shape in self.shape_tree.keys():
                label_tree_item = self.shape_tree[selected_shape]
                if label_tree_item:
                    # 更新画布和右树的标签，并更新item_shape的映射
                    old_label_text = label_tree_item.text(0)
                    if old_label_text != label_text:
                        if old_label_text in self.item_shape and selected_shape in self.item_shape[old_label_text]:
                            self.item_shape[old_label_text].remove(selected_shape)

                        if label_text not in self.item_shape.keys():
                            self.item_shape[label_text] = list()

                        self.item_shape[label_text].append(selected_shape)
                        selected_shape.set_label(label_text)
                        label_tree_item.setText(0, label_text)
                        self.update()

    def mouseDoubleClickEvent(self, ev):
        if self.is_service_running():
            return

        mode = tree_mgr.get_mode()
        logger.debug("mode is %s", mode)

        if mode in [Mode.UI, Mode.SCENE, Mode.AI]:
            self._dclick_save_image_event(ev)

        elif mode in [Mode.UI_AUTO_EXPLORE]:
            self._dclick_ui_explore_event(ev)

        else:
            logger.debug("invalid double click event")

    def mousePressEvent(self, ev):
        if self.is_service_running():
            return

        for shape in self.shapes:
            shape.selected = False

        if self.mouse_flag is False:
            return

        if self.pixmap is None:
            return

        self.mouse_move_flag = True
        pos = self.transformPos(ev.pos())

        if self.segment():
            logger.debug("mouse press event...........")
            self.handle_drawing(pos)
            return

        if ev.button() == Qt.LeftButton:
            if self.drawing():
                self.shapes_num = len(self.shapes)

                if len(self.current_model) == 0:
                    return
                if self.current_model[0] in [Shape.POINT]:
                    return
                self.handle_drawing(pos)
                self.btn_press_pos = pos
            else:
                self.selectShapePoint(pos)
                if self.ui_graph is not None:
                    self._explore_graph_mouse_press(pos)

                self.prev_point = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            # if self.label_flag is True:
            mode = tree_mgr.get_mode()
            if mode == Mode.UI_AUTO_EXPLORE and self.selected_shape is not None:
                self.right_menu.addAction(self.action_delete_shape)
                self.right_menu.exec_(QCursor.pos())

            self.prev_point = pos
            self.repaint()

    def _explore_graph_mouse_press(self, pos):
        # first select edge
        edge = self.ui_graph.nearest_edge(pos.x(), pos.y(), self.epsilon / self.scale)
        if edge is None:
            # if there is no edge nearby, may be this is a new node
            node = self.ui_graph.nearest_node(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
            self.ui_graph.set_select_node(node)
            self.ui_graph.set_show_node_image(False)

        # clear previous selected edge
        self.ui_graph.clear_select_edge()

    def _record_label_info(self, label_text):
        # 获取右树的所有顶层节点
        nodes = get_tree_top_nodes(self.ui.tree_widget_right)

        # 找到名称未"labels"的节点
        label_tree_item = None
        for node in nodes:
            if node.text(0) == 'labels':
                label_tree_item = node
        if label_tree_item is None:
            return

        # 创建一个标签节点，记录标记的样本的名称，位置(x,y,w,h)
        shape = self.shapes[-1]
        points = shape.points
        top_left = points[0]
        x0 = int(top_left.x())
        y0 = int(top_left.y())
        down_right = points[2]
        x1 = int(down_right.x())
        y1 = int(down_right.y())

        if x1 == x0 or y1 == y0:
            return

        sub_item = create_tree_item(key=label_text)
        label_tree_item.addChild(sub_item)

        sub_item_x = create_tree_item(key='x', value=x0)
        sub_item_y = create_tree_item(key='y', value=y0)
        sub_item_w = create_tree_item(key='w', value=x1 - x0)
        sub_item_h = create_tree_item(key='h', value=y1 - y0)
        sub_item.addChild(sub_item_x)
        sub_item.addChild(sub_item_y)
        sub_item.addChild(sub_item_w)
        sub_item.addChild(sub_item_h)
        shape.set_label(label_text)

        self.set_rect_tree_item(sub_item)
        self.set_editing()
        self.shape_tree[shape] = sub_item
        self.update()

    def _create_label(self, evt_pos):
        """ 框选对象

        :return:
        """
        pre_shape_number = len(self.shapes)
        if self.current:  # 上一个按下的位置应是在加载的图片的范围内
            pos = self.transformPos(evt_pos)
            self.handle_drawing(pos)
        if len(self.shapes) == pre_shape_number:
            return
        label_text = self.label_dialog.pop_up()
        if label_text is None or label_text == "":
            if len(self.shapes) > 0:
                self.shapes.pop()
            self.update()
            return
        self._record_label_info(label_text)

    def _handle_right_button_up(self, evt_pos):
        """ 右键释放

        :param evt_pos:
        :return:
        """
        if self.selected_vertex():
            self.right_menu.exec_(QCursor.pos())
            return

        menu = self.menus[bool(self.selected_shape_copy)]
        self.restore_cursor()
        if not menu.exec_(self.mapToGlobal(evt_pos)) \
                and self.selected_shape_copy:
            # Cancel the move by deleting the shadow copy.
            self.selected_shape_copy = None
            self.repaint()

    def _handle_operation_on_device(self, evt_pos):
        """ 将画布上的操作下发到设备或窗口执行

        :return:
        """
        geometry = self.dev_toolbar.geometry()
        dev_l = geometry.x()
        dev_t = geometry.y()
        dev_r = dev_l + geometry.width()
        dev_b = dev_t + geometry.height()
        x = evt_pos.x()
        y = evt_pos.y()
        if dev_l <= x <= dev_r and dev_t <= y <= dev_b:
            return

        # 正在绘图过程，不下发操作
        if self.drawing() and self.get_pixmap() is not None:
            return

        pos = self.transformPos(evt_pos)

        if self.prev_point == pos:
            if g_app_context.get_info('enable_device_operation', False):
                if self._sample_tree_item:
                    sample_img_dir = self._sample_tree_item.text(2)
                    if sample_img_dir:
                        img_path = os.path.join(sample_img_dir, "sample_%s.jpg" % int(time.time()))
                        img_data = self.__data_source.get_frame()
                        if img_data is not None:
                            cv2.imwrite(img_path, img_data)

                        # 先清除之前的节点
                        sub_nodes = get_sub_nodes(self._sample_tree_item)
                        for sub_node in sub_nodes:
                            self._sample_tree_item.removeChild(sub_node)

                        get_file_list(sample_img_dir, self._sample_tree_item, 1)
                        self._sample_tree_item.setExpanded(True)

            kwargs = dict()
            kwargs[DeviceActionParamName.X] = pos.x()
            kwargs[DeviceActionParamName.Y] = pos.y()
            self.__data_source.do_action(DeviceActionType.CLICK, **kwargs)
        else:
            kwargs = dict()
            kwargs[DeviceActionParamName.FROM_X] = self.prev_point.x()
            kwargs[DeviceActionParamName.FROM_Y] = self.prev_point.y()
            kwargs[DeviceActionParamName.TO_X] = pos.x()
            kwargs[DeviceActionParamName.TO_Y] = pos.y()
            self.__data_source.do_action(DeviceActionType.SLIDE, **kwargs)

    def _create_shape(self, evt_pos):
        """ 创建形状

        :param evt_pos:
        :return:
        """
        pos = self.transformPos(evt_pos)
        if self.current_model[0] == Shape.LINE:
            self.handle_drawing_line(pos)
            if len(self.line_tree_item) > 0 and len(self.shapes) > 0:
                self.shape_tree[self.shapes[-1]] = self.line_tree_item[0]
        elif self.current_model[0] == Shape.RECT:
            self.handle_drawing(pos)
            if len(self.rect_tree_item) > 0 and len(self.shapes) > 0:
                self.shape_tree[self.shapes[-1]] = self.rect_tree_item[0]
        elif self.current_model[0] == Shape.POINT:
            if 'actionX' in self.item_point.keys():
                self.item_point["actionX"] = int(pos.x())
                self.item_point["actionY"] = int(pos.y())
            elif 'x' in self.item_point.keys():
                self.item_point["x"] = int(pos.x())
                self.item_point["y"] = int(pos.y())

            self.set_item_point()
            shape = Shape(name=Shape.POINT)
            shape.add_point(QPoint(pos.x(), pos.y()))
            self.shapes.append(shape)
            self.shape_tree[self.shapes[-1]] = self.point_tree_item[0]
            self.repaint()

    def _handle_left_button_up(self, evt_pos):
        """ 处理左键释放事件

        :param evt_pos:
        :return:
        """
        if self.selected_shape:
            if self.selected_vertex():
                self.override_cursor(CURSOR_POINT)
            else:
                self.override_cursor(CURSOR_GRAB)
            return

        if len(self.current_model) > 0:
            if self.drawing():
                self._create_shape(evt_pos)

            if len(self.shapes) - self.shapes_num == 1:
                if self.current_model[0] == Shape.LINE:
                    self.line_tree_item.pop(0)
                elif self.current_model[0] == Shape.RECT:
                    self.rect_tree_item.pop(0)
                else:
                    self.point_tree_item.pop(0)

                if self.current_model[0] not in [Shape.POLYGONLINE, Shape.GRAPH]:
                    self.current_model.pop(0)

        if g_app_context.get_info("phone", False) and self.__data_source.device and evt_pos:  # 如果是连接设备，并且是设备状态
            self._handle_operation_on_device(evt_pos)

    def mouseReleaseEvent(self, ev):
        if self.is_service_running():
            return

        if self.mouse_flag is False:
            return

        self.mouse_move_flag = True

        evt_pos = ev.pos()

        if self.segment():
            self._create_label(evt_pos)
            return

        if ev.button() == Qt.RightButton:
            self._handle_right_button_up(evt_pos)

        if ev.button() == Qt.LeftButton:
            self._handle_left_button_up(evt_pos)

    def save_pixmap(self):
        if self.ui is None:
            logger.error("ui is none, to trees information")
            return

        image_node = None
        node_index = -1
        right_tree = self.ui.tree_widget_right
        node = right_tree.currentItem()

        if node is None or node.childCount() == 0:
            # 如果当前节点为空，获取右树的所有子节点
            for index in range(right_tree.topLevelItemCount()):
                sub_node = right_tree.topLevelItem(index)
                if sub_node.text(0) in image_path_keys:
                    image_node = sub_node
                    node_index = index
                    break
        else:
            # 否则获取当前节点的所有子节点
            node_text = node.text(0)
            if node_text == 'refer':
                template_nodes = get_item_by_type(ITEM_TYPE_TEMPLATE, node)
                if template_nodes and len(template_nodes) == 1:
                    template_node = template_nodes[0]
                    sub_nodes = get_sub_nodes(template_node)
                    for index, sub_node in enumerate(sub_nodes):
                        sub_node_text = sub_node.text(0)
                        if sub_node_text in image_path_keys:
                            image_node = sub_node
                            node_index = index
                            break
            else:
                sub_nodes = get_sub_nodes(node)
                for index, sub_node in enumerate(sub_nodes):
                    sub_node_text = sub_node.text(0)
                    if sub_node_text in image_path_keys:
                        image_node = sub_node
                        node_index = index
                        break

        if image_node is None:
            logger.error("not find result node, which key in image_path_keys")
            return

        # 获取当前画布的图像
        pixmap = self.get_pixmap()
        cv_image = qtpixmap_to_cvimg(pixmap)

        first_child = right_tree.topLevelItem(0)

        # 重构图像名称：类型_element名称_当前时间.jpg
        element_name = first_child.text(1)
        element_type = first_child.text(2)
        # time_number = int(time.time())
        img_name = '{}_{}_{}.jpg'.format(element_type, element_name, node_index)

        # 记录图像：project/游戏名称/data/图像名称
        project_data_path = ProjectDataManager().get_project_data_path()
        image_path = os.path.join(project_data_path, img_name)
        logger.debug("write image %s", image_path)
        cv2.imwrite(image_path, cv_image)
        image_node.setText(1, image_path)

    def handle_drawing_line(self, pos):
        if self.current and self.current.reach_max_points() is False:
            targetPos = self.line[1]
            self.current.add_point(targetPos)
            self.finalise()
        elif not self.out_of_pixmap(pos):
            self.current = Shape()
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawing_polygon.emit(True)
            self.update()

    def handle_drawing(self, pos):
        if self.current and self.current.reach_max_points() is False:
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()
            self.current.add_point(QPointF(maxX, minY))
            self.current.add_point(targetPos)
            self.current.add_point(QPointF(minX, maxY))
            self.finalise()
        elif not self.out_of_pixmap(pos):
            self.current = Shape()
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawing_polygon.emit(True)
            self.update()

    def set_hiding(self, enable=True):
        self.__hide_background = self.hide_background if enable else False

    def can_close_shape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selected_shape = shape
        self.set_hiding()
        self.selection_changed.emit(True)
        self.update()

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape()
        if self.selected_vertex():  # A vertex is marked for selection.
            index, shape = self.h_vertex, self.h_shape
            shape.highlight_vertex(index, shape.MOVE_VERTEX)
            self.selectShape(shape)
            return

        index = len(self.shapes) - 1
        for shape in reversed(self.shapes):
            if self.is_visible(shape) and shape.contains_point(point):
                self.selectShape(shape)
                self.calculateOffsets(shape, point)
                return
            index -= 1

    def calculateOffsets(self, shape, point):
        rect = shape.bounding_rect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def snapPointToCanvas(self, x, y):
        """
        Moves a point x,y to within the boundaries of the canvas.
        :return: (x,y,snapped) where snapped is True if x or y were changed, False if not.
        """
        if x < 0 or x > self.pixmap.width() or y < 0 or y > self.pixmap.height():
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.pixmap.width())
            y = min(y, self.pixmap.height())
            return x, y, True

        return x, y, False

    def bounded_move_vertex(self, pos):
        index, shape = self.h_vertex, self.h_shape
        point = shape[index]
        if self.out_of_pixmap(pos):
            pos = self.intersectionPoint(point, pos)

        shift_pos = pos - point
        shape.move_vertex_by(index, shift_pos)

        if shape.shape_name == shape.RECT:
            lindex = (index + 1) % 4
            rindex = (index + 3) % 4
            lshift = None
            rshift = None
            if index % 2 == 0:
                rshift = QPointF(shift_pos.x(), 0)
                lshift = QPointF(0, shift_pos.y())
            else:
                lshift = QPointF(shift_pos.x(), 0)
                rshift = QPointF(0, shift_pos.y())
            shape.move_vertex_by(rindex, rshift)
            shape.move_vertex_by(lindex, lshift)

    def bounded_move_shape(self, shape, pos):
        if self.out_of_pixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.out_of_pixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.out_of_pixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        # self.calculateOffsets(self.selected_shape, pos)
        dp = pos - self.prev_point
        if dp:
            shape.move_by(dp)
            self.prev_point = pos
            return True
        return False

    def deSelectShape(self):
        if self.selected_shape:
            self.selected_shape.selected = False
            self.selected_shape = None
            self.set_hiding(False)
            self.selection_changed.emit(False)
            self.update()

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prev_point = point
        if not self.bounded_move_shape(shape, point - offset):
            self.bounded_move_shape(shape, point + offset)

    def scale_window(self):
        if None not in [self.ui, self.pixmap]:
            ui_w = self.ui.graph_view.width()
            ui_h = self.ui.graph_view.height()
            ui_a = ui_w / ui_h

            img_w = self.pixmap.width()
            img_h = self.pixmap.height()
            img_a = img_w / img_h
            value = 1
            if img_a >= ui_a:
                value = ui_w / img_w
            else:
                value = ui_h / img_h

            self.scale = value
            self.adjustSize()

    def paintEvent(self, event):
        if not self.pixmap:
            return super(UICanvas, self).paintEvent(event)
        # self.scale_window()

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self.__hide_background) and self.is_visible(shape):
                shape.fill = shape.selected or shape == self.h_shape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selected_shape_copy:
            self.selected_shape_copy.paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawing_rect_color)
            brush = QBrush(Qt.BDiagPattern)
            p.setBrush(brush)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prev_point.isNull() and not self.out_of_pixmap(self.prev_point):
            if len(self.current_model) > 0:
                p.setPen(QColor(0, 0, 0))
                p.drawLine(self.prev_point.x(), 0, self.prev_point.x(), self.pixmap.height())
                p.drawLine(0, self.prev_point.y(), self.pixmap.width(), self.prev_point.y())

        if self.segment() and not self.prev_point.isNull() and not self.out_of_pixmap(self.prev_point):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prev_point.x(), 0, self.prev_point.x(), self.pixmap.height())
            p.drawLine(0, self.prev_point.y(), self.pixmap.width(), self.prev_point.y())

        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(pal)

        if self.ui_graph is not None:
            self.ui_graph.paint(p)

        p.end()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        if self.pixmap is None:
            return QPointF(0, 0)

        s = self.scale
        area = super(UICanvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def out_of_pixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    def finalise(self):
        assert self.current
        # 曲线闭合的判断
        # if self.current.points[0] == self.current.points[-1]:
        #     logger.info("**************current points {} points length {}*************".format(self.current,
        #     len(self.current.points)))
        #     self.current = None
        #     self.drawing_polygon.emit(False)
        #     self.update()
        #     return

        self.current.close()
        if len(self.current_model) > 0:
            self.current.set_shape_name(self.current_model[0])
        self.shapes.append(self.current)
        self.current = None
        self.set_hiding(False)
        self.new_shape.emit()
        self.update()

    def closeEnough(self, p1, p2):
        # d = distance(p1 - p2)
        # m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        _, i, (x, y) = min(self.intersecting_edges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            return QPointF(min(max(0, x2), max(x3, x4)), y3)

        # Ensure the labels are within the bounds of the image. If not, fix them.
        x, y, _ = self.snapPointToCanvas(x, y)
        return QPointF(x, y)

    @staticmethod
    def intersecting_edges(x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                yield d, i, (x, y)

    def sizeHint(self):
        # These two, along with a call to adjustSize are required for the
        # scroll area.
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(UICanvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
            else:
                v_delta = 0
        else:
            delta = ev.angleDelta()
            v_delta = delta.y()
        if self.segment():
            if v_delta > 0:
                self.cursor_width += 2
                if self.cursor_width > 30:
                    self.cursor_width = 30
            else:
                self.cursor_width -= 2
                if self.cursor_width < 5:
                    self.cursor_width = 5

            self.repaint()
            return
        if self.editing():
            if v_delta > 0:
                self.scale += 0.05

                self.adjustSize()
                self.update()
            else:
                self.scale -= 0.05
                self.adjustSize()
                self.update()
            return

        if self.ui_graph is not None:
            if v_delta > 0:
                self.scale += 0.05
                print("canvas scale .... {}".format(self.scale))
                self.adjustSize()
                self.update()
            else:
                self.scale -= 0.05
                self.adjustSize()
                self.update()
            return

        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.zoom_request.emit(v_delta)
        else:
            v_delta and self.scroll_request.emit(v_delta, Qt.Vertical)
            h_delta and self.scroll_request.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape:
            # print('ESC press, label_flag {}, self.mode {}'.format(self.label_flag, self.mode))
            self.label_flag = False
            if self.mode == self.EDIT:
                self.mode = self.LABEL
                self.label_flag = True
            elif self.mode == self.LABEL:
                self.mode = self.EDIT

        elif key == Qt.Key_Return and self.can_close_shape():
            self.finalise()
        elif key == Qt.Key_Left and self.selected_shape:
            self.move_one_pixel('Left')
        elif key == Qt.Key_Right and self.selected_shape:
            self.move_one_pixel('Right')
        elif key == Qt.Key_Up and self.selected_shape:
            self.move_one_pixel('Up')
        elif key == Qt.Key_Down and self.selected_shape:
            self.move_one_pixel('Down')
        elif key == Qt.Key_Shift:
            self.pix_level_flag = True
        elif key == Qt.Key_Z:
            if self.label_flag is True:
                if self.ui.actionSwitch.isChecked():
                    self.ui.actionSwitch.setChecked(False)
                else:
                    self.ui.actionSwitch.setChecked(True)
                    self.set_editing()

    def keyReleaseEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Shift:
            self.pix_level_flag = False

    def move_one_pixel(self, direction):
        # print(self.selected_shape.points)
        if direction == 'Left' and not self.move_out_of_bound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selected_shape.points[0] += QPointF(-1.0, 0)
            self.selected_shape.points[1] += QPointF(-1.0, 0)
            self.selected_shape.points[2] += QPointF(-1.0, 0)
            self.selected_shape.points[3] += QPointF(-1.0, 0)
        elif direction == 'Right' and not self.move_out_of_bound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selected_shape.points[0] += QPointF(1.0, 0)
            self.selected_shape.points[1] += QPointF(1.0, 0)
            self.selected_shape.points[2] += QPointF(1.0, 0)
            self.selected_shape.points[3] += QPointF(1.0, 0)
        elif direction == 'Up' and not self.move_out_of_bound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selected_shape.points[0] += QPointF(0, -1.0)
            self.selected_shape.points[1] += QPointF(0, -1.0)
            self.selected_shape.points[2] += QPointF(0, -1.0)
            self.selected_shape.points[3] += QPointF(0, -1.0)
        elif direction == 'Down' and not self.move_out_of_bound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selected_shape.points[0] += QPointF(0, 1.0)
            self.selected_shape.points[1] += QPointF(0, 1.0)
            self.selected_shape.points[2] += QPointF(0, 1.0)
            self.selected_shape.points[3] += QPointF(0, 1.0)
        self.shape_moved.emit()
        self.repaint()

    def move_out_of_bound(self, step):
        points = [p1 + p2 for p1, p2 in zip(self.selected_shape.points, [step] * 4)]
        return True in map(self.out_of_pixmap, points)

    def load_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.mouse_flag = True
        self.repaint()
        scale_view = 1
        view_w = 1
        view_h = 1

        if self.ui is not None:
            view_w = self.ui.graph_view.width()
            view_h = self.ui.graph_view.height()
            scale_view = view_w / view_h
        try:
            pixmap_w = self.pixmap.width()
            pixmap_h = self.pixmap.height()
            if pixmap_h == 0:
                return
            scale_pixmap = pixmap_w / pixmap_h
            self.scale = view_w / pixmap_w if scale_pixmap >= scale_view else view_h / pixmap_h
            self.adjustSize()
            self.update()
        except RuntimeError as err:
            logger.error("Error is %s", err)

    def get_scale(self):
        return self.scale

    def load_shapes(self, shapes):
        self.shapes = shapes
        self.current = None
        self.repaint()

    def override_cursor(self, cursor):
        self._cursor = cursor
        # 不更改鼠标形状
        QApplication.changeOverrideCursor(cursor)

    @staticmethod
    def restore_cursor():
        QApplication.restoreOverrideCursor()

    def reset_state(self):
        self.restore_cursor()
        self.pixmap = None
        # self.mode = self.CREATE
        self.mouse_flag = False
        self.selected_shape = None
        self.current_model.clear()
        self.rect_tree_item.clear()
        self.line_tree_item.clear()
        self.point_tree_item.clear()
        self.update()

    def reset_shapes(self):
        self.mouse_flag = True

        self.selected_shape = None
        self.current_model.clear()
        self.rect_tree_item.clear()
        self.line_tree_item.clear()
        self.point_tree_item.clear()

    def create_process_bar(self, title, label, min_value, max_value):
        self.process_bar = ProgressBarDialog(title=title, label=label,
                                             minValue=min_value, maxValue=max_value)

    def set_bar_cur_value(self, value):
        self.process_bar.set_value(value)

    def close_bar(self):
        self.process_bar.close_bar()
        self.process_bar.reset_bar()

    def show_img(self, image_name):
        frame = QImage(image_name)
        pix = QPixmap.fromImage(frame)
        self.load_pixmap(pix)


canvas = UICanvas()


def reset_canvas_roi(node):
    if node is None or node.childCount() == 0:
        return None
    x = int(node.child(0).text(1))
    y = int(node.child(1).text(1))
    w = int(node.child(2).text(1))
    h = int(node.child(3).text(1))
    points = [Point(x, y), Point(x + w, y), Point(x + w, y + h), Point(x, y + h)]
    for point in points:
        point.x, point.y, _ = canvas.snapPointToCanvas(point.x, point.y)

    shape = create_shape(points=points, closed=True)
    return shape


def reset_canvas_action(node):
    shape = None
    if node.childCount() in[len(Click_Key), len(Drag_Check_Key)]:
        # click: "actionX", "actionY", "actionThreshold",
        # "actionTmplExpdWPixel", "actionTmplExpdHPixel", "actionROIExpdWRatio", "actionROIExpdHRatio"
        x = int(node.child(0).text(1))
        y = int(node.child(1).text(1))
        canvas.set_point_tree_item(node)
        shape = create_shape([Point(x, y)])
        # shapes.append(shape)
        canvas.shape_tree[shape] = node
    elif node.childCount() == len(Drag_Key):
        # "actionX1", "actionY1", "actionThreshold1",
        # "actionTmplExpdWPixel1", "actionTmplExpdHPixel1", "actionROIExpdWRatio1", "actionROIExpdHRatio1",
        # "actionX2", "actionY2", "actionThreshold2",
        #  "actionTmplExpdWPixel2", "actionTmplExpdHPixel2", "actionROIExpdWRatio2", "actionROIExpdHRatio2"
        x1 = int(node.child(0).text(1))
        y1 = int(node.child(1).text(1))
        x2 = int(node.child(len(Drag_Key) / 2).text(1))
        y2 = int(node.child(len(Drag_Key) / 2 + 1).text(1))
        canvas.set_line_tree_item(node)
        if x1 >= 0 and y1 >= 0 and x2 >= 0 and y2 >= 0:
            canvas.set_editing()
            shape = create_shape([Point(x1, y1), Point(x2, y2)])
            canvas.shape_tree[shape] = node
    else:
        logger.info("unknown action which has %s count of children", node.childCount())
    return shape


def update_rect_shapes(node):
    if node is None:
        return
    if node.childCount() < 4:
        return

    key_shape = None
    for key, value in canvas.shape_tree.items():
        if value == node:
            key_shape = key
            break

    if key_shape is not None:
        canvas.shape_tree.pop(key_shape)
        x = int(node.child(0).text(1))
        y = int(node.child(1).text(1))
        w = int(node.child(2).text(1))
        h = int(node.child(3).text(1))
        points = [Point(x, y), Point(x + w, y), Point(x + w, y + h), Point(x, y + h)]
        new_shape = create_shape(points=points, closed=True)
        canvas.shape_tree[new_shape] = node
        if key_shape in canvas.shapes:
            canvas.shapes.remove(key_shape)
        canvas.shapes.append(new_shape)
        canvas.update()
