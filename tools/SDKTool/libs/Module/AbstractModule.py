# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
import shutil
from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from abc import ABCMeta, abstractmethod
from libs.shape import *
from libs.customDialog import *
from define import *

class AbstractModule(object):
    __metaclass__ = ABCMeta

    def __init__(self, MainWindow=None, ui=None):
        self.logger = logging.getLogger("sdktool")
        self.ui = ui                                      # ui是QTdesigner生成的类的对象，包含所有按钮或其他控件
        self.mainWindow = MainWindow                      # 窗口类，包含很多按钮或动作的槽函数

        # 树结构的icon
        self.treeIcon = QtGui.QIcon()
        self.treeIcon.addPixmap(QtGui.QPixmap(":/menu/treeIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.projectDict = None

    '''
        创建一个QTreeItem
        输入参数：key为item的key值，也就是第一列的值
        输入参数：value为item的value值，也就是第二列的值
        输入参数：type为item的类别，也就是第三列的值，所有类别均在define.py中定义
        输入参数：edit表示item是否可编辑
    '''
    def CreateTreeItem(self, key, value=None, type=None, edit=False):
        child = QTreeWidgetItem()
        child.setText(0, str(key))

        if value is not None:
            child.setText(1, str(value))

        if type is not None:
            child.setText(2, type)
        child.setIcon(0, self.treeIcon)
        if edit is True:
            child.setFlags(child.flags() | Qt.ItemIsEditable)

        return child

    '''
        在画布上显示图像
        输入参数：imgPath表示图像的路径
    '''
    def PaintImage(self, imgPath):
        if imgPath == "" or imgPath is None:
            self.logger.error('wrong imgPath: {}'.format(imgPath))
            return

        try:
            frame = QImage(imgPath)
            self.mainWindow.image = frame
            pix = QPixmap.fromImage(frame)
            self.mainWindow.canvas.loadPixmap(pix)
            self.mainWindow.canvas.setEnabled(True)
            self.mainWindow.adjustScale(initial=True)
            self.mainWindow.paintCanvas()
        except Exception as e:
            self.logger.error('read image failed, imgPath: {}'.format(imgPath))
            self.logger.error(e)

    def SetProjectDict(self, projectDict=None):
        self.projectDict = projectDict

    '''
        获取制定item中特定子item的值
        输入参数：treeItem表示需要查找的父item
        输入参数：sourceColumn表示需要查找的key在树的第几列
        输入参数：sourceKey表示将要查找的key
        输入参数：targetColumn表示需要查找的value在树的第几列
        返回值：字符串（查找的value值）或item（因为有可能value是Qt的控件，比如下拉选项框或者编辑框）
    '''
    def GetChildItemValue(self, treeItem, sourceColumn, sourceKey, targetColumn):
        if treeItem is None:
            self.logger.error('GetChildItemValue failed, treeItem is None')
            return

        for itemIdx in range(treeItem.childCount()):
            treeItemChild = treeItem.child(itemIdx)
            if treeItemChild.text(sourceColumn) == sourceKey:
                itemWidget = self.ui.treeWidget.itemWidget(treeItemChild, targetColumn)
                if itemWidget is not None:
                    if isinstance(itemWidget, QLineEdit):
                        return itemWidget.text()
                    return itemWidget
                else:
                    return treeItemChild.text(targetColumn)

    '''
        返回指定QTreeItem的子item
        输入参数：treeItem表示需要查找的父item
        输入参数：itemKey表示需要查找的key，默认第一列为key
        返回值：QTreeItem（满足key的子item）或None（当没有找到满足key的item时）
    '''
    def GetChildItem(self, treeItem, itemKey):
        if treeItem is None:
            self.logger.error("GetChildItem failed, treeItem is None")
            return

        for itemIdx in range(treeItem.childCount()):
            childItem = treeItem.child(itemIdx)
            if childItem.text(0) == itemKey:
                return childItem

        return None

    '''
        根据rect字典的值，创建对应的树结构
        输入参数：ROIJsonDict表示rect字典，{"x": int, "y", int, "w": int, "h": int}
        输入参数：treeItemROI表示父item，将在该item下创建rect的树结构
    '''
    def LoadRectIndex(self, ROIJsonDict, treeItemROI, index):
        if treeItemROI is None:
            self.logger.error("LoadRect failed, treeItemROI is None")
            return

        if ROIJsonDict is None:
            self.logger.error("LoadRect failed, ROIJsonDict is None")
            return
        if index is not None:
            xText = "x{}".format(index)
            yText = "y{}".format(index)
            wText = "w{}".format(index)
            hText = "h{}".format(index)
        else:
            xText = "x"
            yText = "y"
            wText = "w"
            hText = "h"

        if xText not in ROIJsonDict.keys():
            ROIJsonDict["x"] = 0
        if yText not in ROIJsonDict.keys():
            ROIJsonDict["y"] = 0
        if wText not in ROIJsonDict.keys():
            ROIJsonDict["w"] = 0
        if hText not in ROIJsonDict.keys():
            ROIJsonDict["h"] = 0

        treeItemROI.addChild(self.CreateTreeItem(key=xText, value=ROIJsonDict.get(xText) or 0, edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key=yText, value=ROIJsonDict.get(yText) or 0, edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key=wText, value=ROIJsonDict.get(wText) or 0, edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key=hText, value=ROIJsonDict.get(hText) or 0, edit=True))

    '''
        根据rect字典的值，创建对应的树结构
        输入参数：ROIJsonDict表示rect字典，{"x": int, "y", int, "w": int, "h": int}
        输入参数：treeItemROI表示父item，将在该item下创建rect的树结构
    '''
    def LoadRect(self, ROIJsonDict, treeItemROI):
        if treeItemROI is None:
            self.logger.error("LoadRect failed, treeItemROI is None")
            return

        if ROIJsonDict is None:
            self.logger.error("LoadRect failed, ROIJsonDict is None")
            return

        if "x" not in ROIJsonDict.keys():
            ROIJsonDict["x"] = 0
        if "y" not in ROIJsonDict.keys():
            ROIJsonDict["y"] = 0
        if "w" not in ROIJsonDict.keys():
            ROIJsonDict["w"] = 0
        if "h" not in ROIJsonDict.keys():
            ROIJsonDict["h"] = 0

        treeItemROI.addChild(self.CreateTreeItem(key='x', value=ROIJsonDict["x"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='y', value=ROIJsonDict["y"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='w', value=ROIJsonDict["w"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='h', value=ROIJsonDict["h"], edit=True))

    '''
        根据point字典的值，创建对应的树结构
        输入参数：pointJsonDict表示rect字典，{"x": int, "y", int}
        输入参数：treeItemPoint表示父item，将在该item下创建point的树结构
    '''
    def LoadPoint(self, pointJsonDict, treeItemPoint):
        if treeItemPoint is None:
            self.logger.error("LoadPoint failed, treeItemROI is None")
            return

        if pointJsonDict is None:
            self.logger.error("LoadPoint failed, pointJsonDict is None")
            return

        if "x" not in pointJsonDict.keys():
            pointJsonDict["x"] = 0
        if "y" not in pointJsonDict.keys():
            pointJsonDict["y"] = 0

        treeItemPoint.addChild(self.CreateTreeItem(key='x', value=pointJsonDict["x"], edit=True))
        treeItemPoint.addChild(self.CreateTreeItem(key='y', value=pointJsonDict["y"], edit=True))

    def _GetDictValue(self, dic, keyList):
        for key in keyList:
            if key in dic.keys():
                return dic[key]

        return None

    '''
        根据点的个数创建shape
        输入参数：point的list
        输出参数：shape
    '''
    def CreateShape(self, points, close=True):
        if points is None:
            self.logger.error("CreateShape failed, points is None")

            return

        if len(points) == 1:
            shape = Shape(name=Shape.POINT)
        elif len(points) == 2:
            shape = Shape(name=Shape.LINE)
        elif len(points) == 4:
            shape = Shape()
        else:
            self.logger.error("wrong type of shape, points number: {}".format(len(points)))
            return

        for x, y in points:
            x, y, snapped = self.mainWindow.canvas.snapPointToCanvas(x, y)
            shape.addPoint(QPointF(x, y))

        return shape

    '''
        隐藏满足条件的QTreeItem
    '''
    def HiddenItem(self, treeItem):
        iterator = QTreeWidgetItemIterator(treeItem)
        while iterator.value() is not None:
            if iterator.value().text(0) in ["elementID", "templateID", "taskName", "elementName", "templateName"]:
                iterator.value().setHidden(True)
            iterator.__iadd__(1)

    def GenerateRect(self):
        rect = OrderedDict()
        rect["x"] = 0
        rect["y"] = 0
        rect["w"] = 0
        rect["h"] = 0
        return rect

    def copyFile(self, sourcePath, targetPath):
        for file in os.listdir(sourcePath):
            sourceFile = os.path.join(sourcePath, file)
            targetFile = os.path.join(targetPath, file)

            if os.path.isdir(sourceFile):
                if not os.path.exists(targetFile):
                    os.makedirs(targetFile)
                self.copyFile(sourceFile, targetFile)

            if os.path.isfile(sourceFile):
                extension = os.path.splitext(file)[1]
                if extension in [".jpg", ".png", ".bmp"]:
                    shutil.copy(sourceFile, targetFile)
