# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtCore import Qt, QMetaObject, QSize
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QLabel, QDockWidget, QTextEdit, QSizePolicy, QApplication, QItemDelegate

# app = QApplication(["SdkTool"])

from .sdk_tool import UIMainWindow


class EmptyDelegate(QItemDelegate):
    def __int__(self, parent):
        super(EmptyDelegate, self).__init__(parent)


class ToolWindow(UIMainWindow):
    def __init__(self):
        super(ToolWindow).__init__()
        self.center_widget = None
        self.content_layout = None
        self.tree_widget_left = None
        self.center_layout = None
        self.graph_view_layout = None
        self.graphics_view = None
        self.video_play_layout = None
        self.video_button = None
        self.video_slider = None
        self.video_label = None
        self.textEdit = None
        self.tree_widget_right = None
        self.status_bar = None
        self.tool_bar = None
        self.menu_bar = None
        self.menu_project = None
        self.menu_UI = None
        self.menu_Task = None
        self.menu_Debug = None
        self.menu_debug_UI = None
        self.menu_debug_GameReg = None
        self.menu_PlugIn = None
        self.menu_Tools = None
        self.menu_help = None
        self.tool_bar = None
        self.labelCoordinates = None
        self.canvas = None

        # 非QtDesigner 生成的
        # self.canvas = None

    def setup_ui(self, main_window):
        super().setup_ui(main_window)

        # col: 0,key; 1,value; 2,type; 3,image_path
        self.tree_widget_left.setColumnCount(4)
        self.tree_widget_left.setColumnWidth(0, 200)
        self.tree_widget_left.setColumnHidden(1, True)
        self.tree_widget_left.setColumnHidden(2, True)
        self.tree_widget_left.setColumnHidden(3, True)
        self.tree_widget_left.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget_left.headerItem().setText(0, "")
        self.tree_widget_left.headerItem().setText(1, "")
        self.tree_widget_left.headerItem().setText(2, "")
        self.tree_widget_left.headerItem().setText(3, "")

        # canvas replace TextEdit
        self.graph_view.setWidget(QTextEdit())
        # self.graph_view.setWidget(self.canvas)
        self.graph_view.setWidgetResizable(True)

        self.video_button.hide()
        self.video_slider.hide()
        self.video_label.hide()

        self.text_edit.setMaximumSize(QSize(167700, 167))

        # col: 0,key; 1,value; 2,type; 3,image_path
        self.tree_widget_right.setColumnCount(4)
        self.tree_widget_right.setColumnWidth(0, 200)
        self.tree_widget_right.headerItem().setText(0, "Attribute")
        self.tree_widget_right.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget_right.headerItem().setText(1, "")
        self.tree_widget_right.headerItem().setText(2, "")
        self.tree_widget_right.headerItem().setText(3, "")
        self.tree_widget_right.setMinimumSize(QSize(600, 16777215))
        self.tree_widget_right.setColumnHidden(2, True)
        self.tree_widget_right.setColumnHidden(3, True)
        self.labelCoordinates = QLabel('')
        self.status_bar.addPermanentWidget(self.labelCoordinates)

        dock_tree_widget_left = QDockWidget('', main_window)
        dock_tree_widget_left.setObjectName(u'treeWidgetR')
        dock_tree_widget_left.setWidget(self.tree_widget_left)
        dock_tree_widget_left.setFeatures(QDockWidget.DockWidgetMovable)
        main_window.addDockWidget(Qt.LeftDockWidgetArea, dock_tree_widget_left)

        dock_tree_widget_right = QDockWidget('', main_window)
        dock_tree_widget_right.setObjectName(u'treeWidgetL')
        dock_tree_widget_right.setWidget(self.tree_widget_right)
        dock_tree_widget_right.setFeatures(QDockWidget.DockWidgetMovable)
        main_window.addDockWidget(Qt.RightDockWidgetArea, dock_tree_widget_right)

        self.retranslate_ui(main_window)
        QMetaObject.connectSlotsByName(main_window)

        # 日志框设置为不可编辑
        # 日志框可以拖动，未实现
        self.text_edit.setReadOnly(True)
        dock = QDockWidget('', main_window)
        dock.setFeatures(QDockWidget.DockWidgetMovable|QDockWidget.DockWidgetFloatable)
        dock.setWidget(self.textEdit)
        main_window.addDockWidget(Qt.TopDockWidgetArea, dock)

        self.tree_widget_left.setItemDelegateForColumn(0, EmptyDelegate(self.tree_widget_left))
        self.tree_widget_right.setItemDelegateForColumn(0, EmptyDelegate(self.tree_widget_right))

    def set_ui_canvas(self, canvas):
        self.canvas = canvas
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setSizePolicy(size_policy)
        self.graph_view.setWidget(self.canvas)
        self.graph_view.setWidgetResizable(True)
        self.canvas.update_dev_toolbar()

    def set_widget(self, widget):
        self.graph_view.setWidget(widget)

    def get_canvas(self):
        return self.canvas

    def set_play_button(self, show: bool):
        if show:
            self.video_button.show()
            self.video_slider.show()
            self.video_label.show()
        else:
            self.video_button.hide()
            self.video_slider.hide()
            self.video_label.hide()

    def set_text(self, text: str):
        self.text_edit.setText(text)
        self.text_edit.moveCursor(QTextCursor.End)


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
tool_app = QApplication(["SdkTool"])
ui = ToolWindow()
