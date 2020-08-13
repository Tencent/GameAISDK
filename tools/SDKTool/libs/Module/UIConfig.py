# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from libs.Module.AbstractModule import *
from libs.shape import *
from libs.confirmDialog import *


DEVICE_CLOSE_ICON_NAME = "devicesCloseIcons"


class CUIConfig(AbstractModule):
    def __init__(self, MainWindow=None, ui=None):
        AbstractModule.__init__(self, MainWindow, ui)

        # 添加UI动作，与MainWindow中的右键菜单绑定
        self.actionAddUI = QAction(MainWindow)
        self.actionAddUI.setText("添加UI")
        self.actionAddUI.triggered.connect(self.AddUI)

        # 添加GameOver元素动作，与MainWindow中的右键菜单绑定
        self.actionAddGameOver = QAction(MainWindow)
        self.actionAddGameOver.setText("添加元素")
        self.actionAddGameOver.triggered.connect(self.AddGameOverElement)

        # 添加closeIcon元素动作，与MainWindow中的右键菜单绑定
        self.actionAddCloseIcon = QAction(MainWindow)
        self.actionAddCloseIcon.setText("添加元素")
        self.actionAddCloseIcon.triggered.connect(self.AddCloseIconsElement)

        # 添加DeviceCloseIcon元素动作，与MainWindow中的右键菜单绑定
        self.actionAddDevicesCloseIcon = QAction(MainWindow)
        self.actionAddDevicesCloseIcon.setText("添加元素")
        self.actionAddDevicesCloseIcon.triggered.connect(self.AddDevicesCloseIcon)

        # 添加uistates元素动作，与MainWindow中的右键菜单绑定
        self.actionAddUIState = QAction(MainWindow)
        self.actionAddUIState.setText("添加元素")
        self.actionAddUIState.triggered.connect(self.AddUIStatesElement)

        # 添加ID动作，与MainWindow中的右键菜单绑定
        self.actionAddUIStateID = QAction(MainWindow)
        self.actionAddUIStateID.setText("添加ID")
        self.actionAddUIStateID.triggered.connect(self.AddUIStateID)

        # 添加ID动作，与MainWindow中的右键菜单绑定
        self.actionAddScriptTask = QAction(MainWindow)
        self.actionAddScriptTask.setText("添加task")
        self.actionAddScriptTask.triggered.connect(self.ADDUIScriptTaskElement)

        self.LoadUIFunc = OrderedDict()
        self.LoadUIFunc[TYPE_UIACTION_CLICK] = self.CreateUIClickItem
        self.LoadUIFunc[TYPE_UIACTION_DRAG] = self.CreateUIDragItem
        self.LoadUIFunc[TYPE_UIACTION_DRAGCHECK] = self.CreateUIDragCheckItem
        self.LoadUIFunc[TYPE_UIACTION_SCRIPT] = self.CreateUIScriptItem

        self.LoadGameOverFunc = OrderedDict()
        self.LoadGameOverFunc[TYPE_UIACTION_CLICK] = self.CreateGameOverClickItem
        self.LoadGameOverFunc[TYPE_UIACTION_DRAG] = self.CreateGameOverDragItem

        self.UIGameOverIDIndex = 1
        self.UICloseIconsIDIndex = 1
        self.UIDevicesCloseIconsIDIndex = 1
        self.UIStatesIDIndex = 1
        self.UIScriptIDIndex = dict()
        self.UIScriptIDIndex[self.UIStatesIDIndex] = 1
        self.LineText = None

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
        if "shift" not in ROIJsonDict.keys():
            ROIJsonDict["shift"] = DEFAULT_UI_SHIFT

        if "templateThreshold" not in ROIJsonDict.keys():
            ROIJsonDict["templateThreshold"] = DEFAULT_TEMPLATE_THRESHOLD

        treeItemROI.addChild(self.CreateTreeItem(key='x', value=ROIJsonDict["x"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='y', value=ROIJsonDict["y"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='w', value=ROIJsonDict["w"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='h', value=ROIJsonDict["h"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='shift', value=ROIJsonDict["shift"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='templateThreshold', value=ROIJsonDict["templateThreshold"],
                                                 edit=True))

    def SetProjectDict(self, projectDict=None):
        self.projectDict = projectDict

        self.UIGameOverIDIndex = self.projectDict[
            "GameOverIDStart"] if "GameOverIDStart" in self.projectDict.keys() is not None else 1

        self.UICloseIconsIDIndex = self.projectDict[
            "CloseIconIDStart"] if "CloseIconIDStart" in self.projectDict.keys() is not None else 1

        self.UIDevicesCloseIconsIDIndex = self.projectDict[
            "DeviceCloseIDStart"] if "DeviceCloseIDStart" in self.projectDict.keys() is not None else 1

        self.UIStatesIDIndex = self.projectDict[
            "UIStatesIDStart"] if "UIStatesIDStart" in self.projectDict.keys() is not None else 1

        self.UIScriptIDIndex[self.UIStatesIDIndex] = 1

    '''
        将UI树转换为字典，返回给mainWindow
        返回值：UI字典
    '''
    def SaveUITree(self):
        UIDict = OrderedDict()
        topLevelItem = self.ui.treeWidget.topLevelItem(0)

        if topLevelItem is None:
            return

        for versionIndex in range(topLevelItem.childCount()):
            versionItem = topLevelItem.child(versionIndex)
            if versionItem.text(0) in ["project.json", "project.json~"]:
                continue

            UIVersionDict = OrderedDict()
            for sceneIndex in range(versionItem.childCount()):
                sceneItem = versionItem.child(sceneIndex)
                sceneKey = sceneItem.text(0)
                if sceneKey == "UI":
                    UIVersionDict = self.UITree2Dict(sceneItem)
            UIDict[versionItem.text(0)] = UIVersionDict
        return UIDict

    '''
        将UI树转换为字典
        输入参数：UI的根节点
        返回值：UI字典
    '''
    def UITree2Dict(self, treeItem):
        if treeItem is None:
            self.logger.error("UITree2Dict failed, treeItem is None")
            return

        # 获取json中的各个字段的item
        DebugItem = treeItem.child(0)
        ShowImageItem = treeItem.child(1)
        SaveResultItem = treeItem.child(2)
        ShowSaveResultItem = treeItem.child(3)
        MatchStartStateItem = treeItem.child(4)
        MatchEndStateFromUIStatesItem = treeItem.child(5)
        CheckCloseIconsWhenPlayingItem = treeItem.child(6)
        GameOverItem = treeItem.child(7)
        CloseIconsItem = treeItem.child(8)
        DeviceCloseItem = treeItem.child(9)
        UIStatesItem = treeItem.child(10)

        # 填充字段值
        UIDict = OrderedDict()
        combox = self.ui.treeWidget.itemWidget(DebugItem, 1)
        UIDict["debugWithSDKTools"] = combox.currentText() == "True"
        combox = self.ui.treeWidget.itemWidget(ShowImageItem, 1)
        UIDict["showImage"] = combox.currentText() == "True"
        combox = self.ui.treeWidget.itemWidget(SaveResultItem, 1)
        UIDict["saveResult"] = combox.currentText() == "True"
        combox = self.ui.treeWidget.itemWidget(ShowSaveResultItem, 1)
        UIDict["showSaveResult"] = combox.currentText() == "True"
        UIDict["matchStartState"] = list()
        UIDict["matchEndStateFromUIStates"] = list()
        combox = self.ui.treeWidget.itemWidget(CheckCloseIconsWhenPlayingItem, 1)
        UIDict["checkCloseIconsWhenPlaying"] = combox.currentText() == "True"
        UIDict["gameOver"] = list()
        UIDict["closeIcons"] = list()
        UIDict[DEVICE_CLOSE_ICON_NAME] = list()
        UIDict["uiStates"] = list()

        # 遍历MatchStartStateItem填充id
        for itemIndex in range(MatchStartStateItem.childCount()):
            idItem = MatchStartStateItem.child(itemIndex)
            idDict = {"id": int(idItem.text(1))}
            UIDict["matchStartState"].append(idDict)

        for itemIndex in range(MatchEndStateFromUIStatesItem.childCount()):
            idItem = MatchEndStateFromUIStatesItem.child(itemIndex)
            idDict = {"id": int(idItem.text(1))}
            UIDict["matchEndStateFromUIStates"].append(idDict)
            # UIDict["matchEndStateFromUIStates"].append(int(idItem.text(1)))

        # 遍历填充GameOver的字典
        for itemIndex in range(GameOverItem.childCount()):
            elementItem = GameOverItem.child(itemIndex)
            elementDict = OrderedDict()
            elementDict["id"] = int(self.GetChildItemValue(elementItem, 0, "id", 1))
            if "gameOver" in self.mainWindow.projectDict["UIImagePath"].keys():
                self.mainWindow.projectDict["UIImagePath"]["gameOver"][str(elementDict["id"])] = elementItem.text(3)
            elif "GameOver" in self.mainWindow.projectDict["UIImagePath"].keys():
                self.mainWindow.projectDict["UIImagePath"]["GameOver"][str(elementDict["id"])] = elementItem.text(3)
            combox = self.GetChildItemValue(elementItem, 0, "actionType", 1)
            elementDict["actionType"] = combox.currentText()
            elementDict["desc"] = self.GetChildItemValue(elementItem, 0, "desc", 1)
            elementDict["imgPath"] = self.GetChildItemValue(elementItem, 0, "imgPath", 1)
            self._UIROITree2Dict(elementItem.child(4), elementDict)
            elementDict["shift"] = int(self.GetChildItemValue(elementItem, 0, "shift", 1))
            self.UIActionTree2Dict(elementItem.child(6), elementDict)
            UIDict["gameOver"].append(elementDict)

        # 遍历填充closeIcon的字典
        for itemIndex in range(CloseIconsItem.childCount()):
            elementItem = CloseIconsItem.child(itemIndex)
            elementDict = OrderedDict()
            elementDict["id"] = int(self.GetChildItemValue(elementItem, 0, "id", 1))
            if "closeIcons" in self.mainWindow.projectDict["UIImagePath"].keys():
                self.mainWindow.projectDict["UIImagePath"]["closeIcons"][str(elementDict["id"])] = elementItem.text(3)
            elif "CloseIcons" in self.mainWindow.projectDict["UIImagePath"].keys():
                self.mainWindow.projectDict["UIImagePath"]["CloseIcons"][str(elementDict["id"])] = elementItem.text(3)
            elementDict["desc"] = self.GetChildItemValue(elementItem, 0, "desc", 1)
            elementDict["imgPath"] = self.GetChildItemValue(elementItem, 0, "imgPath", 1)
            self._UIROITree2Dict(elementItem.child(3), elementDict, True)
            UIDict["closeIcons"].append(elementDict)

        for itemIndex in range(DeviceCloseItem.childCount()):
            elementItem = DeviceCloseItem.child(itemIndex)
            elementDict = OrderedDict()
            elementDict["id"] = int(self.GetChildItemValue(elementItem, 0, "id", 1))
            imgPath = elementItem.text(3)
            if DEVICE_CLOSE_ICON_NAME in self.mainWindow.projectDict["UIImagePath"].keys():
                self.mainWindow.projectDict["UIImagePath"][DEVICE_CLOSE_ICON_NAME][str(elementDict["id"])] = imgPath
            else:
                self.mainWindow.projectDict["UIImagePath"][DEVICE_CLOSE_ICON_NAME] = dict()
                self.mainWindow.projectDict["UIImagePath"][DEVICE_CLOSE_ICON_NAME][str(elementDict["id"])] = imgPath

            elementDict["desc"] = self.GetChildItemValue(elementItem, 0, "desc", 1)
            elementDict["imgPath"] = self.GetChildItemValue(elementItem, 0, "imgPath", 1)
            self._UIROITree2Dict(elementItem.child(3), elementDict, True)
            UIDict[DEVICE_CLOSE_ICON_NAME].append(elementDict)

        # 遍历填充UIStates的字典
        for itemIndex in range(UIStatesItem.childCount()):
            elementItem = UIStatesItem.child(itemIndex)
            elementDict = OrderedDict()
            self._SaveUICommonItem(elementItem, elementDict)

            if elementDict["actionType"] in [TYPE_UIACTION_CLICK, TYPE_UIACTION_DRAG]:
                item = self.GetChildItem(elementItem, "action")
                self.UIActionTree2Dict(item, elementDict)

            elif elementDict["actionType"] in [TYPE_UIACTION_DRAGCHECK]:
                self.UIDragCheck2Dict(elementItem, elementDict)

            elif elementDict["actionType"] in [TYPE_UIACTION_SCRIPT]:
                self.UIScript2Dict(elementItem, elementDict)
            else:
                if elementDict["template"] == 1:
                    self.UIActionTree2Dict(elementItem.child(8), elementDict)
                else:
                    self.UIActionTree2Dict(elementItem.child(7), elementDict)

            elementDict["checkSameFrameCnt"] = int(self.GetChildItemValue(elementItem, 0, "checkSameFrameCnt", 1))
            elementDict["delete"] = int(self.GetChildItemValue(elementItem, 0, "delete", 1))
            UIDict["uiStates"].append(elementDict)

        return UIDict

    def _SaveUICommonItem(self, elementItem, elementDict):
        elementDict["id"] = int(self.GetChildItemValue(elementItem, 0, "id", 1))
        if "uiStates" in self.mainWindow.projectDict["UIImagePath"].keys():
            self.mainWindow.projectDict["UIImagePath"]["uiStates"][str(elementDict["id"])] = elementItem.text(3)
        elif "UIStates" in self.mainWindow.projectDict["UIImagePath"].keys():
            self.mainWindow.projectDict["UIImagePath"]["UIStates"][str(elementDict["id"])] = elementItem.text(3)
        combox = self.GetChildItemValue(elementItem, 0, "actionType", 1)
        elementDict["actionType"] = combox.currentText()
        elementDict["desc"] = self.GetChildItemValue(elementItem, 0, "desc", 1)
        elementDict["imgPath"] = self.GetChildItemValue(elementItem, 0, "imgPath", 1)

        elementDict["keyPoints"] = int(self.GetChildItemValue(elementItem, 0, "keyPoints", 1))
        lineText = self.GetChildItemValue(elementItem, 0, "template", 1)
        if lineText == '':
            lineText = '0'
        elementDict["template"] = int(lineText)

        if elementDict["template"] == 0:
            elementDict["shift"] = int(self.GetChildItemValue(elementItem, 0, "shift", 1))
            self.UIActionTree2Dict(elementItem.child(7), elementDict)
        elif elementDict["template"] == 1:
            elementDict["shift"] = int(self.GetChildItemValue(elementItem, 0, "shift", 1))
            self._UIROITree2Dict(elementItem.child(5), elementDict)
            # self.UIActionTree2Dict(elementItem.child(8), elementDict)
        else:
            self._UIROISTree2Dict(elementItem, elementDict)
        # elementDict["shift"] = int(self.GetChildItemValue(elementItem, 0, "shift", 1))

    '''
        UI的ROI树转换为字典
        输入参数：treeItem，ROI树的根节点
        输入参数：isCloseIcon表示是否为closeIcon的ROI
        输出参数：UIDict表示填充的字典
    '''
    def _UIROITree2Dict(self, treeItem, UIDict, isCloseIcon=False):
        if treeItem is None:
            self.logger.error("UITree2Dict failed, treeItem is None")
            return

        if UIDict is None:
            self.logger.error("UITree2Dict failed, UIDict is None")
            return

        UIDict["x"] = int(self.GetChildItemValue(treeItem, 0, "x", 1))
        UIDict["y"] = int(self.GetChildItemValue(treeItem, 0, "y", 1))
        if isCloseIcon:
            UIDict["width"] = int(self.GetChildItemValue(treeItem, 0, "w", 1))
            UIDict["height"] = int(self.GetChildItemValue(treeItem, 0, "h", 1))
        else:
            UIDict["w"] = int(self.GetChildItemValue(treeItem, 0, "w", 1))
            UIDict["h"] = int(self.GetChildItemValue(treeItem, 0, "h", 1))

    def _UIROISTree2Dict(self, treeItem, UIDict):
        if None in [treeItem, UIDict]:
            self.logger.error("input param {},{} is invalid, please check".format(treeItem, UIDict))
            return
        UIDict["templateOp"] = self.GetChildItemValue(treeItem, 0, "templateOp", 1)
        roiId = 1
        for index in range(treeItem.childCount()):
            item = treeItem.child(index)
            content = item.text(0)
            if content == "ROI":
                xname = "x{}".format(roiId)
                yname = "y{}".format(roiId)
                wname = "w{}".format(roiId)
                hname = "h{}".format(roiId)
                shiftname = "shift{}".format(roiId)
                tmplThrName = "templateThreshold{}".format(roiId)
                UIDict[xname] = self.GetChildItemValue(item, 0, "x", 1)
                UIDict[yname] = self.GetChildItemValue(item, 0, "y", 1)
                UIDict[wname] = self.GetChildItemValue(item, 0, "w", 1)
                UIDict[hname] = self.GetChildItemValue(item, 0, "h", 1)
                UIDict[shiftname] = self.GetChildItemValue(item, 0, "shift", 1)
                UIDict[tmplThrName] = self.GetChildItemValue(item, 0, "templateThreshold", 1)
                roiId += 1

    '''
        UI的DragCheck动作转换为dict
        输入参数：treeItem表示根节点
        输出参数：UIDict为将填充的字典
    '''
    def UIDragCheck2Dict(self, treeItem, UIDict):
        if treeItem is None:
            self.logger.error("UIDragCheck2Dict failed, treeItem is None")
            return

        if UIDict is None:
            self.logger.error("UIDragCheck2Dict failed, UIDict is None")
            return

        actionDirCombox = self.GetChildItemValue(treeItem, 0, "actionDir", 1)
        if actionDirCombox is not None:
            UIDict["actionDir"] = actionDirCombox.currentText()

        dragPointItem = self.GetChildItem(treeItem, "dragPoint")
        dragX = dragPointItem.child(0).text(1)
        UIDict["dragX"] = int(dragX)
        dragY = dragPointItem.child(1).text(1)
        UIDict["dragY"] = int(dragY)

        UIDict["dragLen"] = int(self.GetChildItem(treeItem, "dragLen").text(1))

        targetItem = self.GetChildItem(treeItem, "target")
        UIDict["targetImg"] = targetItem.child(0).text(1)
        targetROIItem = targetItem.child(1)
        UIDict["targetX"] = int(targetROIItem.child(0).text(1))
        UIDict["targetY"] = int(targetROIItem.child(1).text(1))
        UIDict["targetW"] = int(targetROIItem.child(2).text(1))
        UIDict["targetH"] = int(targetROIItem.child(3).text(1))

    def UIScript2Dict(self, treeItem, UIDict):
        if treeItem is None:
            self.logger.error("UIScript2Dict failed, treeItem is None")
            return

        if UIDict is None:
            self.logger.error("UIScript2Dict failed, UIDict is None")
            return

        UIDict["scriptPath"] = self.GetChildItemValue(treeItem, 0, "scriptPath", 1)
        tasksItem = self.GetChildItem(treeItem, "tasks")
        UIDict["tasks"] = []

        for index in range(tasksItem.childCount()):
            task = tasksItem.child(index)
            taskDict = dict()
            taskDict["taskid"] = int(self.GetChildItemValue(task, 0, "taskid", 1))
            combox = self.GetChildItemValue(task, 0, "type", 1)
            taskDict["duringTimeMs"] = int(self.GetChildItemValue(task, 0, "duringTimeMs", 1) or 100)
            taskDict["sleepTimeMs"] = int(self.GetChildItemValue(task, 0,  "sleepTimeMs", 1))

            taskDict["type"] = combox.currentText()
            actionItem = self.GetChildItem(task, "action")
            if taskDict["type"] in [TYPE_UIACTION_CLICK]:
                self._UIClickAction2Dict(actionItem, taskDict)
            elif taskDict["type"] in [TYPE_UIACTION_DRAG]:
                self._UIDragAction2Dict(actionItem, taskDict)
            else:
                logging.error("invalid action type {}".format(taskDict["type"]))

            UIDict["tasks"].append(taskDict)

    def _UIClickAction2Dict(self, treeItem, UIDict):
        # not only get the value but also transfer type
        # names = ['actionX', 'actionY', 'actionThreshold',
        #          'actionTmplExpdWPixel', 'actionTmplExpdHPixel',
        #          'actionROIExpdWRatio', 'actionROIExpdHRatio']
        # for name in names:
        #     value = self.GetChildItemValue(treeItem, 0, name, 1)
        #     if name is not None:
        #         UIDict[name] = value

        UIDict['actionX'] = int(self.GetChildItemValue(treeItem, 0, 'actionX', 1) or 0)
        UIDict['actionY'] = int(self.GetChildItemValue(treeItem, 0, 'actionY', 1) or 0)
        UIDict['actionThreshold'] = float(self.GetChildItemValue(treeItem, 0, 'actionThreshold', 1)
                                          or DEFAULT_TEMPLATE_THRESHOLD)
        UIDict['actionTmplExpdWPixel'] = int(self.GetChildItemValue(treeItem, 0, 'actionTmplExpdWPixel', 1)
                                             or DEFAULT_TMPL_EXPD_W_PIXEL)
        UIDict['actionTmplExpdHPixel'] = int(self.GetChildItemValue(treeItem, 0, 'actionTmplExpdHPixel', 1)
                                             or DEFAULT_TMPL_EXPD_H_PIXEL)
        UIDict['actionROIExpdWRatio'] = float(self.GetChildItemValue(treeItem, 0, 'actionROIExpdWRatio', 1)
                                              or DEFAULT_EXPD_W_RATIO)
        UIDict['actionROIExpdHRatio'] = float(self.GetChildItemValue(treeItem, 0, 'actionROIExpdHRatio', 1)
                                              or DEFAULT_EXPD_H_RATIO)

    def _UIDragAction2Dict(self, treeItem, UIDict):
        # drag action have two drag points
        # not only get the value but also transfer type
        for index in [1, 2]:
            name = "actionX{}".format(index)
            UIDict[name] = int(self.GetChildItemValue(treeItem, 0, name, 1) or 0)

            name = "actionY{}".format(index)
            UIDict[name] = int(self.GetChildItemValue(treeItem, 0, name, 1) or 0)

            name = "actionThreshold{}".format(index)
            UIDict[name] = float(self.GetChildItemValue(treeItem, 0, name, 1) or DEFAULT_TEMPLATE_THRESHOLD)

            name = "actionTmplExpdWPixel{}".format(index)
            UIDict[name] = int(self.GetChildItemValue(treeItem, 0, name, 1) or DEFAULT_TMPL_EXPD_W_PIXEL)

            name = "actionTmplExpdHPixel{}".format(index)
            UIDict[name] = int(self.GetChildItemValue(treeItem, 0, name, 1) or DEFAULT_TMPL_EXPD_H_PIXEL)

            name = "actionROIExpdWRatio{}".format(index)
            UIDict[name] = float(self.GetChildItemValue(treeItem, 0, name, 1) or DEFAULT_EXPD_W_RATIO)

            name = "actionROIExpdHRatio{}".format(index)
            UIDict[name] = float(self.GetChildItemValue(treeItem, 0, name, 1) or DEFAULT_EXPD_H_RATIO)

    '''
        UI的动作树结构转换为字典
        输入参数：treeItem表示根节点
        输出参数：UIDict为将填充的字典
    '''
    def UIActionTree2Dict(self, treeItem, UIDict):
        if treeItem is None:
            self.logger.error("UIActionTree2Dict failed, treeItem is None")
            return

        if UIDict is None:
            self.logger.error("UIActionTree2Dict failed, UIDict is None")
            return
        names = ['actionX', 'actionY', 'actionThreshold',
                 'actionTmplExpdWPixel', 'actionTmplExpdHPixel',
                 'actionROIExpdWRatio', 'actionROIExpdHRatio']
        
        IntNames = ['actionX', 'actionY', 'actionTmplExpdWPixel', 'actionTmplExpdHPixel']
        floatNames = ['actionThreshold', 'actionROIExpdWRatio', 'actionROIExpdHRatio']
        for index in [1, 2]:
            id = index

            nameActionX = "actionX{}".format(id)
            names.append(nameActionX)
            IntNames.append(nameActionX)

            nameActionY = "actionY{}".format(id)
            names.append(nameActionY)
            IntNames.append(nameActionY)

            nameThreshold = "actionThreshold{}".format(id)
            names.append(nameThreshold)
            floatNames.append(nameThreshold)

            nameActionTmplExpdWPixel = "actionTmplExpdWPixel{}".format(id)
            names.append(nameActionTmplExpdWPixel)
            IntNames.append(nameActionTmplExpdWPixel)

            nameActionTmplExpdHPixel = "actionTmplExpdHPixel{}".format(id)
            names.append(nameActionTmplExpdHPixel)
            IntNames.append(nameActionTmplExpdHPixel)

            nameActionROIExpdWRatio = "actionROIExpdWRatio{}".format(id)
            names.append(nameActionROIExpdWRatio)
            floatNames.append(nameActionROIExpdWRatio)

            nameActionROIExpdHRatio = "actionROIExpdHRatio{}".format(id)
            names.append(nameActionROIExpdHRatio)
            floatNames.append(nameActionROIExpdHRatio)

        for name in names:
            value = self.GetChildItemValue(treeItem, 0, name, 1)
            if value is None:
                continue
                
            if name in IntNames:
                UIDict[name] = int(value)
            elif name in floatNames:
                UIDict[name] = float(value)
            else:
                raise Exception('type of name {} is unkonwn'.format(name))

    '''
        根据导入的UI字典，生成对应的UI树结构
        输入参数：UIJsonDict表示UI的字典
        输入参数：treeItemVersion表示version节点，UI树将作为其子节点
    '''
    def LoadUIJson(self, UIJsonDict, treeItemVersion):
        if UIJsonDict is None:
            self.logger.error("LoadUIJson failed, UIJsonDict is None")
            return

        if treeItemVersion is None:
            self.logger.error("LoadUIJson failed, treeItemVersion is None")
            return

        # 创建UI根节点
        child = self.CreateTreeItem(key='UI')
        treeItemVersion.addChild(child)

        # 创建UI的一些列子节点
        self.CreateDebugWithSDKTool(child, self._GetDictValue(UIJsonDict, ["DebugWithSDKTools", "debugWithSDKTools"]))
        self.CreateShowImageItem(child, self._GetDictValue(UIJsonDict, ["ShowImage", "showImage"]))
        self.CreateSaveResultItem(child, self._GetDictValue(UIJsonDict, ["SaveResult", "saveResult"]))
        self.CreateShowSaveResultItem(child, self._GetDictValue(UIJsonDict, ["ShowSaveResult", "showSaveResult"]))
        self.CreateMatchStartStateItem(child, self._GetDictValue(UIJsonDict, ["MatchStartState", "matchStartState"]))
        self.CreateMatchEndStateFromUIStatesItem(child, self._GetDictValue(UIJsonDict, ["MatchEndStateFromUIStates",
                                                                                        "matchEndStateFromUIStates"]))
        self.CreateCheckCloseIconsWhenPlayingItem(child, self._GetDictValue(UIJsonDict, ["CheckCloseIconsWhenPlaying",
                                                                                         "checkCloseIconsWhenPlaying"]))

        # GameOver节点的创建
        childGameOver = self.CreateTreeItem(key='gameOver', type=ITEM_TYPE_GAMEOVER)
        for value in self._GetDictValue(UIJsonDict, ["GameOver", "gameOver"]):
            childGameOver.addChild(self.CreateGameOverItem(value))
        child.addChild(childGameOver)

        # closeIcon节点的创建
        childCloseIcon = self.CreateTreeItem(key='closeIcons', type=ITEM_TYPE_CLOSEICONS)
        for value in self._GetDictValue(UIJsonDict, ["CloseIcons", "closeIcons"]):
            childCloseIcon.addChild(self.CreateCloseIconsItem(value))
        child.addChild(childCloseIcon)

        deviceCloseIcons = self.CreateTreeItem(key=DEVICE_CLOSE_ICON_NAME, type=ITEM_TYPE_CLOSEICONS)
        for value in self._GetDictValue(UIJsonDict, [DEVICE_CLOSE_ICON_NAME]) or []:
            deviceCloseIcons.addChild(self.CreateDeviceCloseIconsItem(value))
        child.addChild(deviceCloseIcons)

        # UIStates节点的创建
        childUIStates = self.CreateTreeItem(key='uiStates', type=ITEM_TYPE_UISTATES)
        for value in self._GetDictValue(UIJsonDict, ["UIStates", "uiStates"]):
            childUIStates.addChild(self.CreateUIStatesItem(value))
        child.addChild(childUIStates)

    '''
        创建UI树
        都用默认的值
    '''
    def AddUI(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddUI failed, treeItem is None')
            return

        # 创建UI树的根节点
        child = self.CreateTreeItem(key='UI')
        treeItem.addChild(child)

        # 填充默认值
        UIDict = OrderedDict()
        UIDict["debugWithSDKTools"] = False
        UIDict["showImage"] = False
        UIDict["saveResult"] = False
        UIDict["showSaveResult"] = False
        UIDict["matchStartState"] = list()
        UIDict["matchEndStateFromUIStates"] = list()
        UIDict["checkCloseIconsWhenPlaying"] = True
        UIDict["gameOver"] = list()
        UIDict["gameOver"].append(OrderedDict())
        UIDict["gameOver"][0]["id"] = self.UIGameOverIDIndex
        self.UIGameOverIDIndex += 1
        UIDict["gameOver"][0]["actionType"] = TYPE_UIACTION_CLICK
        UIDict["gameOver"][0]["x"] = 0
        UIDict["gameOver"][0]["y"] = 0
        UIDict["gameOver"][0]["w"] = 0
        UIDict["gameOver"][0]["h"] = 0
        UIDict["gameOver"][0]["imgPath"] = ""
        UIDict["gameOver"][0]["desc"] = ""
        UIDict["gameOver"][0]["shift"] = DEFAULT_UI_SHIFT
        UIDict["gameOver"][0]["actionX"] = 0
        UIDict["gameOver"][0]["actionY"] = 0

        UIDict["closeIcons"] = list()
        UIDict["closeIcons"].append(OrderedDict())
        UIDict["closeIcons"][0]["id"] = self.UICloseIconsIDIndex
        self.UICloseIconsIDIndex += 1
        UIDict["closeIcons"][0]["x"] = 0
        UIDict["closeIcons"][0]["y"] = 0
        UIDict["closeIcons"][0]["width"] = 0
        UIDict["closeIcons"][0]["height"] = 0
        UIDict["closeIcons"][0]["imgPath"] = ""
        UIDict["closeIcons"][0]["desc"] = ""

        UIDict["uiStates"] = list()
        UIDict["uiStates"].append(OrderedDict())
        UIDict["uiStates"][0]["id"] = self.UIStatesIDIndex

        self.UIScriptIDIndex[self.UIStatesIDIndex] = 1
        self.logger.debug("ui script id index {}".format(self.UIScriptIDIndex))

        self.UIStatesIDIndex += 1

        UIDict["uiStates"][0]["desc"] = ""
        UIDict["uiStates"][0]["actionType"] = TYPE_UIACTION_CLICK
        UIDict["uiStates"][0]["template"] = 0
        UIDict["uiStates"][0]["keyPoints"] = DEFAULT_UI_KEYPOINT
        UIDict["uiStates"][0]["shift"] = DEFAULT_UI_SHIFT
        UIDict["uiStates"][0]["imgPath"] = ""
        UIDict["uiStates"][0]["x"] = 0
        UIDict["uiStates"][0]["y"] = 0
        UIDict["uiStates"][0]["w"] = 0
        UIDict["uiStates"][0]["h"] = 0
        UIDict["uiStates"][0]["actionX"] = 0
        UIDict["uiStates"][0]["actionY"] = 0
        UIDict["uiStates"][0]["actionThreshold"] = DEFAULT_TEMPLATE_THRESHOLD
        UIDict["uiStates"][0]["actionTmplExpdWPixel"] = DEFAULT_TMPL_EXPD_W_PIXEL
        UIDict["uiStates"][0]["actionTmplExpdHPixel"] = DEFAULT_TMPL_EXPD_H_PIXEL
        UIDict["uiStates"][0]["actionROIExpdWRatio"] = DEFAULT_EXPD_W_RATIO
        UIDict["uiStates"][0]["actionROIExpdHRatio"] = DEFAULT_EXPD_H_RATIO


        UIDict["uiStates"][0]["checkSameFrameCnt"] = 5
        UIDict["uiStates"][0]["delete"] = 0

        # 创建一系列子节点
        self.CreateDebugWithSDKTool(child, UIDict["debugWithSDKTools"])
        self.CreateShowImageItem(child, UIDict["showImage"])
        self.CreateSaveResultItem(child, UIDict["saveResult"])
        self.CreateShowSaveResultItem(child, UIDict["showSaveResult"])
        self.CreateMatchStartStateItem(child, UIDict["matchStartState"])
        self.CreateMatchEndStateFromUIStatesItem(child, UIDict["matchEndStateFromUIStates"])
        self.CreateCheckCloseIconsWhenPlayingItem(child, UIDict["checkCloseIconsWhenPlaying"])

        # 创建GameOver节点
        childGameOver = self.CreateTreeItem(key='gameOver', type=ITEM_TYPE_GAMEOVER)
        for value in UIDict["gameOver"]:
            childGameOver.addChild(self.CreateGameOverItem(value))
        child.addChild(childGameOver)

        # 创建closeIcon节点
        childCloseIcon = self.CreateTreeItem(key='closeIcons', type=ITEM_TYPE_CLOSEICONS)
        for value in UIDict["closeIcons"]:
            childCloseIcon.addChild(self.CreateCloseIconsItem(value))
        child.addChild(childCloseIcon)

        # 创建devicesCloseIcons节点
        deviceCloseIcons = self.CreateTreeItem(key=DEVICE_CLOSE_ICON_NAME, type=ITEM_TYPE_CLOSEICONS)
        for value in UIDict.get(DEVICE_CLOSE_ICON_NAME) or []:
            deviceCloseIcons.addChild(self.CreateDeviceCloseIconsItem(value))
        child.addChild(deviceCloseIcons)

        # 创建uiStates节点
        childUIStates = self.CreateTreeItem(key='uiStates', type=ITEM_TYPE_UISTATES)
        for value in UIDict.get("uiStates"):
            childUIStates.addChild(self.CreateUIStatesItem(value))
        child.addChild(childUIStates)

    '''
        添加GameOver的element
    '''
    def AddGameOverElement(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddGameOverElement failed, treeItem is None")
            return

        GameOverList = list()
        GameOverList.append(OrderedDict())
        GameOverList[0]["id"] = self.UIGameOverIDIndex
        self.UIGameOverIDIndex += 1
        GameOverList[0]["actionType"] = TYPE_UIACTION_CLICK
        GameOverList[0]["x"] = 0
        GameOverList[0]["y"] = 0
        GameOverList[0]["w"] = 0
        GameOverList[0]["h"] = 0
        GameOverList[0]["imgPath"] = ""
        GameOverList[0]["desc"] = ""
        GameOverList[0]["shift"] = DEFAULT_UI_SHIFT
        GameOverList[0]["actionX"] = 0
        GameOverList[0]["actionY"] = 0
        GameOverList[0]["actionThreshold"] = DEFAULT_TEMPLATE_THRESHOLD
        GameOverList[0]["actionTmplExpdWPixel"] = DEFAULT_TMPL_EXPD_W_PIXEL
        GameOverList[0]["actionTmplExpdHPixel"] = DEFAULT_TMPL_EXPD_H_PIXEL
        GameOverList[0]["actionROIExpdWRatio"] = DEFAULT_EXPD_W_RATIO
        GameOverList[0]["actionROIExpdHRatio"] = DEFAULT_EXPD_H_RATIO

        for value in GameOverList:
            treeItem.addChild(self.CreateGameOverItem(value))

    '''
        添加closeIcon的element
    '''
    def AddCloseIconsElement(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddCloseIconsElement failed, treeItem is None")
            return

        CloseIconList = list()
        CloseIconList.append(OrderedDict())
        CloseIconList[0]["id"] = self.UICloseIconsIDIndex
        self.UICloseIconsIDIndex += 1
        CloseIconList[0]["x"] = 0
        CloseIconList[0]["y"] = 0
        CloseIconList[0]["width"] = 0
        CloseIconList[0]["height"] = 0
        CloseIconList[0]["imgPath"] = ""
        CloseIconList[0]["desc"] = ""

        for value in CloseIconList:
            treeItem.addChild(self.CreateCloseIconsItem(value))

    def AddDevicesCloseIcon(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddCloseIconsElement failed, treeItem is None")
            return

        DCloseIconList = list()
        DCloseIconList.append(OrderedDict())
        DCloseIconList[0]["id"] = self.UIDevicesCloseIconsIDIndex
        self.UIDevicesCloseIconsIDIndex += 1
        DCloseIconList[0]["x"] = 0
        DCloseIconList[0]["y"] = 0
        DCloseIconList[0]["width"] = 0
        DCloseIconList[0]["height"] = 0
        DCloseIconList[0]["imgPath"] = ""
        DCloseIconList[0]["desc"] = ""

        for value in DCloseIconList:
            treeItem.addChild(self.CreateDeviceCloseIconsItem(value))

    '''
        添加UIStates的element
    '''
    def AddUIStatesElement(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddUIStatesElement failed, treeItem is None")
            return

        UIStatesList = list()
        UIStatesList.append(OrderedDict())
        UIStatesList[0]["id"] = self.UIStatesIDIndex

        self.UIScriptIDIndex[self.UIStatesIDIndex] = 1
        self.logger.debug("ui script id index {}".format(self.UIScriptIDIndex))

        self.UIStatesIDIndex += 1
        UIStatesList[0]["desc"] = ""
        UIStatesList[0]["actionType"] = TYPE_UIACTION_CLICK
        UIStatesList[0]["template"] = 0
        UIStatesList[0]["keyPoints"] = DEFAULT_UI_KEYPOINT
        UIStatesList[0]["shift"] = DEFAULT_UI_SHIFT
        UIStatesList[0]["imgPath"] = ""
        UIStatesList[0]["x"] = 0
        UIStatesList[0]["y"] = 0
        UIStatesList[0]["w"] = 0
        UIStatesList[0]["h"] = 0
        UIStatesList[0]["actionX"] = 0
        UIStatesList[0]["actionY"] = 0
        UIStatesList[0]["actionThreshold"] = DEFAULT_TEMPLATE_THRESHOLD
        UIStatesList[0]["actionTmplExpdWPixel"] = DEFAULT_TMPL_EXPD_W_PIXEL
        UIStatesList[0]["actionTmplExpdHPixel"] = DEFAULT_TMPL_EXPD_H_PIXEL
        UIStatesList[0]["actionROIExpdWRatio"] = DEFAULT_EXPD_W_RATIO
        UIStatesList[0]["actionROIExpdHRatio"] = DEFAULT_EXPD_H_RATIO

        UIStatesList[0]["checkSameFrameCnt"] = 5
        UIStatesList[0]["delete"] = 0

        for value in UIStatesList:
            treeItem.addChild(self.CreateUIStatesItem(value))

    def ADDUIScriptTaskElement(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("ADDUIScriptTaskElement failed, treeItem is None")
            return
        UIStateItem = treeItem.parent()
        UIID = self.GetChildItemValue(UIStateItem, 0, "id", 1)
        self.logger.debug("id is {} UI Script ID Index {}".format(UIID, self.UIScriptIDIndex))
        taskIDIndex = self.UIScriptIDIndex.get(int(UIID))
        if taskIDIndex is not None:
            taskElement = self.CreateScriptTaskItem(text=TYPE_UIACTION_CLICK, taskIDIndex=taskIDIndex + 1)
            self.UIScriptIDIndex[int(UIID)] = taskIDIndex + 1

        else:
            taskElement = self.CreateScriptTaskItem(text=TYPE_UIACTION_CLICK)
        treeItem.addChild(taskElement)
        treeItem.setExpanded(True)

    '''
        添加ID，应该是添加matchstartstate那一项
    '''
    def AddUIStateID(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddUIStateID failed, treeItem is None")
            return

        treeItem.addChild(self.CreateTreeItem(key='id', type=ITEM_TYPE_UISTATE_ID, edit=True))

        treeItem.setExpanded(True)

    '''
        创建debugwithsdktool节点
    '''
    def CreateDebugWithSDKTool(self, treeItem, valueBool):
        if treeItem is None:
            self.logger.error('CreateDebugWithSDKTool failed, treeItem is None')
            return

        child = self.CreateTreeItem(key='DebugWithSDKTools')
        treeItem.addChild(child)

        qCombox = QComboBox()
        qCombox.addItems([
            str(True),
            str(False)
        ])
        qCombox.setCurrentText(str(valueBool))
        self.ui.treeWidget.setItemWidget(child, 1, qCombox)

    '''
        创建ShowImage节点
    '''
    def CreateShowImageItem(self, treeItem, valueBool):
        if treeItem is None:
            self.logger.error('CreateShowImageItem failed, treeItem is None')
            return

        child = self.CreateTreeItem(key='ShowImage')
        treeItem.addChild(child)

        qCombox = QComboBox()
        qCombox.addItems([
            str(True),
            str(False)
        ])
        qCombox.setCurrentText(str(valueBool))
        self.ui.treeWidget.setItemWidget(child, 1, qCombox)

    '''
        创建SaveResult节点
    '''
    def CreateSaveResultItem(self, treeItem, valueBool):
        if treeItem is None:
            self.logger.error('CreateSaveResultItem failed, treeItem is None')
            return

        child = self.CreateTreeItem(key='SaveResult')
        treeItem.addChild(child)

        qCombox = QComboBox()
        qCombox.addItems([
            str(True),
            str(False)
        ])
        qCombox.setCurrentText(str(valueBool))
        self.ui.treeWidget.setItemWidget(child, 1, qCombox)

    '''
        创建ShowSaveResult节点
    '''
    def CreateShowSaveResultItem(self, treeItem, valueBool):
        if treeItem is None:
            self.logger.error('CreateShowSaveResultItem failed, treeItem is None')
            return

        child = self.CreateTreeItem(key='ShowSaveResult')
        treeItem.addChild(child)

        qCombox = QComboBox()
        qCombox.addItems([
            str(True),
            str(False)
        ])
        qCombox.setCurrentText(str(valueBool))
        self.ui.treeWidget.setItemWidget(child, 1, qCombox)

    '''
        创建CheckCloseIconsWhenPlaying节点
    '''
    def CreateCheckCloseIconsWhenPlayingItem(self, treeItem, valueBool):
        if treeItem is None:
            self.logger.error('CreateCheckCloseIconsWhenPlayingItem failed, treeItem is None')
            return

        child = self.CreateTreeItem(key='CheckCloseIconsWhenPlaying')
        treeItem.addChild(child)

        qCombox = QComboBox()
        qCombox.addItems([
            str(True),
            str(False)
        ])
        qCombox.setCurrentText(str(valueBool))
        self.ui.treeWidget.setItemWidget(child, 1, qCombox)

    '''
        创建MatchStartState节点
    '''
    def CreateMatchStartStateItem(self, treeItem, valueList):
        if treeItem is None:
            self.logger.error('CreateMatchStartStateItem failed, treeItem is None')
            return

        if valueList is None:
            self.logger.error('CreateMatchStartStateItem failed, valueList is None')
            return

        child = self.CreateTreeItem(key='MatchStartState')
        treeItem.addChild(child)

        for value in valueList:
            child.addChild(self.CreateTreeItem(key='id', value=value["id"], edit=True))

    '''
        创建MatchEndStateFromUIStates节点
    '''
    def CreateMatchEndStateFromUIStatesItem(self, treeItem, valueList):
        if treeItem is None:
            self.logger.error('CreateMatchEndStateFromUIStatesItem failed, treeItem is None')
            return

        if valueList is None:
            self.logger.error('CreateMatchEndStateFromUIStatesItem failed, valueList is None')

            return

        child = self.CreateTreeItem(key='MatchEndStateFromUIStates')
        treeItem.addChild(child)

        for value in valueList:
            child.addChild(self.CreateTreeItem(key='id', value=value["id"], edit=True))

    def CreateScriptTaskItem(self, text, taskIDIndex=1, valueDict=dict()):
        if text is None:
            self.logger.error('CreateScriptTaskItem failed, input text is None')
            return

        taskElement = self.CreateTreeItem(key='task')
        # "taskid"
        taskElement.addChild(self.CreateTreeItem(key="taskid", value=taskIDIndex, edit=True))

        # "duringTimeMs"
        taskElement.addChild(self.CreateTreeItem(key="duringTimeMs", value=valueDict.get("duringTimeMs") or 100, edit=True))

        # "sleepTimeMs"
        taskElement.addChild(self.CreateTreeItem(key="sleepTimeMs", value=valueDict.get("sleepTimeMs") or 100, edit=True))

        # "type"
        childActionType = self.CreateTreeItem(key='type')
        taskElement.addChild(childActionType)
        qCombox2 = QComboBox()
        qCombox2.addItems([
            TYPE_UIACTION_CLICK,
            TYPE_UIACTION_DRAG
        ])
        qCombox2.setCurrentText(text)
        qCombox2.currentTextChanged.connect(self.UIScriptActionComboxTextChange)

        self.ui.treeWidget.setItemWidget(childActionType, 1, qCombox2)

        childAction = self.CreateTreeItem(key='action', type=ITEM_TYPE_UI_SCRIPT_TASK_ACTION)
        # if "type" is click, add "actionX", "actionY"
        if text == TYPE_UIACTION_CLICK:
            self._LoadClickAction(valueDict, childAction)
        if text == TYPE_UIACTION_DRAG:
            self._LoadDragAction(valueDict, childAction)

        taskElement.addChild(childAction)

        return taskElement
        
    '''
        创建GameOver节点
    '''
    def CreateGameOverItem(self, valueDict):
        if valueDict is None:
            self.logger.error('CreateGameOverItem failed, valueDict is None')
            return

        if int(valueDict["id"]) >= self.UIGameOverIDIndex:
            self.UIGameOverIDIndex = int(valueDict["id"]) + 1

        UIType = self._GetDictValue(valueDict, ["action_type", "actionType"])

        # 兼容GameOver和gameOver
        if "GameOver" in self.projectDict["UIImagePath"].keys():
            return self.LoadGameOverFunc[UIType](valueDict, "GameOver")
        else:
            return self.LoadGameOverFunc[UIType](valueDict, "gameOver")

    def CreateDeviceCloseIconsItem(self, valueDict):
        if valueDict is None:
            self.logger.error('CreateCloseIconsItem failed, valueDict is None')
            return

        childCloseIcon = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)

        # 兼容closeIcons和CloseIcons
        if DEVICE_CLOSE_ICON_NAME in self.projectDict["UIImagePath"].keys():
            # 从project.json中获取配置的图像路径，填入根节点第四列（第四列隐藏）
            if str(valueDict["id"]) in self.projectDict["UIImagePath"][DEVICE_CLOSE_ICON_NAME].keys():
                childCloseIcon.setText(3, self.projectDict["UIImagePath"][DEVICE_CLOSE_ICON_NAME][str(valueDict["id"])])
            else:
                # 如果project.json没有路径，那可能是导入的之前手动配置的配置文件，需要找到imgpath字段，将路径填到根节点第四列
                imgPath = self._GetDictValue(valueDict, ["imgpath", "imgPath"])
                if imgPath is not None and imgPath != "":
                    childCloseIcon.setText(3, self.projectDict["projectPath"] + "/v1.0/" + imgPath)

        # 创建一系列字段，如id，imgPath，ROI等
        if int(valueDict["id"]) >= self.UIDevicesCloseIconsIDIndex:
            self.UIDevicesCloseIconsIDIndex = int(valueDict["id"]) + 1

        childCloseIcon.addChild(self.CreateTreeItem(key='id', value=valueDict["id"]))
        childCloseIcon.addChild(self.CreateTreeItem(key='desc', value=valueDict["desc"], edit=True))
        childCloseIcon.addChild(
            self.CreateTreeItem(key='imgPath', value=self._GetDictValue(valueDict, ["imgpath", "imgPath"]), edit=True))

        childROI = self.CreateTreeItem(key='ROI')
        childCloseIcon.addChild(childROI)

        self.LoadPoPUITempRect(valueDict, childROI)

        return childCloseIcon

    '''
        创建CloseIcons节点
    '''
    def CreateCloseIconsItem(self, valueDict):
        if valueDict is None:
            self.logger.error('CreateCloseIconsItem failed, valueDict is None')
            return

        childCloseIcon = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)

        # 兼容closeIcons和CloseIcons
        if "closeIcons" in self.projectDict["UIImagePath"].keys():
            # 从project.json中获取配置的图像路径，填入根节点第四列（第四列隐藏）
            if str(valueDict["id"]) in self.projectDict["UIImagePath"]["closeIcons"].keys():
                childCloseIcon.setText(3, self.projectDict["UIImagePath"]["closeIcons"][str(valueDict["id"])])
            else:
                # 如果project.json没有路径，那可能是导入的之前手动配置的配置文件，需要找到imgpath字段，将路径填到根节点第四列
                imgPath = self._GetDictValue(valueDict, ["imgpath", "imgPath"])
                if imgPath is not None and imgPath != "":
                    childCloseIcon.setText(3, self.projectDict["projectPath"] + "/v1.0/" + imgPath)
        elif "CloseIcons" in self.projectDict["UIImagePath"].keys():
            if str(valueDict["id"]) in self.projectDict["UIImagePath"]["CloseIcons"].keys():
                childCloseIcon.setText(3, self.projectDict["UIImagePath"]["CloseIcons"][str(valueDict["id"])])
            else:
                imgPath = self._GetDictValue(valueDict, ["imgpath", "imgPath"])
                if imgPath is not None and imgPath != "":
                    childCloseIcon.setText(3, self.projectDict["projectPath"] + "/v1.0/" + imgPath)

        # 创建一系列字段，如id，imgPath，ROI等
        if int(valueDict["id"]) >= self.UICloseIconsIDIndex:
            self.UICloseIconsIDIndex = int(valueDict["id"]) + 1

        childCloseIcon.addChild(self.CreateTreeItem(key='id', value=valueDict["id"], edit=True))
        childCloseIcon.addChild(self.CreateTreeItem(key='desc', value=valueDict["desc"], edit=True))
        childCloseIcon.addChild(
            self.CreateTreeItem(key='imgPath', value=self._GetDictValue(valueDict, ["imgpath", "imgPath"]), edit=True))

        childROI = self.CreateTreeItem(key='ROI')
        childCloseIcon.addChild(childROI)

        self.LoadPoPUITempRect(valueDict, childROI)

        return childCloseIcon

    '''
        创建UIState节点
    '''
    def CreateUIStatesItem(self, valueDict):
        if valueDict is None:
            self.logger.error('CreateUIStatesItem failed, valueDict is None')
            return

        UIType = self._GetDictValue(valueDict, ["action_type", "actionType"])

        if int(valueDict["id"]) >= self.UIStatesIDIndex:
            self.UIStatesIDIndex = int(valueDict["id"]) + 1           # id+1是为了避免导入之前手动配置的文件时，id出现错误的情况

            self.UIScriptIDIndex[self.UIStatesIDIndex] = 1
        if "uiStates" in self.projectDict["UIImagePath"].keys():
            return self.LoadUIFunc[UIType](valueDict, "uiStates")
        else:
            return self.LoadUIFunc[UIType](valueDict, "UIStates")

    def CreateUIScriptItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIClickItem failed, valueDict is None')
            return

        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)

        self._CreateUICommItem(elementItem, elementType, valueDict)
        elementItem.addChild(self.CreateTreeItem(key="scriptPath", value=valueDict.get("scriptPath") or "", edit=True))
        childTasks = self.CreateTreeItem(key='tasks', type=ITEM_TYPE_UI_SCRIPT_TASK)

        taskList = valueDict.get("tasks") or []
        elementID = int(valueDict["id"])
        if len(taskList) > 0:
            # get "task" dict in "tasks" and fill item
            for taskDcit in taskList:
                taskID = int(taskDcit.get("taskid"))

                childTasks.addChild(self.CreateScriptTaskItem(text=taskDcit.get("type") or TYPE_UIACTION_CLICK,
                                                              taskIDIndex=taskID,
                                                              valueDict=taskDcit))
                elementItem.addChild(childTasks)

                if self.UIScriptIDIndex.get(elementID) is None:
                    self.UIScriptIDIndex[elementID] = taskID
                else:
                    # set UIScript2Dict[elementID]  as the max num
                    self.UIScriptIDIndex[elementID] = max(self.UIScriptIDIndex[elementID], taskID)

        else:
            childTasks.addChild(self.CreateScriptTaskItem(text=TYPE_UIACTION_CLICK))
            elementItem.addChild(childTasks)

        elementItem.addChild(self.CreateTreeItem(key="checkSameFrameCnt",
                                                 value=valueDict.get("checkSameFrameCnt") or 5, edit=True))
        elementItem.addChild(self.CreateTreeItem(key="delete", value=valueDict.get("delete") or 0, edit=True))
        return elementItem

    def _CreateGameOverCommonItem(self, elementItem, elementType, valueDict):
        # 读取project.json中的路径，填入根节点第四列（第四列隐藏）
        if str(valueDict["id"]) in self.projectDict["UIImagePath"][elementType].keys():
            elementItem.setText(3, self.projectDict["UIImagePath"][elementType][str(valueDict["id"])])
        else:
            # 如果project.json中读取不到路径，则可能是导入之前手动配置的配置文件，需要查找imgpath字段来获取路径，填入根节点第四列
            imgPath = self._GetDictValue(valueDict, ["imgpath", "imgPath"])
            if imgPath is not None and imgPath != "":
                elementItem.setText(3, self.projectDict["projectPath"] + "/v1.0/" + imgPath)

        # 添加click类型的子节点
        # "id"
        elementItem.addChild(self.CreateTreeItem(key='id', value=valueDict["id"], edit=True))

        # "actionType"
        childActionType = self.CreateTreeItem(key='actionType')
        elementItem.addChild(childActionType)
        qCombox = QComboBox()
        qCombox.addItems([
            TYPE_UIACTION_CLICK,
            TYPE_UIACTION_DRAG
        ])

        qCombox.setCurrentText(str(self._GetDictValue(valueDict, ["action_type", "actionType"])))
        qCombox.currentTextChanged.connect(self.UIComboxTextChange)
        self.ui.treeWidget.setItemWidget(childActionType, 1, qCombox)

        # "desc"
        elementItem.addChild(self.CreateTreeItem(key='desc', value=valueDict["desc"], edit=True))

        # "imgPath"
        elementItem.addChild(
            self.CreateTreeItem(key='imgPath', value=self._GetDictValue(valueDict, ["imgpath", "imgPath"]), edit=True))

        # "ROI": "x", "y", "w","h"
        childROI = self.CreateTreeItem(key='ROI')
        elementItem.addChild(childROI)

        self.LoadTempRect(valueDict, childROI)
        #  "shift"
        # shift可有可无，当shift没有时，默认其为20
        if "shift" in valueDict.keys():
            shiftNum = valueDict["shift"]
        else:
            shiftNum = DEFAULT_UI_SHIFT

        elementItem.addChild(self.CreateTreeItem(key='shift', value=shiftNum, edit=True))

    def CreateGameOverClickItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIClickItem failed, valueDict is None')
            return

        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)
        self._CreateGameOverCommonItem(elementItem, elementType, valueDict)
        #  添加click动作节点:"actionX","actionY"
        childAction = self.CreateTreeItem(key='action')
        elementItem.addChild(childAction)

        self._LoadClickAction(valueDict, childAction)
        return elementItem

    def _CreateTmplItems(self, elementItem, valueDict):
        childTemplate = self.CreateTreeItem(key='template')
        elementItem.addChild(childTemplate)

        LineText = QLineEdit()
        pIntValidator = QIntValidator()
        pIntValidator.setRange(0, 20)
        LineText.setValidator(pIntValidator)

        tmplNum = valueDict.get("template")
        if tmplNum is not None:
            LineText.setText(str(tmplNum))
        else:
            LineText.setPlaceholderText("-1")

        self.ui.treeWidget.setItemWidget(childTemplate, 1, LineText)
        LineText.textChanged.connect(self.UITemplTextChange)
        LineText.editingFinished.connect(self.UITemplComboxChange)

        elementItem.addChild(self.CreateTreeItem(key='desc', value=valueDict["desc"], edit=True))
        elementItem.addChild(
            self.CreateTreeItem(key='imgPath', value=self._GetDictValue(valueDict, ["imgpath", "imgPath"]), edit=True))

        # 配置文件中，可能有template字段，也可能没有template字段，如果没有template字段，默认其为0
        if "template" in valueDict.keys():
            templateFlag = valueDict["template"]
        else:
            templateFlag = 0

        # 当添加的item是uistates且template字段为1，或者添加的item是gameOver时，需要添加ROI节点
        # if elementType in ["uiStates", "UIStates"] and templateFlag == 1 or elementType in ["gameOver", "GameOver"]:
        if templateFlag == 1:
            childROI = self.CreateTreeItem(key='ROI')
            elementItem.addChild(childROI)

            self.LoadTempRect(valueDict, childROI)

        elif templateFlag > 1:
            childROI = self.CreateTreeItem(key='templateOp', value=valueDict.get("templateOp"))
            elementItem.addChild(childROI)
            for roiID in range(templateFlag):
                childROI = self.CreateTreeItem(key='ROI')
                elementItem.addChild(childROI)
                templateDict = OrderedDict()
                templateDict['x'] = valueDict.get("x{}".format(roiID + 1)) or 0
                templateDict['y'] = valueDict.get("y{}".format(roiID + 1)) or 0
                templateDict['w'] = valueDict.get("w{}".format(roiID + 1)) or 0
                templateDict['h'] = valueDict.get("h{}".format(roiID + 1)) or 0
                templateDict['shift'] = valueDict.get("shift{}".format(roiID + 1)) or DEFAULT_UI_SHIFT
                templateDict['templateThreshold'] = valueDict.get("templateThreshold{}".format(roiID + 1)) or DEFAULT_TEMPLATE_THRESHOLD
                self.LoadTempRect(templateDict, childROI)
    '''
        创建UI中click动作的item（有可能时gameover或UIstate的item）
    '''
    def CreateUIClickItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIClickItem failed, valueDict is None')
            return

        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)
        self._CreateUICommItem(elementItem, elementType, valueDict)
        # 添加click动作节点
        childAction = self.CreateTreeItem(key='action')
        elementItem.addChild(childAction)
        # self.LoadUIAction({"actionX": self._GetDictValue(valueDict, ["action_x", "actionX"]),
        #                    "actionY": self._GetDictValue(valueDict, ["action_y", "actionY"])}, childAction)

        self._LoadClickAction(valueDict, childAction)
        elementItem.addChild(
            self.CreateTreeItem(key="checkSameFrameCnt", value=valueDict.get("checkSameFrameCnt") or 5, edit=True))
        elementItem.addChild(self.CreateTreeItem(key="delete", value=valueDict.get("delete") or 0, edit=True))

        return elementItem

    def CreateGameOverDragItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIDragItem failed, valueDict is None')
            return

            # 读取project.json中的路径，填入根节点第四列（第四列隐藏）
        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)
        self._CreateGameOverCommonItem(elementItem, elementType, valueDict)
        # 添加drag动作节点
        childAction = self.CreateTreeItem(key='action')
        elementItem.addChild(childAction)

        self._LoadDragAction(valueDict, childAction)
        return elementItem

    def _CreateUICommItem(self, elementItem, elementType, valueDict):
        # 读取project.json中的路径，填入根节点第四列（第四列隐藏）
        if str(valueDict["id"]) in self.projectDict["UIImagePath"][elementType].keys():
            elementItem.setText(3, self.projectDict["UIImagePath"][elementType][str(valueDict["id"])])
        else:
            # 如果project.json中读取不到路径，则可能是导入之前手动配置的配置文件，需要查找imgpath字段来获取路径，填入根节点第四列
            imgPath = self._GetDictValue(valueDict, ["imgpath", "imgPath"])
            if imgPath is not None and imgPath != "":
                elementItem.setText(3, self.projectDict["projectPath"] + "/v1.0/" + imgPath)

        # 创建各个子节点，包括id，actiontype等，会根据是gameover的item还是UIstates的item而创建不同的子节点
        elementItem.addChild(self.CreateTreeItem(key='id', value=valueDict["id"], edit=True))

        childActionType = self.CreateTreeItem(key='actionType')
        elementItem.addChild(childActionType)
        qCombox = QComboBox()
        qCombox.addItems([
            TYPE_UIACTION_CLICK,
            TYPE_UIACTION_DRAG,
            TYPE_UIACTION_DRAGCHECK,
            TYPE_UIACTION_SCRIPT
        ])

        # 如果要创建的item是gameOver的话，type选项框中还需要多加一个dragcheck
        qCombox.setCurrentText(str(valueDict.get("actionType") or ''))
        qCombox.currentTextChanged.connect(self.UIComboxTextChange)
        self.ui.treeWidget.setItemWidget(childActionType, 1, qCombox)

        self._CreateTmplItems(elementItem, valueDict)
        if "keyPoints" in valueDict.keys():
            elementItem.addChild(self.CreateTreeItem(key='keyPoints', value=valueDict["keyPoints"], edit=True))
        elif "keypoints" in valueDict.keys():
            elementItem.addChild(self.CreateTreeItem(key='keyPoints', value=valueDict["keypoints"], edit=True))

        elementItem.addChild(self.CreateTreeItem(key='shift', value=valueDict.get("shift") or DEFAULT_UI_SHIFT, edit=True))

    '''
        创建UI的drag动作类型的item（有可能时gameOver或UIstates）
    '''
    def CreateUIDragItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIDragItem failed, valueDict is None')
            return
        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)
        self._CreateUICommItem(elementItem, elementType, valueDict)

        # 添加drag动作节点
        childAction = self.CreateTreeItem(key='action')
        elementItem.addChild(childAction)

        self._LoadDragAction(valueDict, childAction)
        elementItem.addChild(
            self.CreateTreeItem(key="checkSameFrameCnt", value=valueDict.get("checkSameFrameCnt") or 5, edit=True))
        elementItem.addChild(self.CreateTreeItem(key="delete", value=valueDict.get("delete") or 1, edit=True))

        return elementItem

    def LoadPoPUITempRect(self, ROIJsonDict, treeItemROI):
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
        if "width" not in ROIJsonDict.keys():
            ROIJsonDict["width"] = 0
        if "height" not in ROIJsonDict.keys():
            ROIJsonDict["height"] = 0
        if "shift" not in ROIJsonDict.keys():
            ROIJsonDict["shift"] = DEFAULT_UI_SHIFT

        if "templateThreshold" not in ROIJsonDict.keys():
            ROIJsonDict["templateThreshold"] = DEFAULT_TEMPLATE_THRESHOLD

        treeItemROI.addChild(self.CreateTreeItem(key='x', value=ROIJsonDict["x"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='y', value=ROIJsonDict["y"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='w', value=ROIJsonDict["width"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='h', value=ROIJsonDict["height"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='shift', value=ROIJsonDict["shift"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='templateThreshold', value=ROIJsonDict["templateThreshold"],
                                                 edit=True))

    def LoadTempRect(self, ROIJsonDict, treeItemROI):
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
        if "shift" not in ROIJsonDict.keys():
            ROIJsonDict["shift"] = DEFAULT_UI_SHIFT

        if "templateThreshold" not in ROIJsonDict.keys():
            ROIJsonDict["templateThreshold"] = DEFAULT_TEMPLATE_THRESHOLD

        treeItemROI.addChild(self.CreateTreeItem(key='x', value=ROIJsonDict["x"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='y', value=ROIJsonDict["y"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='w', value=ROIJsonDict["w"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='h', value=ROIJsonDict["h"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='shift', value=ROIJsonDict["shift"], edit=True))
        treeItemROI.addChild(self.CreateTreeItem(key='templateThreshold', value=ROIJsonDict["templateThreshold"],
                                                 edit=True))

    def LoadDragCheckRect(self, ROIJsonDict, treeItemROI):
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
        创建UIDragCheck类型的item
    '''
    def CreateUIDragCheckItem(self, valueDict, elementType):
        if valueDict is None:
            self.logger.error('CreateUIDragCheckItem failed, valueDict is None')
            return

        # 读取project.json中的路径，填入根节点第四列（第四列隐藏）
        elementItem = self.CreateTreeItem(key='element', type=ITEM_TYPE_UI_ELEMENT)
        self._CreateUICommItem(elementItem, elementType, valueDict)
        childActionDir = self.CreateTreeItem(key='actionDir')
        elementItem.addChild(childActionDir)
        qCombox = QComboBox()
        qCombox.addItems([
            "up",
            "down",
            "left",
            "right"
        ])
        qCombox.setCurrentText(str(valueDict["actionDir"]))
        self.ui.treeWidget.setItemWidget(childActionDir, 1, qCombox)

        childPoint = self.CreateTreeItem(key='dragPoint')
        elementItem.addChild(childPoint)
        # self.LoadPoint({"x": valueDict["x"], "y": valueDict["y"]}, childPoint)
        childPoint.addChild(self.CreateTreeItem(key="actionX", value=valueDict["dragX"], edit=True))
        childPoint.addChild(self.CreateTreeItem(key="actionY", value=valueDict["dragY"], edit=True))

        elementItem.addChild(self.CreateTreeItem(key="dragLen", value=valueDict["dragLen"], edit=True))
        childTargetItem = self.CreateTreeItem(key="target", type=ITEM_TYPE_ELEMENT)
        elementItem.addChild(childTargetItem)
        childTargetItem.addChild(self.CreateTreeItem(key="targetImg", value=valueDict["targetImg"], edit=True))

        childTargetROI = self.CreateTreeItem(key='ROI')
        childTargetItem.addChild(childTargetROI)
        self.LoadDragCheckRect({"x": valueDict["targetX"], "y": valueDict["targetY"], "w": valueDict["targetW"], "h": valueDict["targetH"]}, childTargetROI)

        elementItem.addChild(
            self.CreateTreeItem(key="checkSameFrameCnt", value=valueDict.get("checkSameFrameCnt") or 5, edit=True))
        elementItem.addChild(
            self.CreateTreeItem(key="delete", value=valueDict.get("delete") or 0, edit=True))
        return elementItem

    def UIScriptActionComboxTextChange(self, text):
        if text is None:
            self.logger.error("UIComboxTextChange failed, text is {}".format(text))
            return

        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("UIComboxTextChange failed, treeItem is None")
            return

        # item: "task"
        item = treeItem.parent()
        if item is None:
            self.logger.error("UIComboxTextChange failed, elementItem is None")
            return

        # item: "tasks"
        tasksItem = item.parent()

        curTaskID = self.GetChildItemValue(item, 0, "taskid", 1)
        for itemIndex in range(tasksItem.childCount()):

            # search "task"
            element = tasksItem.child(itemIndex)
            id = self.GetChildItemValue(element, 0, "taskid", 1)
            if id == curTaskID:
                # 删除原来的item
                tasksItem.takeChild(itemIndex)

                # create a new task element
                newElementItem = self.CreateScriptTaskItem(text=text)
                # 将新的item插入
                tasksItem.insertChild(itemIndex, newElementItem)
                newElementItem.setExpanded(True)
                tasksItem.setExpanded(True)
                self.mainWindow.canvas.resetState()
                break


    '''
        UI中type的下拉选项框修改时，执行的槽函数
        将原有的item（gameover，closicons，uistates）删除，创建新的树结构替换他
    '''
    def UIComboxTextChange(self, text):
        if text is None:
            self.logger.error("UIComboxTextChange failed, text is {}".format(text))
            return

        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("UIComboxTextChange failed, treeItem is None")
            return

        elementItem = treeItem.parent()
        if elementItem is None:
            self.logger.error("UIComboxTextChange failed, elementItem is None")
            return

        UIItem = elementItem.parent()
        if UIItem is None:
            self.logger.error("UIComboxTextChange failed, UIItem is None")
            return

        elementID = self.GetChildItemValue(elementItem, 0, "id", 1)
        elementType = UIItem.text(0)

        # 通过id找到修改了类型的UIitem（gameover，closicons，uistates），删除后，再创建一个新的item插入至原来的位置
        for itemIndex in range(UIItem.childCount()):
            element = UIItem.child(itemIndex)
            itemID = self.GetChildItemValue(element, 0, "id", 1)
            if itemID == elementID:
                # 删除原来的item
                UIItem.takeChild(itemIndex)
                # 创建新的item
                if elementType == "gameOver":
                    newElementItem = self.CreateGameOverItem(self.GenerateUIActionDict(text, elementType))
                elif elementType == "uiStates":
                    newElementItem = self.CreateUIStatesItem(self.GenerateUIActionDict(text, elementType))
                else:
                    self.logger.error("wrong type of element of UI: {}".format(elementType))
                    return

                # 将新的item插入
                UIItem.insertChild(itemIndex, newElementItem)
                newElementItem.setExpanded(True)
                UIItem.setExpanded(True)
                self.mainWindow.canvas.resetState()
                break

    def UITemplTextChange(self, text):
        treeItem = self.ui.treeWidget.currentItem()
        treeItem.setText(1, text)

    def _DelPreUITmplItem(self, tmplItem, elementItem):
        childCnt = elementItem.childCount()
        index = 0
        while index < childCnt:
            tempItem = elementItem.child(index)
            if tmplItem is None:
                index += 1
            # delete previous "ROI" Item
            elif tempItem.text(0) == "ROI":
                elementItem.takeChild(index)
                childCnt -= 1

                if len(self.mainWindow.canvas.shapes) > 0:
                    self.mainWindow.canvas.shapes.pop(0)
                    self.mainWindow.canvas.update()

            # delete previous "templateOp" Item
            elif tempItem.text(0) == "templateOp":
                elementItem.takeChild(index)
                childCnt -= 1

            else:
                index += 1

    def _AddNewTmplItem(self, tmplItem, elementItem):
        strTmplNum = tmplItem.text(1)
        childCnt = elementItem.childCount()
        index = 0
        while index < childCnt:
            tempItem = elementItem.child(index)
            if tempItem is None:
                index += 1
                continue

            elif tempItem.text(0) == "imgPath" and strTmplNum == '':
                return

            # 如果选择template为1，则插入ROI节点，并设置画布需要画一个框
            elif tempItem.text(0) == "imgPath" and strTmplNum == "1":
                # add item "ROI"
                childROI = self.CreateTreeItem(key='ROI')
                self.LoadTempRect(OrderedDict(), childROI)
                childCnt = childCnt + 1
                index += 1
                elementItem.insertChild(index, childROI)
                # 当elementItem的第四列不为空，说明之前已导入过图像
                if elementItem.text(3) != "":
                    self.mainWindow.canvas.currentModel.insert(0, Shape.RECT)  # 向画布中的队列插入rect，说明需要画一个框
                    self.mainWindow.canvas.setRectTreeItem(childROI)  # 绑定树中的ROI，使得画框坐标改变时，树中ROI的值也会发送变化
                    self.PaintImage(elementItem.text(3))
                    self.mainWindow.canvas.setEditing(False)
                index += 1

            elif tempItem.text(0) == "imgPath" and int(strTmplNum) > 1:
                # add item "templateOp"
                index += 1
                childROI = self.CreateTreeItem(key='templateOp', value='and', edit=True)
                elementItem.insertChild(index, childROI)
                childCnt += 1
                for roiID in range(int(strTmplNum)):
                    childROI = self.CreateTreeItem(key='ROI')
                    self.LoadTempRect(OrderedDict(), childROI)
                    childCnt += 1
                    index += 1
                    elementItem.insertChild(index, childROI)
                    # 当elementItem的第四列不为空，说明之前已导入过图像
                    if elementItem.text(3) != "":
                        self.mainWindow.canvas.currentModel.insert(0, Shape.RECT)  # 向画布中的队列插入rect，说明需要画一个框
                        self.mainWindow.canvas.setRectTreeItem(childROI)  # 绑定树中的ROI，使得画框坐标改变时，树中ROI的值也会发送变化
                        self.PaintImage(elementItem.text(3))
                        self.mainWindow.canvas.setEditing(False)
                index += 1
            else:
                index += 1
    '''
        UIStates中template下拉选项框改变时触发的槽函数
        template取值为0或1，选0表示不用模板，选1表示用模板
    '''
    def UITemplComboxChange(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            return

        # text = treeItem.text(1)
        treeItem = self.ui.treeWidget.currentItem()
        elementItem = treeItem.parent()

        # clear previous models
        self.mainWindow.canvas.ClearCurrModel()
        self.mainWindow.canvas.ClearRectTree()

        # action type
        actionItem = None
        for itIndex in range(elementItem.childCount()):
            item = elementItem.child(itIndex)
            if item.text(0) in ["action", "dragPoint"]:
                actionItem = item
                break

        # 如果找到，则判断其坐标值是否大于0，如果大于0就画到画布上
        if actionItem is not None:
            # 如果是四个节点，说明是滑动动作
            if actionItem.childCount() == len(Drag_Key):

                x1 = int(actionItem.child(0).text(1))
                y1 = int(actionItem.child(1).text(1))
                x2 = int(actionItem.child(7).text(1))
                y2 = int(actionItem.child(8).text(1))

                self.mainWindow.canvas.setLineTreeItem(actionItem)
                if x1 > 0 or y1 > 0 or x2 > 0 or y2 > 0:
                    shape = self.CreateShape([(x1, y1), (x2, y2)])
                    self.mainWindow.canvas.loadShapes([shape])
            # 如果是两个节点，说明是点击动作
            elif actionItem.childCount() in[len(Click_Key), len(Drag_Check_Key)]:
                x = int(actionItem.child(0).text(1))
                y = int(actionItem.child(1).text(1))
                self.mainWindow.canvas.setPointTreeItem(actionItem)
                self.mainWindow.canvas.currentModel.insert(0, Shape.POINT)  # 向画布中的队列插入rect，说明需要画一个框
                self.PaintImage(elementItem.text(3))
                self.mainWindow.canvas.setEditing(False)

                if x > 0 or y > 0:
                    shape = self.CreateShape([(x, y)])
                    self.mainWindow.canvas.loadShapes([shape])

        # 遍历element的item（uistates），找到ROI节点，根据template的数值来进行修改
        self._DelPreUITmplItem(treeItem, elementItem)
        self._AddNewTmplItem(treeItem, elementItem)

    def _LoadClickAction(self, actionDict, treeItem):
        names = OrderedDict()
        names['actionX'] = 0
        names['actionY'] = 0
        names['actionThreshold'] = DEFAULT_TEMPLATE_THRESHOLD
        names['actionTmplExpdWPixel'] = DEFAULT_TMPL_EXPD_W_PIXEL
        names['actionTmplExpdHPixel'] = DEFAULT_TMPL_EXPD_H_PIXEL
        names['actionROIExpdWRatio'] = DEFAULT_EXPD_W_RATIO
        names['actionROIExpdHRatio'] = DEFAULT_EXPD_H_RATIO
        # create items
        for key, value in names.items():
            if key in actionDict.keys():
                treeItem.addChild(self.CreateTreeItem(key=key, value=actionDict.get(key), edit=True))
            else:
                treeItem.addChild(self.CreateTreeItem(key=key, value=value, edit=True))

    def _LoadDragAction(self, actionDict, treeItem):
        # build names
        names = OrderedDict()
        for id in [1, 2]:
            nameActionX = "actionX{}".format(id)
            names[nameActionX] = 0

            nameActionY = "actionY{}".format(id)
            names[nameActionY] = 0

            nameThreshold = "actionThreshold{}".format(id)
            names[nameThreshold] = DEFAULT_TEMPLATE_THRESHOLD

            nameActionTmplExpdWPixel = "actionTmplExpdWPixel{}".format(id)
            names[nameActionTmplExpdWPixel] = DEFAULT_TMPL_EXPD_W_PIXEL

            nameActionTmplExpdHPixel = "actionTmplExpdHPixel{}".format(id)
            names[nameActionTmplExpdHPixel] = DEFAULT_TMPL_EXPD_H_PIXEL

            nameActionROIExpdWRatio = "actionROIExpdWRatio{}".format(id)
            names[nameActionROIExpdWRatio] = DEFAULT_EXPD_W_RATIO

            nameActionROIExpdHRatio = "actionROIExpdHRatio{}".format(id)
            names[nameActionROIExpdHRatio] = DEFAULT_EXPD_H_RATIO

        # create items
        for key, value in names.items():
            if key in actionDict.keys():
                treeItem.addChild(self.CreateTreeItem(key=key, value=actionDict.get(key), edit=True))
            else:
                treeItem.addChild(self.CreateTreeItem(key=key, value=value, edit=True))

    '''
        生成默认的UI的element字典
        输入参数：actionType为click，drag，dragcheck
        输入参数：elementType表示gameOver，closeicon，uistates
        返回值：UI的element字典
    '''
    def GenerateUIActionDict(self, actionType, elementType):
        elementDict = OrderedDict()
        if elementType == "uiStates":
            elementDict["id"] = self.UIStatesIDIndex
            self.UIScriptIDIndex[self.UIStatesIDIndex] = 1

            self.UIStatesIDIndex += 1
        elif elementType == "gameOver":
            elementDict["id"] = self.UIGameOverIDIndex
            self.UIGameOverIDIndex += 1
        elementDict["actionType"] = actionType
        elementDict["desc"] = str()
        elementDict["imgPath"] = str()
        elementDict["x"] = 0
        elementDict["y"] = 0
        elementDict["w"] = 0
        elementDict["h"] = 0
        if elementType == "uiStates":
            elementDict["template"] = 0
            elementDict["keyPoints"] = DEFAULT_UI_KEYPOINT
            elementDict["checkSameFrameCnt"] = 5
            elementDict["delete"] = 0

        elementDict["shift"] = DEFAULT_UI_SHIFT
        elementDict["action"] = OrderedDict()
        if actionType == "click":
            elementDict["actionX"] = 0
            elementDict["actionY"] = 0
            elementDict["actionThreshold"] = DEFAULT_TEMPLATE_THRESHOLD
            elementDict["actionTmplExpdWPixel"] = DEFAULT_TMPL_EXPD_W_PIXEL
            elementDict["actionTmplExpdHPixel"] = DEFAULT_TMPL_EXPD_H_PIXEL
            elementDict["actionROIExpdWRatio"] = DEFAULT_EXPD_W_RATIO
            elementDict["actionROIExpdHRatio"] = DEFAULT_EXPD_H_RATIO
            
        elif actionType == "drag":
            elementDict["actionX1"] = 0
            elementDict["actionY1"] = 0
            elementDict["actionThreshold1"] = DEFAULT_TEMPLATE_THRESHOLD
            elementDict["actionTmplExpdWPixel1"] = DEFAULT_TMPL_EXPD_W_PIXEL
            elementDict["actionTmplExpdHPixel1"] = DEFAULT_TMPL_EXPD_H_PIXEL
            elementDict["actionROIExpdWRatio1"] = DEFAULT_EXPD_W_RATIO
            elementDict["actionROIExpdHRatio1"] = DEFAULT_EXPD_H_RATIO
            elementDict["actionX2"] = 0
            elementDict["actionY2"] = 0
            elementDict["actionThreshold2"] = DEFAULT_TEMPLATE_THRESHOLD
            elementDict["actionTmplExpdWPixel2"] = DEFAULT_TMPL_EXPD_W_PIXEL
            elementDict["actionTmplExpdHPixel2"] = DEFAULT_TMPL_EXPD_H_PIXEL
            elementDict["actionROIExpdWRatio2"] = DEFAULT_EXPD_W_RATIO
            elementDict["actionROIExpdHRatio2"] = DEFAULT_EXPD_H_RATIO
        elif actionType == "dragcheck":
            elementDict["actionDir"] = "down"
            elementDict["dragX"] = 0
            elementDict["dragY"] = 0
            elementDict["dragLen"] = 80
            elementDict["targetImg"] = ""
            elementDict["targetX"] = 0
            elementDict["targetY"] = 0
            elementDict["targetW"] = 0
            elementDict["targetH"] = 0
        elif actionType == TYPE_UIACTION_SCRIPT:
            elementDict["scriptPath"] = ""
            elementDict["tasks"] = []
            task = dict()
            task["taskid"] = 0
            task["type"] = "click"
            task["actionX"] = 0
            task["actionY"] = 0
            task["duringTimeMs"] = 100
            task["sleepTimeMs"] = 100
            elementDict["tasks"].append(task)

        return elementDict