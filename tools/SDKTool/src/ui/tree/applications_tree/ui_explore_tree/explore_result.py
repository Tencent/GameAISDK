# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import json
import math
import logging
import cv2
import numpy as np
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt

from .graph import UIGraph, UIGRAPH
from ....canvas.ui_canvas import canvas
from ....dialog.tip_dialog import show_warning_tips
from ....main_window.tool_window import ui
from .....common.define import UMING_TTC
from .....common.utils import get_font
from ....utils import cvimg_to_qtimg

platform = sys.platform
plt.rcParams['font.sans-serif'] = get_font()  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False   # 用来正常显示负号


class ExploreResult(object):
    def __init__(self, path=None):
        self.__logger = logging.getLogger('sdktool')
        # self.__canvas = canvas
        self.__ui = ui
        self.__image_list = []
        self.__image_index = -1
        self.__explore_ret_path = path
        self.__table_widget = None

    def set_path(self, path):
        self.__explore_ret_path = path

    @staticmethod
    def load_image_file(ui_graph):
        w, h = ui_graph.get_painter_size()
        if w > 0 and h > 0:
            max_w = max(canvas.geometry().width(), w)
            max_h = max(canvas.geometry().height(), h)

            img_data = cv2.imread("Resource/White.jpeg")
            if img_data is None:
                raise Exception('Resource/White.jpeg is not found')

            img_data = cv2.resize(img_data, (max_w, max_h))
            qtimg = cvimg_to_qtimg(img_data)

            canvas.load_pixmap(qtimg)

        canvas.add_ui_graph(ui_graph)

        canvas.current_model.append(UIGRAPH)
        canvas.update()

        # 优化显示，否则当界面元素过多时，元素显示很小
        if canvas.scale < 1:
            canvas.scale = 1.0
            canvas.adjustSize()
            canvas.update()

    def ui_graph(self):
        file_list = os.listdir(self.__explore_ret_path)
        img_list = [item for item in file_list if item.split('.')[1] in ['jpg']]
        json_list = [item for item in file_list if '.json' in item]
        if 0 in [len(file_list), len(img_list), len(json_list)]:
            show_warning_tips("files count wrong, img count {}, json count{}".format(len(img_list), len(json_list)))
            return

        image_label_dict = dict()
        for item in img_list:
            key = item.split('.')[0]
            jsonfile = "{}.json".format(key)
            if jsonfile in json_list:
                image_label_dict[key] = dict()
                image_label_dict[key]["image"] = item
                image_label_dict[key]["label"] = jsonfile

        self.__logger.info("images count %s,  json count %s, pairs count %s", len(img_list),
                           len(json_list), len(image_label_dict.keys()))

        ui_graph = UIGraph()
        ui_graph.set_canvas_scale(canvas.get_scale())

        # create graph
        for key, value in image_label_dict.items():
            with open("{0}/{1}".format(self.__explore_ret_path, value.get("label")), 'r') as ui_label_file:
                content = json.load(ui_label_file)
                label_list = content.get("labels")
                cur_image = content.get("fileName")
                if not label_list:
                    self.__logger.error("%s label is none", ui_label_file)
                    continue

                for button in label_list:
                    next_ui = button.get("nextUI")
                    # labelName = button.get("label")

                    number = int(button.get("clickNum"))
                    ui_graph.add_node_button(cur_image, (button.get("x"), button.get("y"),
                                                       button.get("w"), button.get("h")), next_ui, number)
                    # if (nextUI is not '') and (labelName not in ['return']):
                    if next_ui != '':
                        # uiGraph.add_edge(value.get("image"), nextUI)
                        ui_graph.add_edge(cur_image, next_ui)

        self.__logger.info("edges num %s node num %s", len(ui_graph.edges()), len(ui_graph.nodes()))

        for node in ui_graph.nodes():
            img_path = self.__explore_ret_path + '/' + str(node)
            ui_graph.add_node_image(node, img_path)

        ui_graph.process()
        ui_graph.set_text_edit(self.__ui.textEdit)

        # 加载图像文件
        self.load_image_file(ui_graph)

    @staticmethod
    def _plt_set(y_value, x_label, y_label, title):
        y_max_value = math.ceil(max(y_value) * 1.2)
        plt.ylim(0, y_max_value)
        if platform == 'win32':
            plt.xlabel(str(x_label))
            plt.ylabel(str(y_label))
            plt.title(str(title))
            plt.legend()
        else:
            chinesefont = FontProperties(fname=UMING_TTC)
            plt.xlabel(str(x_label), fontproperties=chinesefont)
            plt.ylabel(str(y_label), fontproperties=chinesefont)
            plt.title(str(title), fontproperties=chinesefont)
            plt.legend(prop=chinesefont)
        plt.tight_layout()

    @staticmethod
    def _set_bar(index, height, width, alpha, color, label):
        plt.bar(index, height, width, alpha=alpha, color=color, label=label)

    @staticmethod
    def _set_bar_text(x, y, s, ha='center'):
        plt.text(x, y, s, ha=ha)

    def coverage(self):
        # clear previous figures
        plt.figure(1)
        json_file = self.__explore_ret_path + '/coverage.json'
        if not os.path.exists(json_file):
            self.__logger.error("file %s not exists", json_file)
            return
        try:
            with open(json_file) as f:
                value = json.load(f)
        except IOError as e:
            self.__logger.error("load json file %s failed, err: %s", json_file, e)
            return

        button_value = value.get("button")
        scene_value = value.get("scene")
        if None in [button_value, scene_value]:
            self.__logger.error("read button or scene from file %s failed", json_file)
            return

        plt.cla()
        n_groups = 1
        index = np.arange(n_groups)
        bar_width = 0.3
        _, (ax1, ax2) = plt.subplots(1, 2)
        # ax2 = plt.subplot(1, 2, 2)
        plt.sca(ax2)
        opacity = 0.4

        self._set_bar(index, height=button_value.get("sampleNum"), width=bar_width,
                      alpha=opacity, color='b', label='游戏按钮')
        self._set_bar_text(x=index, y=button_value.get("sampleNum"), s=str(button_value.get("sampleNum")), ha='center')

        self._set_bar(index + bar_width, button_value.get("coverNum"), bar_width, alpha=opacity,
                      color='r', label='探索覆盖')
        self._set_bar_text(x=index + bar_width, y=button_value.get("coverNum"),
                           s=str(button_value.get("coverNum")), ha='center')

        y_value = (button_value.get("sampleNum"), button_value.get("coverNum"))
        self._plt_set(y_value, x_label=str('按钮'), y_label=str('按钮数量'), title=str('按钮覆盖率'))

        # ax1 = plt.subplot(1, 2, 1)
        plt.sca(ax1)
        self._set_bar(index, height=scene_value.get("sampleNum"), width=bar_width,
                      alpha=opacity, color='g', label='游戏场景')
        self._set_bar_text(x=index, y=scene_value.get("sampleNum"), s=str(scene_value.get("sampleNum")), ha='center')

        self._set_bar(index + bar_width, height=scene_value.get("coverNum"), width=bar_width,
                      alpha=opacity, color='y', label='探索覆盖')
        self._set_bar_text(x=index + bar_width, y=scene_value.get("coverNum"),
                           s=str(scene_value.get("coverNum")), ha='center')

        y_value = (scene_value.get("sampleNum"), scene_value.get("coverNum"))
        self._plt_set(y_value, x_label=str('场景'), y_label=str('场景数量'), title=str('场景覆盖率'))

        plt.subplots_adjust(left=0.1, right=0.97, top=0.92, bottom=0.12, wspace=0.31, hspace=0.2)

        name = 'coverage.jpg'
        plt.savefig(name)

        # 加载图像文件
        frame = QImage(name)
        pix = QPixmap.fromImage(frame)
        canvas.load_pixmap(pix)
        canvas.update()
        plt.close(1)

    @staticmethod
    def _set_widget_item(table_widget, name, row=0, col=0, set_edit=True):
        new_item = QTableWidgetItem(name)
        if set_edit:
            new_item.setData(Qt.EditRole, name)
        table_widget.setItem(row, col, new_item)

    def ui_coverage(self):
        json_file = self.__explore_ret_path + '/coverage.json'
        if not os.path.exists(json_file):
            self.__logger.error("file %s not exists", json_file)
            return
        try:
            with open(json_file) as f:
                value = json.load(f)
        except IOError as e:
            self.__logger.error("load json file %s failed, err: %s", json_file, e)
            return

        cover_list = value.get('coverList') or []
        self.__table_widget = QTableWidget()
        self.__table_widget.setSortingEnabled(True)
        self.__table_widget.setRowCount(len(cover_list))
        self.__table_widget.setColumnCount(4)
        self.__table_widget.setHorizontalHeaderLabels(['图像名', '按钮数', '覆盖数', '覆盖率'])
        self.__table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        index = 0
        for item in cover_list:
            self._set_widget_item(self.__table_widget, item.get("fileName"), index, 0, set_edit=False)
            self._set_widget_item(self.__table_widget, int(item.get("sampleNum")), index, 1)
            self._set_widget_item(self.__table_widget, int(item.get("coverNum")), index, 2)
            self._set_widget_item(self.__table_widget, str(item.get("coverage")), index, 3)
            index += 1

        for i in range(self.__ui.graph_view_layout.count()):
            item = self.__ui.graph_view_layout.itemAt(i)
            item.widget().hide()
        # self.__ui.horizontalLayout_4.addWidget(self.__table_widget)
        self.__ui.graph_view_layout.addWidget(self.__table_widget)

    def reset(self):
        if self.__table_widget is not None:
            self.__table_widget.deleteLater()
            self.__table_widget = None

        for i in range(self.__ui.graph_view_layout.count()):
            item = self.__ui.graph_view_layout.itemAt(i)
            item.widget().show()
