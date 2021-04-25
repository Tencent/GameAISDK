# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class UIMainWindow(object):
    def __init__(self):
        self.center_widget = None
        self.whole_layout = None
        self.content_layout = None
        self.tree_widget_left = None
        self.center_layout = None
        self.graph_view_layout = None
        self.graph_view = None
        self.scroll_area_contents = None
        self.video_play_layout = None
        self.video_button = None
        self.video_slider = None
        self.video_label = None
        self.status_bar = None
        self.text_edit = None
        self.tree_widget_right = None
        self.tool_bar = None
        self.menu_bar = None

    def setup_ui(self, main_window):
        main_window.setObjectName("main_window")
        main_window.resize(941, 660)
        main_window.setMinimumSize(QtCore.QSize(180, 157))
        main_window.setMaximumSize(QtCore.QSize(1677401, 16777215))
        self.center_widget = QtWidgets.QWidget(main_window)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.center_widget.sizePolicy().hasHeightForWidth())
        self.center_widget.setProperty("sizePolicy", size_policy)
        self.center_widget.setObjectName("center_widget")
        self.whole_layout = QtWidgets.QHBoxLayout(self.center_widget)
        self.whole_layout.setObjectName("whole_layout")
        self.content_layout = QtWidgets.QHBoxLayout()
        self.content_layout.setObjectName("content_layout")
        self.tree_widget_left = QtWidgets.QTreeWidget(self.center_widget)
        self.tree_widget_left.setObjectName("tree_widget_left")
        self.tree_widget_left.setExpandsOnDoubleClick(False)

        self.content_layout.addWidget(self.tree_widget_left)

        self.center_layout = QtWidgets.QVBoxLayout()
        self.center_layout.setObjectName("center_layout")

        self.graph_view_layout = QtWidgets.QHBoxLayout()
        self.graph_view_layout.setObjectName("graph_view_layout")
        self.graph_view = QtWidgets.QScrollArea(self.center_widget)
        self.graph_view.setWidgetResizable(True)
        self.graph_view.setObjectName("graph_view")
        self.scroll_area_contents = QtWidgets.QWidget()
        self.scroll_area_contents.setGeometry(QtCore.QRect(0, 0, 539, 456))
        self.scroll_area_contents.setObjectName("scroll_area_contents")
        self.graph_view.setWidget(self.scroll_area_contents)
        self.graph_view_layout.addWidget(self.graph_view)
        self.center_layout.addLayout(self.graph_view_layout)
        self.video_play_layout = QtWidgets.QHBoxLayout()
        self.video_play_layout.setObjectName("video_play_layout")
        self.video_button = QtWidgets.QPushButton(self.center_widget)
        self.video_button.setMinimumSize(QtCore.QSize(70, 0))
        self.video_button.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/menu/play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.video_button.setIcon(icon)
        self.video_button.setIconSize(QtCore.QSize(30, 30))
        self.video_button.setObjectName("video_button")
        self.video_play_layout.addWidget(self.video_button)
        self.video_slider = QtWidgets.QSlider(self.center_widget)
        self.video_slider.setMinimumSize(QtCore.QSize(0, 0))
        self.video_slider.setMaximumSize(QtCore.QSize(1677, 167))
        self.video_slider.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.video_slider.setMinimum(0)
        self.video_slider.setMaximum(999)
        self.video_slider.setPageStep(100)
        self.video_slider.setOrientation(QtCore.Qt.Horizontal)
        self.video_slider.setObjectName("video_slider")
        self.video_play_layout.addWidget(self.video_slider)
        self.video_label = QtWidgets.QLabel(self.center_widget)
        self.video_label.setObjectName("video_label")
        self.video_play_layout.addWidget(self.video_label)
        self.center_layout.addLayout(self.video_play_layout)
        self.text_edit = QtWidgets.QTextEdit(self.center_widget)
        self.text_edit.setMinimumSize(QtCore.QSize(0, 0))
        self.text_edit.setMaximumSize(QtCore.QSize(1677, 167))
        self.text_edit.setObjectName("text_edit")
        self.center_layout.addWidget(self.text_edit)
        # self.center_layout.setStretch(0, 1)
        self.center_layout.setStretch(0, 20)
        self.center_layout.setStretch(1, 1)
        self.center_layout.setStretch(2, 3)
        self.content_layout.addLayout(self.center_layout)
        self.tree_widget_right = QtWidgets.QTreeWidget(self.center_widget)
        self.tree_widget_right.setEnabled(True)
        self.tree_widget_right.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.tree_widget_right.setColumnCount(2)
        self.tree_widget_right.setObjectName("tree_widget_right")
        self.tree_widget_right.headerItem().setText(0, "Attribute")
        self.tree_widget_right.header().setVisible(True)
        self.tree_widget_right.setExpandsOnDoubleClick(False)

        self.content_layout.addWidget(self.tree_widget_right)
        self.content_layout.setStretch(0, 2)
        self.content_layout.setStretch(1, 6)
        self.content_layout.setStretch(2, 2)
        self.whole_layout.addLayout(self.content_layout)
        main_window.setCentralWidget(self.center_widget)
        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("status_bar")
        main_window.setStatusBar(self.status_bar)
        self.tool_bar = QtWidgets.QToolBar(main_window)
        self.tool_bar.setMouseTracking(False)
        self.tool_bar.setAcceptDrops(False)
        self.tool_bar.setObjectName("tool_bar")
        main_window.addToolBar(QtCore.Qt.TopToolBarArea, self.tool_bar)
        self.menu_bar = QtWidgets.QMenuBar(main_window)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 941, 19))
        self.menu_bar.setMouseTracking(False)
        self.menu_bar.setAcceptDrops(False)
        self.menu_bar.setToolTipDuration(0)
        self.menu_bar.setDefaultUp(False)
        self.menu_bar.setNativeMenuBar(False)
        self.menu_bar.setObjectName("menu_bar")

        font = self.menu_bar.font()
        font.setPointSize(12)
        self.menu_bar.setFont(font)

        main_window.setMenuBar(self.menu_bar)
        self.tool_bar.addSeparator()

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("main_window", "SDKTool"))
        self.video_label.setText(_translate("main_window", "00 : 00 : 00"))
        self.text_edit.setHtml(_translate("main_window", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" "
                                                         "\"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                                         "<html><head><meta name=\"qrichtext\" content=\"1\" />"
                                                         "<style type=\"text/css\">\np, li { white-space: pre-wrap; }\n"
                                                         "</style></head><body style=\" font-family:\'Sans Serif\'; "
                                                         "font-size:9pt; font-weight:400; font-style:normal;\">\n"
                                                         "<p style=\" margin-top:0px; margin-bottom:0px; "
                                                         "margin-left:0px; margin-right:0px; -qt-block-indent:0; "
                                                         "text-indent:0px;\"><span style=\" font-family:\'Ubuntu\'; "
                                                         "font-size:11pt;\">LogInfo</span></p></body></html>"))
        self.tool_bar.setWindowTitle(_translate("main_window", "toolBar"))
