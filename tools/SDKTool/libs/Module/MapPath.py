# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging
from libs.Module.AbstractModule import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from libs.shape import *

class CMapPath(AbstractModule):
    def __init__(self, MainWindow=None, ui=None):
        AbstractModule.__init__(self, MainWindow, ui)

        self.actionAddMapPath = QAction(MainWindow)
        self.actionAddMapPath.setText("添加地图路线")
        self.actionAddMapPath.triggered.connect(self.AddMapPath)

        self.actionAddSinglePath = QAction(MainWindow)
        self.actionAddSinglePath.setText("添加路线")
        self.actionAddSinglePath.triggered.connect(self.AddSinglePath)

        self.actionChangePath = QAction(MainWindow)
        self.actionChangePath.setText("修改路线")
        self.actionChangePath.triggered.connect(self.ChangePathLine)

        self.actionAddPathType = QAction(MainWindow)
        self.actionAddPathType.setText("添加路线类型")
        self.actionAddPathType.triggered.connect(self.AddPathType)

        self.actionDelPathPoint = QAction(MainWindow)
        self.actionDelPathPoint.setText("删除")
        self.actionDelPathPoint.triggered.connect(self.DelPathPoint)

        self.mapPathTypeDialog = customDialog(text="输入路径类型", parent=self.mainWindow)

    def SetProjectInfo(self, projectName=None, projectPath=None):
        self.projectName = projectName
        self.projectPath = projectPath

    '''
        添加地图路径
    '''
    def AddMapPath(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddSinglePath failed, treeItem is None")
            return

        mapDict = self.GenerateMapPathDict()

        # 导入图像
        FileDialog = QFileDialog()
        FileDialog.setFileMode(QFileDialog.Directory)
        FileDialog.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        if FileDialog.exec():
            directoryName = FileDialog.selectedFiles()[0]
            if directoryName == "":
                self.logger.info("directory is empty")
                return
        else:
            self.logger.error("get directory failed")
            return

        version = self.GetVersionItem(treeItem).text(0)
        mapImageDir = self.projectPath + "/" + version + "/mapImage"
        isExist = os.path.exists(mapImageDir)
        if isExist is not True:
            os.makedirs(mapImageDir)

        # 将刚导入的图像拷贝至指定目录
        self.copyFile(directoryName, mapImageDir)

        for file in os.listdir(mapImageDir):
            mapDict[file] = OrderedDict()

        # 创建地图路径的树结构
        self.CreateMapPathTree(mapDict, treeItem)

        # treeItem.addChild(mapPathTreeItem)
        treeItem.setExpanded(True)

    '''
        获取versionitem
        输入参数：treeItem指输入的某一QTreeItem
    '''
    def GetVersionItem(self, treeItem):
        if treeItem is None:
            self.logger.error("GetRectItem failed, treeItem is None")

            return

        versionItem = None
        while True:
            if treeItem.parent() is None:
                break

            if treeItem.parent().text(0) == self.projectName:
                versionItem = treeItem
                break

            treeItem = treeItem.parent()
        return versionItem

    '''
        返回地图路径字典
    '''
    def GenerateMapPathDict(self):
        mapDict = OrderedDict()
        mapDict['walkSpeed'] = 5
        mapDict['mapCreateAuto'] = 1
        mapDict['mapCreatePath'] = str()
        mapDict['mapPath'] = str()
        return mapDict

    '''
        根据输入的地图路径字典，创建对应的树结构
        输入参数：mapPathDict表示地图路径字典
        输入参数：treeItem表示要挂载的节点
    '''
    def CreateMapPathTree(self, mapPathDict, treeItem):
        if treeItem is None:
            self.logger.error("CreateMapPathTree failed, treeItem is None")
            return

        if mapPathDict is None:
            self.logger.error("CreateMapPathTree failed, mapPathDict is None")
            return

        # 创建地图路径根节点
        mapPathTreeItem = self.CreateTreeItem(key='MapPath', type=ITEM_TYPE_MAPPATH)
        treeItem.addChild(mapPathTreeItem)

        # 创建其他节点
        childWalkSpeed = self.CreateTreeItem(key='walkSpeed', value=mapPathDict['walkSpeed'], edit=True)
        mapPathTreeItem.addChild(childWalkSpeed)

        childItem = self.CreateTreeItem(key='mapCreateAuto')
        mapPathTreeItem.addChild(childItem)
        qCombox = QComboBox()
        qCombox.addItems([
            "0",
            "1"
        ])
        qCombox.setCurrentText(str(mapPathDict['mapCreatePath']))
        self.ui.treeWidget.setItemWidget(childItem, 1, qCombox)
        mapPathTreeItem.addChild(
            self.CreateTreeItem(key='mapCreatePath', value=mapPathDict['mapCreatePath'], edit=True))
        mapPathTreeItem.addChild(self.CreateTreeItem(key='mapPath', value=mapPathDict['mapPath'], edit=True))

        # 地图路径的配置文件images下存放所有图片对应的路径，key为图像名字
        childMapPathItem = self.CreateTreeItem(key='images', type=ITEM_TYPE_MAPPATH)
        mapPathTreeItem.addChild(childMapPathItem)

        # 遍历每个mapPathDict的item，除了'walkSpeed', 'mapCreateAuto', 'mapCreatePath', 'mapPath'，
        # 其他的就是以图像名为key值的路径
        for key, value in mapPathDict.items():
            if key in ['walkSpeed', 'mapCreateAuto', 'mapCreatePath', 'mapPath']:
                continue

            # 创建单个路径的item
            mapPathSingleItem = self.CreateTreeItem(key=key, type=ITEM_TYPE_MAPPATH_IMAGE)
            childMapPathItem.addChild(mapPathSingleItem)

            # 路径会有个类别，字典中的结构是类别为key，路径为value
            for pathkey, pathValue in value.items():
                # 创建路径的item
                childGRItem = self.CreateTreeItem(key=pathkey, type=ITEM_TYPE_MAPPATH_LINEPATH)
                mapPathSingleItem.addChild(childGRItem)

                # 对每个路径都添加对应的名为line的item
                for lineKey, lineValue in pathValue.items():
                    childLineItem = self.CreateTreeItem(key='line', type=ITEM_TYPE_MAPPATH_SINGLE_LINE)
                    childGRItem.addChild(childLineItem)
                    # 对路径的每个点都添加名为point的item
                    for point in lineValue:
                        childPointItem = self.CreateTreeItem(key='point')
                        childLineItem.addChild(childPointItem)
                        childPointItem.addChild(self.CreateTreeItem(key='x', value=point[0], edit=True))
                        childPointItem.addChild(self.CreateTreeItem(key='y', value=point[1], edit=True))

    '''
        选中point的item，右键删除路径的某个点
    '''
    def DelPathPoint(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("DelPathPoint failed, treeItem is None")

            return

        parentItem = treeItem.parent()

        # 获取当前item对应的点在shape中的索引
        index = parentItem.indexOfChild(treeItem)

        if len(self.mainWindow.canvas.shapes) == 0:
            self.logger.warning('shapes is empty')
            return
        shape = self.mainWindow.canvas.shapes[0]

        # 从shape中删除选中的点
        shape.points.pop(index)
        self.mainWindow.canvas.update()

        # 删除选中的point的item
        treeItem.parent().removeChild(treeItem)

    '''
        弹框添加路径的类型
    '''
    def AddPathType(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddPathType failed, treeItem is None")
            return

        pathType = self.mapPathTypeDialog.popUp()
        if pathType is None or pathType == "":
            return

        # 创建以输入的名字为名的路径种类的item
        treeItem.addChild(self.CreateTreeItem(key=pathType, type=ITEM_TYPE_MAPPATH_LINEPATH))

    '''
        右键某一路径的item，点击修改路径时触发的槽函数
    '''
    def ChangePathLine(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("ChangePathLine failed, treeItem is None")
            return

        mapImageName = treeItem.parent().parent().text(0)

        # 画出修改路径对应的图像
        version = self.GetVersionItem(treeItem).text(0)
        imagePath = self.projectPath + "/" + version + "/mapImage/" + mapImageName
        self.PaintImage(imagePath)
        self.mainWindow.canvas.currentModel.append(Shape.POLYGONLINE)

        # 画出当前的路径
        shape = Shape(name=Shape.POLYGONLINE)
        self.mainWindow.canvas.setPolygonLineItem(treeItem)
        for itemIndex in range(treeItem.childCount()):
            childItem = treeItem.child(itemIndex)
            x = int(childItem.child(0).text(1))
            y = int(childItem.child(1).text(1))
            shape.addPoint(QPoint(x, y))

        self.mainWindow.canvas.AddShape(shape)
        self.mainWindow.canvas.setPolygonLineItem(treeItem)

        # 将画布的模式设为CREATE
        self.mainWindow.canvas.setEditing(False)

    '''
        在某一种类item下添加路径
    '''
    def AddSinglePath(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddSinglePath failed, treeItem is None")
            return

        mapImageName = treeItem.parent().text(0)

        # 创建名为line的item，表示路径，其子节点存的时point的item
        childLineItem = self.CreateTreeItem(key='line', type=ITEM_TYPE_MAPPATH_SINGLE_LINE)
        treeItem.addChild(childLineItem)

        # 将当前对应的图像画出来
        version = self.GetVersionItem(treeItem).text(0)
        imagePath = self.projectPath + "/" + version + "/mapImage/" + mapImageName
        self.PaintImage(imagePath)
        self.mainWindow.canvas.currentModel.append(Shape.POLYGONLINE)
        self.mainWindow.canvas.setPolygonLineItem(childLineItem)
        self.mainWindow.canvas.setEditing(False)

    '''
        将地图路径的树结构转换为字典，返回给mainwindow
    '''
    def SaveMapPathFile(self):
        mapPathJsonDict = OrderedDict()
        topLevelItem = self.ui.treeWidget.topLevelItem(0)

        if topLevelItem is None:
            return

        # 遍历每个version
        for versionIndex in range(topLevelItem.childCount()):
            versionItem = topLevelItem.child(versionIndex)
            mapPathDict = OrderedDict()
            if versionItem.text(0) in ["project.json", "project.json~"]:
                continue

            for sceneIndex in range(versionItem.childCount()):
                sceneItem = versionItem.child(sceneIndex)
                sceneKey = sceneItem.text(0)
                # 只处理key为MapPath的节点
                if sceneKey == "MapPath":
                    mapPathDict = self.MapPathTree2Dict(sceneItem)

            mapPathJsonDict[versionItem.text(0)] = mapPathDict
        return mapPathJsonDict

    '''
        将地图路径树结构的内容转换为字典
        返回值：mapPathDict表示地图路径树结构对应的字典
    '''
    def MapPathTree2Dict(self, treeItem):
        if treeItem is None:
            self.logger.error("MapPathTree2Dict failed, treeItem is None")
            return

        # 填充某些字段
        mapPathDict = OrderedDict()
        mapPathDict['walkSpeed'] = int(treeItem.child(0).text(1))
        combox = self.GetChildItemValue(treeItem, 0, "mapCreateAuto", 1)
        mapPathDict['mapCreateAuto'] = int(combox.currentText())
        mapPathDict['mapCreatePath'] = treeItem.child(2).text(1)
        mapPathDict['mapPath'] = treeItem.child(3).text(1)

        imageItem = treeItem.child(4)        # 第5个节点为images节点
        # 遍历每个图像的路径
        for imageIndex in range(imageItem.childCount()):
            childImageItem = imageItem.child(imageIndex)
            imageName = childImageItem.text(0)

            mapPathDict[imageName] = OrderedDict()

            # 遍历当前图像的每个路径类型
            for typeIndex in range(childImageItem.childCount()):
                childTypeItem = childImageItem.child(typeIndex)
                typeName = childTypeItem.text(0)

                mapPathDict[imageName][typeName] = OrderedDict()

                # 遍历当前类型下的每个路径
                for lineIndex in range(childTypeItem.childCount()):
                    childLineItem = childTypeItem.child(lineIndex)
                    if childLineItem.childCount() > 0:
                        mapPathDict[imageName][typeName]['line' + str(lineIndex)] = list()

                    # 遍历当前路径的每个点
                    for pointIndex in range(childLineItem.childCount()):
                        childPointItem = childLineItem.child(pointIndex)
                        x = int(childPointItem.child(0).text(1))
                        y = int(childPointItem.child(1).text(1))

                        # 每个点之后还要填充一个方向，比如[100, 100, -50, -50] 后面两个-50表示方向
                        # 如果是最后一个点，则填0 ，0
                        if pointIndex == childLineItem.childCount() - 1:
                            directX = 0
                            directY = 0
                        # 如果不是最后一个点，要计算其与之后点的方向
                        else:
                            childNextPointItem = childLineItem.child(pointIndex + 1)
                            x1 = int(childNextPointItem.child(0).text(1))
                            y1 = int(childNextPointItem.child(1).text(1))
                            directX = x1 - x
                            directY = y1 - y

                        # 填充点
                        mapPathDict[imageName][typeName]['line' + str(lineIndex)].append([x, y, directX, directY])

                    if childLineItem.childCount() > 0:
                        mapPathDict[imageName][typeName]['line' + str(lineIndex)] = str(
                            mapPathDict[imageName][typeName]['line' + str(lineIndex)])

        return mapPathDict