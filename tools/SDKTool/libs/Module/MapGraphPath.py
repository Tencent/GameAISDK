# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from libs.Module.AbstractModule import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from libs.shape import *

class CMapGraphPath(AbstractModule):
    def __init__(self, MainWindow=None, ui=None):
        AbstractModule.__init__(self, MainWindow, ui)
        self.actionAddGraphPath = QAction(MainWindow)
        self.actionAddGraphPath.setText("添加图结构路径")
        self.actionAddGraphPath.triggered.connect(self.AddGraphPath)

        self.actionAddGraphPathPoint = QAction(MainWindow)
        self.actionAddGraphPathPoint.setText("添加路径点")
        self.actionAddGraphPathPoint.triggered.connect(self.AddGraphPathPoint)
        self.imagePath = None

    '''
        添加图结构路径，并导入图片
    '''
    def AddGraphPath(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddUI failed, treeItem is None')
            return

        image, Type = QFileDialog.getOpenFileName(None, "导入图片", "~/", "*.*")
        if image == "":
            self.logger.info('image is empty in ImportImageFile')
            return

        self.imagePath = image
        self.CreateMapGraphPathTree({}, treeItem)

    '''
        添加路径点
    '''
    def AddGraphPathPoint(self):
        self.mainWindow.canvas.setEditing(False)
        self.mainWindow.canvas.pointGraphIndex = 1

        # 保证canvas的currentModel中只有GRAPH
        if len(self.mainWindow.canvas.currentModel) == 0:
            self.mainWindow.canvas.currentModel.append(Shape.GRAPH)
        else:
            while len(self.mainWindow.canvas.currentModel) > 1:
                self.mainWindow.canvas.currentModel.pop()

            self.mainWindow.canvas.currentModel[0] = Shape.GRAPH

    '''
        根据图结构路径的字典，创建图结构路径的树
        输入参数：mapGraphDict表示图结构路径的字典
        输入参数：treeItem表示挂载的节点
    '''
    def CreateMapGraphPathTree(self, mapGraphDict, treeItem):
        if treeItem is None:
            self.logger.error("CreateMapGraphPathTree failed, treeItem is None")
            return

        if mapGraphDict is None:
            self.logger.error("CreateMapGraphPathTree failed, mapGraphDict is None")
            return

        # 创建根节点
        mapPathTreeItem = self.CreateTreeItem(key='MapGraphPath', type=ITEM_TYPE_MAPPATH_GRAPH)
        treeItem.addChild(mapPathTreeItem)

        # 保存图像路径
        self.mapGraphDict = mapGraphDict
        if "imagePath" in mapGraphDict.keys():
            self.imagePath = mapGraphDict['imagePath']

    def showImagePath(self):
        self.PaintImage(self.imagePath)

    '''
        将地图路径转换为字典，返回给mainwindow
    '''
    def SaveGraphPathFile(self):
        mapGraphPathJsonDict = OrderedDict()
        topLevelItem = self.ui.treeWidget.topLevelItem(0)

        if topLevelItem is None:
            return

        # 遍历每个version
        for versionIndex in range(topLevelItem.childCount()):
            versionItem = topLevelItem.child(versionIndex)
            if versionItem.text(0) in ["project.json", "project.json~"]:
                continue

            mapGraphVersionDict = OrderedDict()
            for sceneIndex in range(versionItem.childCount()):
                sceneItem = versionItem.child(sceneIndex)
                sceneKey = sceneItem.text(0)
                # 只处理key为MapGraphPath的节点
                if sceneKey == "MapGraphPath":
                    mapGraphVersionDict['points'] = list()
                    mapGraphVersionDict['paths'] = list()
                    mapGraphVersionDict['imagePath'] = self.imagePath
                    # 将canvas的shape转换为字典
                    for shape in self.mainWindow.canvas.shapes:
                        if shape.shapeName == Shape.GRAPH:
                            # 遍历每个点，填充point字段
                            for index, point in enumerate(shape.points):
                                pointDict = OrderedDict()
                                pointDict['id'] = index
                                pointDict['point'] = list()
                                pointDict['point'].append(int(point.x()))
                                pointDict['point'].append(int(point.y()))
                                mapGraphVersionDict['points'].append(pointDict)

                            # pointLinePath是一个字典，保存了点到点的连接，比如pointLinePath[1] = 2表示点1到点2之间要连线
                            # 遍历shape的pointLinePath，填充paths字段
                            for key, pointList in shape.pointLinePath.items():
                                pathDict = None
                                for path in mapGraphVersionDict['paths']:
                                    if path['from'] == key:
                                        pathDict = path
                                        break

                                if pathDict is None:
                                    pathDict = OrderedDict()
                                    pathDict['from'] = key
                                    pathDict['to'] = pointList

                                for pointIndex in pointList:
                                    if pointIndex not in pathDict['to']:
                                        pathDict['to'].append(pointIndex)

                                mapGraphVersionDict['paths'].append(pathDict)

            mapGraphPathJsonDict[versionItem.text(0)] = mapGraphVersionDict
            self.mapGraphDict = mapGraphVersionDict
        return mapGraphPathJsonDict

    '''
        根据self.mapGraphDict字段的内容，画出图结构的路径
    '''
    def PaintGraphPath(self):
        self.showImagePath()

        # 创建图结构的shape
        shape = Shape(name=Shape.GRAPH)

        # 添加point
        if 'points' in self.mapGraphDict.keys():
            for point in self.mapGraphDict['points']:
                shape.addPoint(QPoint(point['point'][0], point['point'][1]))

        # 添加path
        if 'paths' in self.mapGraphDict.keys():
            for path in self.mapGraphDict['paths']:
                shape.pointLinePath[path['from']] = path['to']

        self.mainWindow.canvas.shapes.append(shape)
        self.mainWindow.canvas.currentModel.append(Shape.GRAPH)

        self.mainWindow.canvas.update()