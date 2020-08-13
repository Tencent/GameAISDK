# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from libs.canvas import *
from libs.zoomWidget import *
from libs.customDialog import *
from libs.confirmDialog import *
from libs.fileWidget import *


class Ui_MainWindow(object):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    def __init__(self):
        self.centralwidget = None
        self.mainWindow = None
        # self.progressBar = None

    def setupUi(self, MainWindow):
        self.mainWindow = MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1079, 660)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.horizontalLayout_2.addWidget(self.treeWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pushButton_prev = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_prev.setObjectName("pushButton_prev")
        self.pushButton_prev.setEnabled(False)
        # self.pushButton_prev.setEnabled(False)
        self.horizontalLayout_5.addWidget(self.pushButton_prev)
        self.pushButton_next = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_next.setObjectName("pushButton_next")
        self.pushButton_next.setEnabled(False)
        # self.pushButton_next.setEnabled(False)
        self.horizontalLayout_5.addWidget(self.pushButton_next)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        MainWindow.canvas = Canvas(MainWindow)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        MainWindow.canvas.setSizePolicy(sizePolicy)

        self.scroll = QScrollArea()
        self.scroll.setWidget(MainWindow.canvas)
        self.scroll.setWidgetResizable(True)

        self.scroll.setHorizontalScrollBarPolicy(self.scroll.horizontalScrollBar().maximum())
        self.hScrollbar = QScrollBar(Qt.Horizontal)
        self.hScrollbar.setMaximum(self.scroll.horizontalScrollBar().maximum())

        self.vScrollbar = QScrollBar(Qt.Vertical)
        self.vScrollbar.setMinimum(self.scroll.verticalScrollBar().maximum())

        self.horizontalLayout_4.addWidget(self.scroll)

        self.horizontalLayout_4.addWidget(self.vScrollbar)
        #############
        self.horizontalLayout_4.setStretch(0, 4)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_videoleft = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_videoleft.setText("")
        self.pushButton_videoleft.setIconSize(QtCore.QSize(30, 30))
        self.pushButton_videoleft.setObjectName("pushButton_videoleft")
        self.pushButton_videoleft.setEnabled(False)
        self.horizontalLayout.addWidget(self.pushButton_videoleft)
        self.pushButton_videostart = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_videostart.setText("")
        self.pushButton_videostart.setIconSize(QtCore.QSize(30, 30))
        self.pushButton_videostart.setObjectName("pushButton_videostart")
        self.pushButton_videostart.setEnabled(False)
        self.horizontalLayout.addWidget(self.pushButton_videostart)
        self.pushButton_videoright = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_videoright.setText("")
        self.pushButton_videoright.setIconSize(QtCore.QSize(30, 30))
        self.pushButton_videoright.setObjectName("pushButton_videoright")
        self.pushButton_videoright.setEnabled(False)
        self.horizontalLayout.addWidget(self.pushButton_videoright)
        self.horizontalSlider = CustomSlider(self.centralwidget)
        self.horizontalSlider.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(999)
        self.horizontalSlider.setPageStep(100)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalSlider.setEnabled(False)
        self.horizontalLayout.addWidget(self.horizontalSlider)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.label.setEnabled(False)
        self.horizontalLayout.addWidget(self.label)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(3, 15)
        self.horizontalLayout.setStretch(4, 1)

        self.verticalLayout.addWidget(self.hScrollbar)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 10)
        self.verticalLayout.setStretch(2, 1)
        self.verticalLayout.setStretch(3, 1)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_2.setStretch(0, 2)
        self.horizontalLayout_2.setStretch(1, 5)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1079, 31))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menuTest2 = QtWidgets.QMenu(self.menu)
        self.menuTest2.setObjectName("menuTest2")
        self.menuTest1 = QtWidgets.QMenu(self.menu)
        self.menuTest1.setObjectName("menuTest1")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.toolBar_2 = QtWidgets.QToolBar(MainWindow)
        self.toolBar_2.setObjectName("toolBar_2")

        self.tbUIGraph = QtWidgets.QToolBar(MainWindow)
        self.tbUIGraph.setObjectName("UIResultAnalyze")

        MainWindow.addToolBar(QtCore.Qt.RightToolBarArea, self.toolBar_2)
        MainWindow.addToolBar(QtCore.Qt.RightToolBarArea, self.tbUIGraph)
        self.actionImportImg = QtWidgets.QAction(MainWindow)
        self.actionImportImg.setObjectName("actionImportImg")
        self.actionTest = QtWidgets.QAction(MainWindow)
        self.actionTest.setCheckable(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/menu/退出.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionTest.setIcon(icon)
        self.actionTest.setObjectName("actionTest")
        self.actionSave = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/menu/保存.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionSave.setIcon(icon1)
        self.actionSave.setObjectName("actionSave")
        self.actionImport = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/menu/import.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionImport.setIcon(icon2)
        self.actionImport.setObjectName("actionImport")

        # menu
        tool = self.menubar.addMenu("Tools")

        # action sample
        actionSampleMenu = tool.addMenu("actionSample")
        self.actionSampleStart = QtWidgets.QAction("start", MainWindow)
        actionSampleMenu.addAction(self.actionSampleStart)
        self.actionSampleExit = QtWidgets.QAction("end", MainWindow)
        actionSampleMenu.addAction(self.actionSampleExit)

        # Generate GPluginTmpt
        # pluginTemplate = tool.addMenu("GeneratePluginSrc")
        self.generatePluginAction = QtWidgets.QAction("GeneratePluginSrc", MainWindow)
        tool.addAction(self.generatePluginAction)

        self.UIExploreAction = QtWidgets.QAction("UIAutoExplore", MainWindow)
        tool.addAction(self.UIExploreAction)

        self.toolBar.addAction(self.actionTest)
        self.toolBar.addAction(self.actionSave)
        self.toolBar_2.addAction(self.actionImport)

        self.actionUIGraph = QtWidgets.QAction(MainWindow)
        iconUIGraph = QtGui.QIcon()
        iconUIGraph.addPixmap(QtGui.QPixmap(":/menu/graph.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionUIGraph.setIcon(iconUIGraph)
        self.actionUIGraph.setObjectName("action Show UI Path")

        self.tbUIGraph.addAction(self.actionUIGraph)
        
        ## ====================== add by myself===========================
        self.fileListWidget = QListWidget()

        features = QtWidgets.QDockWidget.DockWidgetFeatures()
        # self.dockTreeWidget = QDockWidget('treeWidget', self.mainWindow)
        self.dockTreeWidget = QDockWidget('', self.mainWindow)
        self.dockTreeWidget.setObjectName(u'treeWidget')
        self.dockTreeWidget.setWidget(self.treeWidget)
        self.dockTreeWidget.setFeatures(features |
                                        QtWidgets.QDockWidget.DockWidgetClosable |
                                        QtWidgets.QDockWidget.DockWidgetFloatable |
                                        QtWidgets.QDockWidget.DockWidgetMovable)
        # self.dockTreeWidget.setWid

        # self.dockFileListWidget = QDockWidget('file list', self.mainWindow)
        # self.dockFileListWidget.setObjectName(u'file list')
        # self.dockFileListWidget.setWidget(self.fileListWidget)
        # self.dockFileListWidget.setFeatures(features |
        #                                     QtWidgets.QDockWidget.DockWidgetClosable |
        #                                     QtWidgets.QDockWidget.DockWidgetFloatable |
        #                                     QtWidgets.QDockWidget.DockWidgetMovable)

        self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.dockTreeWidget)
        # self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.dockFileListWidget)
        # self.dockFileListWidget.close()

        self.treeWidget.setColumnCount(4)
        self.treeWidget.setColumnWidth(0, 350)
        self.treeWidget.setColumnHidden(2, True)
        self.treeWidget.setColumnHidden(3, True)

        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)

        self.labelCoordinates = QLabel('')
        self.statusbar.addPermanentWidget(self.labelCoordinates)

        ## ===============================================================
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "SDKTool"))
        self.treeWidget.headerItem().setText(0, _translate("MainWindow", "key"))
        self.treeWidget.headerItem().setText(1, _translate("MainWindow", "value"))
        self.pushButton_prev.setText(_translate("MainWindow", "prev"))
        self.pushButton_next.setText(_translate("MainWindow", "next"))
        self.label.setText(_translate("MainWindow", "00 : 00 : 00"))
        self.menu.setTitle(_translate("MainWindow", "菜单"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.toolBar_2.setWindowTitle(_translate("MainWindow", "toolBar_2"))
        self.tbUIGraph.setWindowTitle(_translate("MainWindow", "tbUIGraph"))
        self.actionImportImg.setText(_translate("MainWindow", "导入图片"))
        self.actionTest.setText(_translate("MainWindow", "test"))
        self.actionTest.setToolTip(_translate("MainWindow", "test"))
        self.actionSave.setText(_translate("MainWindow", "save"))
        self.actionSave.setToolTip(_translate("MainWindow", "save"))
        self.actionImport.setText(_translate("MainWindow", "Import"))
        self.actionImport.setToolTip(_translate("MainWindow", "导入图像（目录）"))

import Resource.Resource_rc
