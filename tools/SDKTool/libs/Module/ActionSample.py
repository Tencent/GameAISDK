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

class CActionSample(AbstractModule):
    def __init__(self, MainWindow=None, ui=None, projectDict=None):
        AbstractModule.__init__(self, MainWindow, ui)

        self.actionAddActionSampleRoot = QAction(MainWindow)
        self.actionAddActionSampleRoot.setText("添加动作配置根目录")
        self.actionAddActionSampleRoot.triggered.connect(self.AddActionSampleRoot)

        self.actionAddActionSample = QAction(MainWindow)
        self.actionAddActionSample.setText("添加动作配置")
        self.actionAddActionSample.triggered.connect(lambda: self.AddActionSample([{}], None))

        self.actionAddActionSingle = QAction(MainWindow)
        self.actionAddActionSingle.setText("添加动作")
        self.actionAddActionSingle.triggered.connect(self.AddActionSampleSingle)
        self.ActionIDIndex = 1

    def SetProjectDict(self, projectDict=None):
        self.projectDict = projectDict
        self.ActionIDIndex = self.projectDict["ActionIDStart"] if "ActionIDStart" in self.projectDict.keys() is not None else 1

    '''
        添加动作配置的根目录的树结构
    '''
    def AddActionSampleRoot(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddActionSample failed, treeItem is None')
            return

        # 创建根节点
        childActionSampleRoot = self.CreateTreeItem("ActionSampleRoot", type=ITEM_TYPE_ACTIONSAMPLE_ROOT)
        treeItem.addChild(childActionSampleRoot)

        # 创建debug节点
        childActionSampleRootDebug = self.CreateTreeItem(key='Debug')
        childActionSampleRoot.addChild(childActionSampleRootDebug)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText("True")
        self.ui.treeWidget.setItemWidget(childActionSampleRootDebug, 1, qCombox)

        # 创建其他节点
        childActionSampleRoot.addChild(self.CreateTreeItem(key="GameName", edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameFPS", value=10, edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameHeight", value=360, edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameWidth", value=640, edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="ActionCfgFile", edit=True))

        # OutputAsVideo节点
        childActionSampleRootOutPut = self.CreateTreeItem(key='OutputAsVideo')
        childActionSampleRoot.addChild(childActionSampleRootOutPut)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText("False")
        self.ui.treeWidget.setItemWidget(childActionSampleRootOutPut, 1, qCombox)

        # LogTimestamp节点
        childActionSampleRootLogTime = self.CreateTreeItem(key='LogTimestamp')
        childActionSampleRoot.addChild(childActionSampleRootLogTime)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText("False")
        self.ui.treeWidget.setItemWidget(childActionSampleRootLogTime, 1, qCombox)

    '''
        添加动作配置
        输入参数：actionSampleList表示动作实例的数组
        输入参数：treeItem表示动作配置的树结构挂载的节点
    '''
    def AddActionSample(self, actionSampleList, treeItem=None):
        for actionSampleDict in actionSampleList:
            # 如果没有值，则给默认值
            if "fileName" not in actionSampleDict.keys():
                actionSampleDict["fileName"] = ""

            if "screenWidth" not in actionSampleDict.keys():
                actionSampleDict["screenWidth"] = 1280

            if "screenHeight" not in actionSampleDict.keys():
                actionSampleDict["screenHeight"] = 720

            if "actions" not in actionSampleDict.keys():
                actionSampleDict["actions"] = list()
                actionSampleDict["actions"].append(self.GenerateActionNoneDict())

            if treeItem is None:
                treeItem = self.ui.treeWidget.currentItem()
                if treeItem is None:
                    self.logger.error('AddActionSample failed, treeItem is None')
                    return

            # 动作配置的根节点
            childActionSample = self.CreateTreeItem("ActionSample", type=ITEM_TYPE_ACTIONSAMPLE)
            treeItem.addChild(childActionSample)

            # 动作配置的其他节点
            childFileName = self.CreateTreeItem("FileName", value=actionSampleDict["fileName"], edit=True)
            childScreenWidth = self.CreateTreeItem("screenWidth", value=actionSampleDict["screenWidth"], edit=True)
            childScreenHeight = self.CreateTreeItem("screenHeight", value=actionSampleDict["screenHeight"], edit=True)
            childActionSample.addChild(childFileName)
            childActionSample.addChild(childScreenWidth)
            childActionSample.addChild(childScreenHeight)

            # element节点
            for actionDict in actionSampleDict["actions"]:
                childActionSample.addChild(self.CreateActionTreeItem(actionDict))

    '''
        根据输入的动作配置字典，生成相应的树结构
        输入参数：actionDict表示动作配置的字典
        输入参数actionTreeItem表示树结构所挂载的节点
    '''
    def LoadActionSample(self, actionDict, actionTreeItem):
        if actionTreeItem is None:
            self.logger.error('LoadActionSample failed, actionTreeItem is None')
            return

        if actionDict is None:
            self.logger.error('LoadActionSample failed, actionDict is None')
            return

        # 创建动作配置根目录的根节点
        childActionSampleRoot = self.CreateTreeItem("ActionSampleRoot", type=ITEM_TYPE_ACTIONSAMPLE_ROOT)
        actionTreeItem.addChild(childActionSampleRoot)

        # 创建其他节点
        childActionSampleRootDebug = self.CreateTreeItem(key='Debug')
        childActionSampleRoot.addChild(childActionSampleRootDebug)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText(str(actionDict["Debug"]))
        self.ui.treeWidget.setItemWidget(childActionSampleRootDebug, 1, qCombox)

        childActionSampleRoot.addChild(self.CreateTreeItem(key="GameName", value=actionDict["GameName"], edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameFPS", value=actionDict["FrameFPS"], edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameHeight", value=actionDict["FrameHeight"], edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="FrameWidth", value=actionDict["FrameWidth"], edit=True))
        childActionSampleRoot.addChild(self.CreateTreeItem(key="ActionCfgFile", value=actionDict["ActionCfgFile"], edit=True))

        childActionSampleRootOutPut = self.CreateTreeItem(key='OutputAsVideo')
        childActionSampleRoot.addChild(childActionSampleRootOutPut)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText(str(actionDict["OutputAsVideo"]))
        self.ui.treeWidget.setItemWidget(childActionSampleRootOutPut, 1, qCombox)

        childActionSampleRootLogTime = self.CreateTreeItem(key='LogTimestamp')
        childActionSampleRoot.addChild(childActionSampleRootLogTime)
        qCombox = QComboBox()
        qCombox.addItems([
            "True",
            "False"
        ])
        qCombox.setCurrentText(str(actionDict["LogTimestamp"]))
        self.ui.treeWidget.setItemWidget(childActionSampleRootLogTime, 1, qCombox)

        # 生成单个动作配置的树结构
        self.AddActionSample(actionDict["ActionSample"], childActionSampleRoot)

    '''
        根据动作字典，生成动作的树结构（element节点）
        输入参数：ActionDict表示动作的字典
    '''
    def CreateActionTreeItem(self, ActionDict):
        if ActionDict is None:
            self.logger.error('CreateActionTreeItem failed, ActionDict is None')
            return

        # 如果type不为none类型，则给element设置类型（ITEM_TYPE_ACTIONSAMPLE_ELEMENT）让它双击能导入图片
        # 如果type为none，则不给element类型，不用导入图片
        type = ActionDict['type']
        if type != 0:
            childActionItem = self.CreateTreeItem("element", type=ITEM_TYPE_ACTIONSAMPLE_ELEMENT)
        else:
            childActionItem = self.CreateTreeItem("element")

        # 从project.json中拿id的起始值
        if str(ActionDict["id"]) in self.projectDict["ActionSampleImagePath"].keys():
            childActionItem.setText(3, self.projectDict["ActionSampleImagePath"][str(ActionDict["id"])])

        # 创建其他节点
        childActionItem.addChild(self.CreateTreeItem(key="id", value=ActionDict["id"], edit=True))
        childActionItem.addChild(self.CreateTreeItem(key="name", value=ActionDict["name"], edit=True))

        childActionType = self.CreateTreeItem(key='type')
        childActionItem.addChild(childActionType)
        qCombox = QComboBox()
        qCombox.addItems([
            TYPE_ACTIONSAMPLE_NONE,
            TYPE_ACTIONSAMPLE_DOWN,
            TYPE_ACTIONSAMPLE_UP,
            TYPE_ACTIONSAMPLE_CLICK,
            TYPE_ACTIONSAMPLE_SWIPE
        ])
        qCombox.setCurrentText(ActionSampleMapType[ActionDict['type']])
        qCombox.currentTextChanged.connect(self.ActionSampleComboxChange)        # 修改下拉选项框时执行该函数
        self.ui.treeWidget.setItemWidget(childActionType, 1, qCombox)

        # 如果类型为swipe
        if type == 4:
            rectDict = {'x': ActionDict['startRectx'], 'y': ActionDict['startRecty'], 'w': ActionDict['startRectWidth'],
                        'h': ActionDict['startRectHeight']}
            childRectItem = self.CreateTreeItem('startRect')
            childActionItem.addChild(childRectItem)
            self.LoadRect(rectDict, childRectItem)

            rectDict = {'x': ActionDict['endRectx'], 'y': ActionDict['endRecty'],
                        'w': ActionDict['endRectWidth'], 'h': ActionDict['endRectHeight']}
            childRectItem = self.CreateTreeItem('endRect')
            childActionItem.addChild(childRectItem)
            self.LoadRect(rectDict, childRectItem)
        # 如果类型为none
        elif type == 0:
            pass
        else:
            rectDict = {'x': ActionDict['startRectx'], 'y': ActionDict['startRecty'],
                        'w': ActionDict['width'], 'h': ActionDict['height']}
            childRectItem = self.CreateTreeItem('startRect')
            childActionItem.addChild(childRectItem)
            self.LoadRect(rectDict, childRectItem)

        return childActionItem

    '''
        修改动作类型的时候触发的槽函数，生成不同的动作element
        输入参数：text表示修改后的值
    '''
    def ActionSampleComboxChange(self, text):
        if text not in [TYPE_ACTIONSAMPLE_NONE, TYPE_ACTIONSAMPLE_DOWN, TYPE_ACTIONSAMPLE_UP, TYPE_ACTIONSAMPLE_CLICK,
                        TYPE_ACTIONSAMPLE_SWIPE]:
            self.logger.error("ActionSampleComboxChange failed, text is {}".format(text))
            return

        # 获取修改的type的id
        treeItem = self.ui.treeWidget.currentItem()
        elementItem = treeItem.parent()
        actionSampleItem = elementItem.parent()
        id = self.GetChildItemValue(elementItem, 0, "id", 1)
        self.mainWindow.canvas.resetState()

        # 删除该element，并创建新的element插入到原来位置
        for itemIndex in range(actionSampleItem.childCount()):
            childItem = actionSampleItem.child(itemIndex)
            if childItem.text(0) == "element":
                if childItem.child(0).text(1) == id:
                    actionSampleItem.takeChild(itemIndex)

                    ActionDict = OrderedDict()
                    if text == TYPE_ACTIONSAMPLE_NONE:
                        ActionDict = self.GenerateActionNoneDict()
                    elif text == TYPE_ACTIONSAMPLE_DOWN:
                        ActionDict = self.GenerateActionDownDict()
                    elif text == TYPE_ACTIONSAMPLE_UP:
                        ActionDict = self.GenerateActionUpDict()
                    elif text == TYPE_ACTIONSAMPLE_CLICK:
                        ActionDict = self.GenerateActionClickDict()
                    elif text == TYPE_ACTIONSAMPLE_SWIPE:
                        ActionDict = self.GenerateActionDragDict()

                    childActionItem = self.CreateActionTreeItem(ActionDict)
                    actionSampleItem.insertChild(itemIndex, childActionItem)
                    childActionItem.setExpanded(True)
                    break

    '''
        返回none类型的字典
    '''
    def GenerateActionNoneDict(self):
        ActionDict = OrderedDict()
        ActionDict['startRectx'] = 0
        ActionDict['startRecty'] = 0
        ActionDict['width'] = 0
        ActionDict['height'] = 0
        ActionDict['type'] = 0
        ActionDict['id'] = 0
        ActionDict["name"] = str()
        return ActionDict

    '''
        返回down类型的字典
    '''
    def GenerateActionDownDict(self):
        ActionDict = OrderedDict()
        ActionDict['startRectx'] = 0
        ActionDict['startRecty'] = 0
        ActionDict['width'] = 0
        ActionDict['height'] = 0
        ActionDict['type'] = 1
        ActionDict['id'] = self.ActionIDIndex
        ActionDict["name"] = str()
        self.ActionIDIndex += 1
        return ActionDict

    '''
        返回up类型的字典
    '''
    def GenerateActionUpDict(self):
        ActionDict = OrderedDict()
        ActionDict['startRectx'] = 0
        ActionDict['startRecty'] = 0
        ActionDict['width'] = 0
        ActionDict['height'] = 0
        ActionDict['type'] = 2
        ActionDict['id'] = self.ActionIDIndex
        ActionDict["name"] = str()
        self.ActionIDIndex += 1
        return ActionDict

    '''
        返回click类型字典
    '''
    def GenerateActionClickDict(self):
        ActionDict = OrderedDict()
        ActionDict['startRectx'] = 0
        ActionDict['startRecty'] = 0
        ActionDict['width'] = 0
        ActionDict['height'] = 0
        ActionDict['type'] = 3
        ActionDict['id'] = self.ActionIDIndex
        ActionDict["name"] = str()
        self.ActionIDIndex += 1
        return ActionDict

    '''
        返回swipe类型字典
    '''
    def GenerateActionDragDict(self):
        ActionDict = OrderedDict()
        ActionDict['startRectx'] = 0
        ActionDict['startRecty'] = 0
        ActionDict['startRectWidth'] = 0
        ActionDict['startRectHeight'] = 0
        ActionDict['endRectx'] = 0
        ActionDict['endRecty'] = 0
        ActionDict['endRectWidth'] = 0
        ActionDict['endRectHeight'] = 0
        ActionDict['type'] = 4
        ActionDict['id'] = self.ActionIDIndex
        ActionDict["name"] = str()
        self.ActionIDIndex += 1
        return ActionDict

    def AddActionSampleSingle(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddActionSampleSingle failed, treeItem is None')
            return

        ActionSampleDict = self.GenerateActionClickDict()
        treeItem.addChild(self.CreateActionTreeItem(ActionSampleDict))

    '''
        将动作配置的根目录的树结构转换为字典，返回给mainwindow
    '''
    def SaveActionSampleRootFile(self):
        actionSampleJsonDict = OrderedDict()
        topLevelItem = self.ui.treeWidget.topLevelItem(0)

        if topLevelItem is None:
            return

        '''
            遍历每个version
        '''
        for versionIndex in range(topLevelItem.childCount()):
            versionItem = topLevelItem.child(versionIndex)
            if versionItem.text(0) in ["project.json", "project.json~"]:
                continue

            actionSampleRootVersionDict = OrderedDict()
            for sceneIndex in range(versionItem.childCount()):
                sceneItem = versionItem.child(sceneIndex)
                sceneKey = sceneItem.text(0)
                # 如果key为ActionSampleRoot才处理
                if sceneKey == "ActionSampleRoot":
                    item = self.GetChildItemValue(sceneItem, 0, "Debug", 1)
                    # 填充字段
                    actionSampleRootVersionDict['Debug'] = item.currentText() == "True"
                    actionSampleRootVersionDict['GameName'] = sceneItem.child(1).text(1)
                    actionSampleRootVersionDict['FrameFPS'] = int(sceneItem.child(2).text(1))
                    actionSampleRootVersionDict['FrameHeight'] = int(sceneItem.child(3).text(1))
                    actionSampleRootVersionDict['FrameWidth'] = int(sceneItem.child(4).text(1))
                    actionSampleRootVersionDict['ActionCfgFile'] = sceneItem.child(5).text(1)
                    item = self.GetChildItemValue(sceneItem, 0, "OutputAsVideo", 1)
                    actionSampleRootVersionDict['OutputAsVideo'] = item.currentText() == "True"
                    item = self.GetChildItemValue(sceneItem, 0, "LogTimestamp", 1)
                    actionSampleRootVersionDict['LogTimestamp'] = item.currentText() == "True"
                    actionSampleRootVersionDict['ActionSample'] = list()

                    # 处理每个动作element
                    for itemIndex in range(sceneItem.childCount()):
                        childItem = sceneItem.child(itemIndex)
                        if childItem.text(0) == "ActionSample":
                            actionSampleRootVersionDict['ActionSample'].append(self.SaveActionSampleFile(childItem))

            actionSampleJsonDict[versionItem.text(0)] = actionSampleRootVersionDict
        return actionSampleJsonDict

    '''
        将动作的element转换为字典
    '''
    def SaveActionSampleFile(self, sceneItem):
        # 填充字段
        actionSampleVersionDict = OrderedDict()
        actionSampleVersionDict['fileName'] = sceneItem.child(0).text(1)
        actionSampleVersionDict['screenWidth'] = int(sceneItem.child(1).text(1))
        actionSampleVersionDict['screenHeight'] = int(sceneItem.child(2).text(1))
        actionSampleVersionDict['actions'] = list()

        # 对于每个element都做处理
        for itemIndex in range(sceneItem.childCount()):
            childItem = sceneItem.child(itemIndex)
            if childItem.text(0) == "element":
                # 填充element中某些字段值
                actionSingleDict = OrderedDict()
                actionSingleDict['id'] = int(childItem.child(0).text(1))
                self.mainWindow.projectDict['ActionSampleImagePath'][str(actionSingleDict['id'])] = childItem.text(3)
                actionSingleDict['name'] = childItem.child(1).text(1)
                combox = self.ui.treeWidget.itemWidget(childItem.child(2), 1)
                actionSingleDict['type'] = ActionSampleMapIndex[combox.currentText()]

                # 如果type为swipe时
                if actionSingleDict['type'] == 4:
                    actionSingleDict['startRectx'] = int(childItem.child(3).child(0).text(1))
                    actionSingleDict['startRecty'] = int(childItem.child(3).child(1).text(1))
                    actionSingleDict['startRectWidth'] = int(childItem.child(3).child(2).text(1))
                    actionSingleDict['startRectHeight'] = int(childItem.child(3).child(3).text(1))

                    actionSingleDict['endRectx'] = int(childItem.child(4).child(0).text(1))
                    actionSingleDict['endRecty'] = int(childItem.child(4).child(1).text(1))
                    actionSingleDict['endRectWidth'] = int(childItem.child(4).child(2).text(1))
                    actionSingleDict['endRectHeight'] = int(childItem.child(4).child(3).text(1))
                # 如果type为none时
                elif actionSingleDict['type'] == 0:
                    pass
                else:
                    actionSingleDict['startRectx'] = int(childItem.child(3).child(0).text(1))
                    actionSingleDict['startRecty'] = int(childItem.child(3).child(1).text(1))
                    actionSingleDict['width'] = int(childItem.child(3).child(2).text(1))
                    actionSingleDict['height'] = int(childItem.child(3).child(3).text(1))

                actionSampleVersionDict['actions'].append(actionSingleDict)

        return actionSampleVersionDict

