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
from libs.CommonDialog import *

class CTaskConfig(AbstractModule):
    def __init__(self, MainWindow=None, ui=None):
        AbstractModule.__init__(self, MainWindow, ui)

        # 添加场景的动作，与maniWindow中的右键菜单绑定
        self.actionAddScene = QAction(MainWindow)
        self.actionAddScene.setText("添加场景")
        self.actionAddScene.triggered.connect(self.AddScene)           # 当触发添加场景的动作时，会执行AddScene函数

        # 添加任务的动作，与maniWindow中的右键菜单绑定
        self.actionAddTask = QAction(MainWindow)
        self.actionAddTask.setText("添加任务")
        self.actionAddTask.triggered.connect(self.AddTask)             # 当触发添加任务的动作时，会执行AddTask函数

        # 添加任务元素的动作，与maniWindow中的右键菜单绑定
        self.actionAddElement = QAction(MainWindow)
        self.actionAddElement.setText("添加任务元素")
        self.actionAddElement.triggered.connect(self.AddElement)       # 当触发添加任务元素的动作时，会执行AddElement函数

        # 添加模板的动作，与maniWindow中的右键菜单绑定
        self.actionAddTemplate = QAction(MainWindow)
        self.actionAddTemplate.setText("添加模板")
        self.actionAddTemplate.triggered.connect(self.AddTemplate)     # 当触发添加场景的动作时，会执行AddTemplate函数

        # 添加参考任务的动作，与maniWindow中的右键菜单绑定
        self.actionAddRefer = QAction(MainWindow)
        self.actionAddRefer.setText("添加参考任务")
        self.actionAddRefer.triggered.connect(self.AddReferTask)       # 当触发添加场景的动作时，会执行AddReferTask函数

        self.actionDetailConf = QAction(MainWindow)
        self.actionDetailConf.setText("更多配置")
        self.actionDetailConf.triggered.connect(self.ShowDetailConf)

        self.actionHiddenConf = QAction(MainWindow)
        self.actionHiddenConf.setText("隐藏非关键配置")
        self.actionHiddenConf.triggered.connect(self.HiddenReferConf)
        
        # 初始化一些对话框
        self.sceneNameDialog = customDialog(text="输入场景名", parent=self.mainWindow)
        self.taskNameDialog = customDialog(text="输入任务名", parent=self.mainWindow)
        self.elementNameDialog = customDialog(text="输入元素名", parent=self.mainWindow)
        self.templateNameDialog = customDialog(text="输入模板名", parent=self.mainWindow)

        # 初始化导入每种任务的函数字典
        self.LoadTaskFunc = OrderedDict()
        self.LoadTaskFunc[TASK_TYPE_FIXOBJ] = self.LoadFixObjTask
        self.LoadTaskFunc[TASK_TYPE_PIX] = self.LoadPixTask
        self.LoadTaskFunc[TASK_TYPE_STUCK] = self.LoadStuckTask
        self.LoadTaskFunc[TASK_TYPE_DEFORM] = self.LoadDeformTask
        self.LoadTaskFunc[TASK_TYPE_NUMBER] = self.LoadNumberTask
        self.LoadTaskFunc[TASK_TYPE_FIXBLOOD] = self.LoadFixBloodTask
        self.LoadTaskFunc[TASK_TYPE_DEFORMBLOOD] = self.LoadDeformBloodTask

        # 初始化ID
        self.groupIDIndex = 1
        self.taskIDIndex = 1
        self.elementIDIndex = 1
        self.templateIDIndex = 1

    # 从project.json中读取起始的ID号
    def SetProjectDict(self, projectDict=None):
        self.projectDict = projectDict
        self.groupIDIndex = self.projectDict[
            "groupIDStart"] if "groupIDStart" in self.projectDict.keys() is not None else 1
        self.taskIDIndex = self.projectDict[
            "taskIDStart"] if "taskIDStart" in self.projectDict.keys() is not None else 1
        self.elementIDIndex = self.projectDict[
            "elementIDStart"] if "elementIDStart" in self.projectDict.keys() is not None else 1
        self.templateIDIndex = self.projectDict[
            "templateIDStart"] if "templateIDStart" in self.projectDict.keys() is not None else 1

    '''
        将树结构的task和refer转换成字典，返回给mainWindow中的函数
        返回值：taskJsonDict表示task字典，referJsonDict表示refer字典
    '''
    def SaveTaskFile(self):
        taskJsonDict = OrderedDict()
        referJsonDict = OrderedDict()
        topLevelItem = self.ui.treeWidget.topLevelItem(0)

        if topLevelItem is None:
            return

        # 遍历每个version，每个version都会对应有一个task的dict和refer的dict
        for versionIndex in range(topLevelItem.childCount()):
            # 将树结构转换成task和refer的字典，可参照task.json和refer.json的格式来阅读
            versionItem = topLevelItem.child(versionIndex)
            taskVersionDict = OrderedDict()
            taskVersionDict["allTask"] = list()
            referVersionDict = OrderedDict()
            referVersionDict["allTask"] = list()
            if versionItem.text(0) in ["project.json", "project.json~"]:
                continue

            for sceneIndex in range(versionItem.childCount()):
                sceneItem = versionItem.child(sceneIndex)
                sceneKey = sceneItem.text(0)
                if sceneKey == "scene":
                    sceneDict, referDict = self.TaskTree2Dict(sceneItem)
                    taskVersionDict["allTask"].append(sceneDict)
                    referVersionDict["allTask"].append(referDict)

            taskJsonDict[versionItem.text(0)] = taskVersionDict
            referJsonDict[versionItem.text(0)] = referVersionDict
        return taskJsonDict, referJsonDict

    '''
        将task的结构树转换成字典，可参考task.json和refer.json的格式来阅读
        输入参数：sceneItem表示场景的item，是整个task的根节点
        返回值：sceneDict表示task.json中场景字典，referDict表示refer.json中的场景字典
    '''
    def TaskTree2Dict(self, sceneItem):
        if sceneItem is None:
            self.logger.error("TaskTree2Dict failed, sceneItem is None")
            return

        sceneDict = OrderedDict()
        referDict = OrderedDict()
        # 遍历子节点
        for taskIndex in range(sceneItem.childCount()):
            taskItem = sceneItem.child(taskIndex)
            taskKey = taskItem.text(0)
            taskDict = OrderedDict()
            # 如果子item的key是“task”
            if taskKey == "task":
                # 向task和refer的dict中添加key为“task”的数组
                if "task" not in sceneDict.keys():
                    sceneDict["task"] = list()
                if "task" not in referDict.keys():
                    referDict["task"] = list()

                objElementIndex = 0
                # 遍历task item的子节点，其子节点可能为
                # ”elements“，”type“，”taskID“， ”skipFrame“等等
                for elementIndex in range(taskItem.childCount()):
                    # 将element树结构转换为字典
                    elementItem = taskItem.child(elementIndex)
                    elementKey = elementItem.text(0)
                    elementDict = OrderedDict()                # element字典
                    if elementKey == "element":
                        # 如果是第一次，则需要将taskDict["elements"]设为数组
                        if "elements" not in taskDict.keys():
                            taskDict["elements"] = list()

                        # 遍历element  item的子节点，其子节点可能为
                        # ”ROI“表示检测区域
                        # ”algorithm“
                        # minScale
                        # maxScale
                        # scaleLevel
                        # template表示模板
                        for templateIndex in range(elementItem.childCount()):
                            templateItem = elementItem.child(templateIndex)
                            templateKey = templateItem.text(0)
                            # 如果为template子节点，则调用SaveTemplate函数来将template树结构转换为字典
                            if templateKey == "template":
                                if "templates" not in elementDict.keys():
                                    elementDict["templates"] = list()
                                elementDict["templates"].append(self.SaveTemplate(templateItem))
                            # 如果为algorithm子节点，因为其value是一个下拉选项框，因此要将其值读出来，填到字典里
                            elif templateKey == "algorithm":
                                comBox = self.ui.treeWidget.itemWidget(templateItem, 1)
                                elementDict[templateKey] = comBox.currentText()
                            # 如果为ROI子节点，则调用SaveRect将ROI的树结构转换为字典
                            elif templateKey == "ROI":
                                elementID = self.GetChildItemValue(elementItem, 0, "elementID", 1)
                                self.mainWindow.projectDict["TaskImagePath"]["element"][elementID] = elementItem.text(3)
                                elementDict[templateKey] = self.SaveRect(templateItem)
                            # 如果key值在以下集合中，则说明value是浮点型数字
                            elif templateKey in ["minScale", "maxScale", "threshold", "intervalTime"]:
                                elementDict[templateKey] = float(templateItem.text(1))
                            # 如果key值在以下集合中，则说明value是整型数字
                            elif templateKey in ["elementID", "scaleLevel", "filterSize", "maxPointNum", "maxBBoxNum"]:
                                elementDict[templateKey] = int(templateItem.text(1))
                            # 如果key值为refer，则调用ReferTree2Dict将refer树结构转换为字典
                            # 并且填充objTask，objElement字段
                            elif templateKey == "refer":
                                referTaskDict = self.ReferTree2Dict(templateItem)
                                referTaskDict["objTask"] = taskDict["taskID"]
                                referTaskDict["objElements"] = list()
                                referTaskDict["objElements"].append(objElementIndex)
                                referDict[taskKey].append(referTaskDict)
                            # 最后说明value是字符串，直接填入字典
                            else:
                                elementDict[templateKey] = templateItem.text(1)
                        taskDict["elements"].append(elementDict)
                        objElementIndex += 1
                    elif elementKey == "type":
                        comBox = self.ui.treeWidget.itemWidget(elementItem, 1)
                        taskDict[elementKey] = comBox.currentText()
                    elif elementKey in ["taskID", "skipFrame"]:
                        taskDict[elementKey] = int(elementItem.text(1))
                    else:
                        taskDict[elementKey] = elementItem.text(1)
                sceneDict[taskKey].append(taskDict)
            elif taskKey == "groupID":
                sceneDict[taskKey] = int(taskItem.text(1))
                referDict[taskKey] = int(taskItem.text(1))
            else:
                sceneDict[taskKey] = taskItem.text(1)
                referDict[taskKey] = taskItem.text(1)

        return sceneDict, referDict

    '''
        将refer树结构转换为字典
        输入参数：referItem表示refer的根节点
        返回值：referDict表示refer任务的字典
    '''
    def ReferTree2Dict(self, referItem):
        if referItem is None:
            self.logger.error("ReferTree2Dict failed, referItem is None")
            return

        # 遍历referDict item的子节点
        referDict = OrderedDict()
        for referIndex in range(referItem.childCount()):
            childItem = referItem.child(referIndex)
            childKey = childItem.text(0)
            # 如果key值在以下集合内，说明value是整型
            if childKey in ["taskID", "skipFrame", "scaleLevel", "matchCount"]:
                referDict[childKey] = int(childItem.text(1))
            # 如果key值在以下集合内，说明value浮点型
            elif childKey in ["minScale", "maxScale", "expandWidth", "expandHeight"]:
                referDict[childKey] = float(childItem.text(1))
            # 如果key值在以下集合内，说明value是下拉选项框
            elif childKey in ["type", "algorithm"]:
                combox = self.ui.treeWidget.itemWidget(childItem, 1)
                referDict[childKey] = combox.currentText()
            # 如果key值在以下集合内，conditions是数组
            elif childKey in ["conditions"]:
                referDict["Conditions"] = list()
                for conditionIndex in range(childItem.childCount()):
                    referDict["Conditions"].append(childItem.child(conditionIndex).text(1))
            # 如果key值在以下集合内，应该将rect树结构转换为字典
            elif childKey in ["location", "inferROI"]:
                referDict[childKey] = self.SaveRect(childItem)
                
            # 命名修改 'location'--->'templateLocation',保存文件命名和原来保持一致
            elif childKey in ["templateLocation"]:
                referDict["location"] = self.SaveRect(childItem)

            # 如果key值在以下集合内，将多个rect树结构转换为数组
            elif childKey in ["inferLocations"]:
                referDict[childKey] = list()
                for inferLocationIndex in range(childItem.childCount()):
                    inferLocationItem = childItem.child(inferLocationIndex)
                    referDict[childKey].append(self.SaveRect(inferLocationItem))

            # 命名修改 'inferLocations'--->'inferSubROIs',保存文件命名和原来保持一致
            elif childKey in ["inferSubROIs"]:
                referDict["inferLocations"] = list()
                for inferLocationIndex in range(childItem.childCount()):
                    inferLocationItem = childItem.child(inferLocationIndex)
                    referDict["inferLocations"].append(self.SaveRect(inferLocationItem))

            # 如果key值在以下集合内，将所有template树结构都转换为字典
            elif childKey in ["templates"]:
                referDict[childKey] = list()
                for templateIndex in range(childItem.childCount()):
                    templateItem = childItem.child(templateIndex)
                    referDict[childKey].append(self.SaveTemplate(templateItem))
            else:
                referDict[childKey] = childItem.text(1)

        self.UpdateReferDict(referDict)
        self.mainWindow.projectDict["ReferImagePath"][str(referDict["taskID"])] = referItem.text(3)

        return referDict

    def UpdateReferDict(self, referDict):
        for template in referDict.get("templates") or []:
            # delete 'template[location]' in referDict
            template.pop('location')

        inferSubROIs = referDict.get('inferLocations')
        inferROI = referDict.get("inferROI")

        if None in [inferSubROIs, inferROI]:
            self.logger.info("inferSubROIs or inferROI not in referDict, please check")
            return

        if len(inferSubROIs) < 1:
            self.logger.info("inferSubROIs is None, please check")
            return

        if 0 in [int(inferSubROIs[0].get('w')), int(inferSubROIs[0].get('h'))]:
            inferSubROIs[0]['x'] = inferROI.get('x')
            inferSubROIs[0]['y'] = inferROI.get('y')
            inferSubROIs[0]['w'] = inferROI.get('w')
            inferSubROIs[0]['h'] = inferROI.get('h')

    '''
        将template树结构转换为字典
        输入参数：treeItem表示template的根节点
        返回值：templateDict表示template字典
    '''
    def SaveTemplate(self, treeItem):
        if treeItem is None:
            self.logger.error("SaveTemplate failed, treeItem is None")
            return

        templateDict = OrderedDict()
        for templateIndex in range(treeItem.childCount()):
            templateItem = treeItem.child(templateIndex)
            templateKey = templateItem.text(0)
            if templateKey == "location":
                templateID = self.GetChildItemValue(treeItem, 0, "templateID", 1)
                self.mainWindow.projectDict["TaskImagePath"]["template"][templateID] = treeItem.text(3)
                templateDict[templateKey] = self.SaveRect(templateItem)
            elif templateKey == "threshold":
                templateDict[templateKey] = float(templateItem.text(1))
            elif templateKey == "classID":
                templateDict[templateKey] = int(templateItem.text(1))
            else:
                templateDict[templateKey] = templateItem.text(1)
        return templateDict

    '''
        将rect树结构转换为字典
        输入参数：treeItem表示rect的根节点
        返回值：rectDict表示rect字典
    '''
    def SaveRect(self, treeItem):
        if treeItem is None:
            self.logger.error("SaveRect failed, treeItem is None")
            return

        rectDict = OrderedDict()
        for rectIndex in range(treeItem.childCount()):
            rectItem = treeItem.child(rectIndex)
            rectDict[rectItem.text(0)] = int(rectItem.text(1))
        return rectDict

    '''
        导入task.json内容，并且生成对应的树结构
        输入参数：taskJsonDict表示导入的task字典
        输入参数：treeItemVersion表示version节点，生成的task树会挂在该节点下
    '''
    def LoadTaskJson(self, taskJsonDict, treeItemVersion):
        if treeItemVersion is None:
            self.logger.error("LoadTaskJson failed, treeItemVersion is None")
            return

        if taskJsonDict is None:
            self.logger.error("LoadTaskJson failed, taskJsonDict is None")
            return

        # 兼容alltask和allTask
        if "alltask" in taskJsonDict.keys():
            allTask = taskJsonDict["alltask"]
        elif "allTask" in taskJsonDict.keys():
            allTask = taskJsonDict["allTask"]
        else:
            self.logger.error("alltask or allTask is needed")
            return

        # 遍历每一个场景，生成对应场景的树
        for scene in allTask:
            groupID = scene["groupID"]
            if groupID >= self.groupIDIndex:
                self.groupIDIndex = groupID + 1
            if "name" in scene.keys():
                sceneName = scene["name"]
            elif "description" in scene.keys():
                sceneName = scene["description"]
            else:
                self.logger.error("name or description is needed")
                return

            childScene = self.CreateTreeItem(key='scene', value=sceneName, type=ITEM_TYPE_SCENE)
            childScene.addChild(self.CreateTreeItem(key='groupID', value=groupID))
            childScene.addChild(self.CreateTreeItem(key='name', value=sceneName))

            # 兼容”tasks“和”task“
            if "tasks" in scene.keys():
                taskKey = "tasks"
            elif "task" in scene.keys():
                taskKey = "task"
            else:
                taskKey = None

            # 遍历task数组，生成对应的task任务树结构
            if taskKey is not None:
                for task in scene[taskKey]:
                    taskTreeItem = self.CreateTaskTree(task)
                    childScene.addChild(taskTreeItem)
                    taskTreeItem.setExpanded(True)

            # 将生成的场景树结构添加至version节点下
            treeItemVersion.addChild(childScene)

            childScene.setExpanded(True)
            self.HiddenItem(treeItemVersion)
    '''
        导入fexObj类型的element任务，生成element树结构
        输入参数：fixObjElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadFixObjTask(self, fixObjElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadFixObjTask failed, treeItemTask is None")
            return

        if fixObjElement is None:
            self.logger.error("LoadFixObjTask failed, fixObjElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "algorithm" not in fixObjElement.keys():
            fixObjElement["algorithm"] = DEFAULT_FIXOBJ_ALGORITHM
        if "minScale" not in fixObjElement.keys():
            fixObjElement["minScale"] = DEFAULT_MINSCALE
        if "maxScale" not in fixObjElement.keys():
            fixObjElement["maxScale"] = DEFAULT_MAXSCALE
        if "scaleLevel" not in fixObjElement.keys():
            fixObjElement["scaleLevel"] = DEFAULT_SCALELEVEL
        if "ROI" not in fixObjElement.keys():
            fixObjElement["ROI"] = OrderedDict()
        if "maxBBoxNum" not in fixObjElement.keys():
            fixObjElement["maxBBoxNum"] = DEFAULT_MAX_BBOXNUM
        if "templates" not in fixObjElement.keys():
            fixObjElement["templates"] = list()
        if "elementID" not in fixObjElement.keys():
            fixObjElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1
        if "templates" not in fixObjElement.keys():
            fixObjElement["templates"] = [OrderedDict()]
        if "elementName" not in fixObjElement.keys():
            fixObjElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=fixObjElement["elementName"], type=ITEM_TYPE_ELEMENT)

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(fixObjElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(fixObjElement["elementID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if "templates" in fixObjElement.keys():
                for template in fixObjElement["templates"]:
                    if template["path"] is not None and template["path"] != "":
                        childElement.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemTask.addChild(childElement)

        # 以下为创建fixobj的各个节点，如elementID（隐藏），ROI，algorithm，minScale，maxScale等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=fixObjElement["elementID"]))
        if fixObjElement["elementID"] >= self.elementIDIndex:
            self.elementIDIndex = fixObjElement["elementID"] + 1

        childElement.addChild(self.CreateTreeItem(key='elementName', value=fixObjElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(fixObjElement["ROI"], childROI)

        childAlgorithm = self.CreateTreeItem(key='algorithm')
        childElement.addChild(childAlgorithm)
        qCombox = QComboBox()
        qCombox.addItems([
            ALGORITHM_FIXOBJ_COLORMATCH,
            ALGORITHM_FIXOBJ_GRADMATCH,
            ALGORITHM_FIXOBJ_EDGEMATCH,
            ALGORITHM_FIXOBJ_ORBMATCH
        ])
        qCombox.setCurrentText(fixObjElement["algorithm"])
        self.ui.treeWidget.setItemWidget(childAlgorithm, 1, qCombox)

        childElement.addChild(self.CreateTreeItem(key='minScale', value=fixObjElement["minScale"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxScale', value=fixObjElement["maxScale"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='scaleLevel', value=fixObjElement["scaleLevel"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxBBoxNum', value=fixObjElement["maxBBoxNum"], edit=True))

        # 创建模板
        for template in fixObjElement["templates"]:
            self.LoadTemplate(template, childElement)

    '''
        导入deform类型的element任务，生成element树结构
        输入参数：deformElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadDeformTask(self, deformElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadDeformTask failed, treeItemTask is None")
            return

        if deformElement is None:
            self.logger.error("LoadDeformTask failed, deformElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "threshold" not in deformElement.keys():
            deformElement["threshold"] = DEFAULT_DEFORM_THRESHOLD
        if "ROI" not in deformElement.keys():
            deformElement["ROI"] = OrderedDict()
        if "cfgPath" not in deformElement.keys():
            deformElement["cfgPath"] = str()
        if "namePath" not in deformElement.keys():
            deformElement["namePath"] = str()
        if "weightPath" not in deformElement.keys():
            deformElement["weightPath"] = str()
        if "maskPath" not in deformElement.keys():
            deformElement["maskPath"] = str()
        if "elementID" not in deformElement.keys():
            deformElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1
        if "elementName" not in deformElement.keys():
            deformElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=deformElement["elementName"], type=ITEM_TYPE_ELEMENT)

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(deformElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(deformElement["elementID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if "templates" in deformElement.keys():
                for template in deformElement["templates"]:
                    if template["path"] is not None and template["path"] != "":
                        childElement.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemTask.addChild(childElement)

        # 以下为创建deform的各个节点，如elementID（隐藏），ROI，cfgPath，weightPath，namePath等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=deformElement["elementID"]))
        if deformElement["elementID"] >= self.elementIDIndex:
            self.elementIDIndex = deformElement["elementID"] + 1
        childElement.addChild(self.CreateTreeItem(key='elementName', value=deformElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(deformElement["ROI"], childROI)

        childElement.addChild(self.CreateTreeItem(key='cfgPath', value=deformElement["cfgPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='weightPath', value=deformElement["weightPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='namePath', value=deformElement["namePath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maskPath', value=deformElement["maskPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='threshold', value=deformElement["threshold"], edit=True))

    '''
        导入pix类型的element任务，生成element树结构
        输入参数：pixElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadPixTask(self, pixElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadPixTask failed, treeItemTask is None")
            return

        if pixElement is None:
            self.logger.error("LoadPixTask failed, pixElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "filterSize" not in pixElement.keys():
            pixElement["filterSize"] = DEFAULT_FILTERSIZE
        if "maxPointNum" not in pixElement.keys():
            pixElement["maxPointNum"] = DEFAULT_MAXPOINTNUM
        if "ROI" not in pixElement.keys():
            pixElement["ROI"] = OrderedDict()
        if "condition" not in pixElement.keys():
            pixElement["condition"] = str()
        if "elementID" not in pixElement.keys():
            pixElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1
        if "elementName" not in pixElement.keys():
            pixElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=pixElement["elementName"], type=ITEM_TYPE_ELEMENT)

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(pixElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(pixElement["elementID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if "templates" in pixElement.keys():
                for template in pixElement["templates"]:
                    if template["path"] is not None and template["path"] != "":
                        childElement.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemTask.addChild(childElement)

        # 以下为创建pixel的各个节点，如elementID（隐藏），ROI，condition，filterSize，maxPointNum等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=pixElement["elementID"]))
        if pixElement["elementID"] >= self.elementIDIndex:
            self.elementIDIndex = pixElement["elementID"] + 1
        childElement.addChild(self.CreateTreeItem(key='elementName', value=pixElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(pixElement["ROI"], childROI)

        childElement.addChild(self.CreateTreeItem(key='condition', value=pixElement["condition"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='filterSize', value=pixElement["filterSize"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxPointNum', value=pixElement["maxPointNum"], edit=True))

    '''
        导入number类型的element任务，生成element树结构
        输入参数：numberElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadNumberTask(self, numberElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadNumberTask failed, treeItemTask is None")
            return

        if numberElement is None:
            self.logger.error("LoadNumberTask failed, numberElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "algorithm" not in numberElement.keys():
            numberElement["algorithm"] = DEFAULT_NUMBER_ALGORITHM
        if "minScale" not in numberElement.keys():
            numberElement["minScale"] = DEFAULT_MINSCALE
        if "maxScale" not in numberElement.keys():
            numberElement["maxScale"] = DEFAULT_MAXSCALE
        if "scaleLevel" not in numberElement.keys():
            numberElement["scaleLevel"] = DEFAULT_SCALELEVEL
        if "ROI" not in numberElement.keys():
            numberElement["ROI"] = OrderedDict()
        if "templates" not in numberElement.keys():
            numberElement["templates"] = list()
        if "elementID" not in numberElement.keys():
            numberElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1
        if "templates" not in numberElement.keys():
            numberElement["templates"] = [OrderedDict()]
        if "elementName" not in numberElement.keys():
            numberElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=numberElement["elementName"], type=ITEM_TYPE_ELEMENT)

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(numberElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(numberElement["elementID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if "templates" in numberElement.keys():
                for template in numberElement["templates"]:
                    if template["path"] is not None and template["path"] != "":
                        childElement.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemTask.addChild(childElement)

        # 以下为创建number的各个节点，如elementID（隐藏），ROI，algorithm，minScale，maxScale等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=numberElement["elementID"]))
        if numberElement["elementID"] >= self.elementIDIndex:
            self.elementIDIndex = numberElement["elementID"] + 1
        childElement.addChild(self.CreateTreeItem(key='elementName', value=numberElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(numberElement["ROI"], childROI)

        childAlgorithm = self.CreateTreeItem(key='algorithm')
        childElement.addChild(childAlgorithm)
        qCombox = QComboBox()
        qCombox.addItems([
            ALGORITHM_NUMBER_TEMPLATEMATCH
        ])
        qCombox.setCurrentText(numberElement["algorithm"])
        self.ui.treeWidget.setItemWidget(childAlgorithm, 1, qCombox)

        childElement.addChild(self.CreateTreeItem(key='minScale', value=numberElement["minScale"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxScale', value=numberElement["maxScale"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='scaleLevel', value=numberElement["scaleLevel"], edit=True))

        # 导入所有模板，生成树结构
        for template in numberElement["templates"]:
            self.LoadTemplate(template, childElement)

    '''
        导入stuck类型的element任务，生成element树结构
        输入参数：stuckElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadStuckTask(self, stuckElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadStuckTask failed, treeItemTask is None")
            return

        if stuckElement is None:
            self.logger.error("LoadStuckTask failed, stuckElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "threshold" not in stuckElement.keys():
            stuckElement["threshold"] = DEFAULT_STUCK_THRESHOLD
        if "intervalTime" not in stuckElement.keys():
            stuckElement["intervalTime"] = DEFAULT_INTERVALTIME
        if "ROI" not in stuckElement.keys():
            stuckElement["ROI"] = OrderedDict()
        if "elementID" not in stuckElement.keys():
            stuckElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1
        if "elementName" not in stuckElement.keys():
            stuckElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=stuckElement["elementName"], type=ITEM_TYPE_ELEMENT)

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(stuckElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(stuckElement["elementID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if "templates" in stuckElement.keys():
                for template in stuckElement["templates"]:
                    if template["path"] is not None and template["path"] != "":
                        childElement.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemTask.addChild(childElement)

        # 以下为创建stuck的各个节点，如elementID（隐藏），ROI，intervalTime，threshold等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=stuckElement["elementID"]))
        if stuckElement["elementID"] >= self.elementIDIndex:
            self.elementIDIndex = stuckElement["elementID"] + 1
        childElement.addChild(self.CreateTreeItem(key='elementName', value=stuckElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(stuckElement["ROI"], childROI)

        childElement.addChild(self.CreateTreeItem(key='intervalTime', value=stuckElement["intervalTime"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='threshold', value=stuckElement["threshold"], edit=True))

    '''
        导入fix blood类型的element任务，生成element树结构
        输入参数：bloodElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadFixBloodTask(self, bloodElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadFixBloodTask failed, treeItemTask is None")
            return

        if bloodElement is None:
            self.logger.error("LoadFixBloodTask failed, stuckElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "condition" not in bloodElement.keys():
            bloodElement["condition"] = str()

        if "ROI" not in bloodElement.keys():
            bloodElement["ROI"] = OrderedDict()

        if "bloodLength" not in bloodElement.keys():
            bloodElement["bloodLength"] = DEFAULT_BLOODLENGTH

        if "filterSize" not in bloodElement.keys():
            bloodElement["filterSize"] = DEFAULT_FILTERSIZE

        if "maxPointNum" not in bloodElement.keys():
            bloodElement["maxPointNum"] = DEFAULT_MAXPOINTNUM

        if "elementName" not in bloodElement.keys():
            bloodElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=bloodElement["elementName"], type=ITEM_TYPE_ELEMENT)

        if "elementID" not in bloodElement.keys():
            bloodElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(bloodElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(bloodElement["elementID"])])

        treeItemTask.addChild(childElement)

        # 以下为创建stuck的各个节点，如elementID（隐藏），ROI，intervalTime，threshold等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=bloodElement["elementID"]))
        if bloodElement["elementID"] >= self.elementIDIndex:
             self.elementIDIndex = bloodElement["elementID"] + 1

        childElement.addChild(self.CreateTreeItem(key='elementName', value=bloodElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(bloodElement["ROI"], childROI)

        childElement.addChild(self.CreateTreeItem(key='condition', value=bloodElement["condition"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='bloodLength', value=bloodElement["bloodLength"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='filterSize', value=bloodElement["filterSize"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxPointNum', value=bloodElement["maxPointNum"], edit=True))

    '''
        导入deform blood类型的element任务，生成element树结构
        输入参数：deformBloodElement表示从task.json中读取的element内容
        输入参数：treeItemTask表示task节点，生成的element任务树结构会添加至该节点下
    '''
    def LoadDeformBloodTask(self, deformBloodElement, treeItemTask):
        if treeItemTask is None:
            self.logger.error("LoadFixBloodTask failed, treeItemTask is None")
            return

        if deformBloodElement is None:
            self.logger.error("LoadFixBloodTask failed, stuckElement is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "ROI" not in deformBloodElement.keys():
            deformBloodElement["ROI"] = OrderedDict()

        if "cfgPath" not in deformBloodElement.keys():
            deformBloodElement["cfgPath"] = str()

        if "weightPath" not in deformBloodElement.keys():
            deformBloodElement["weightPath"] = str()

        if "namePath" not in deformBloodElement.keys():
            deformBloodElement["namePath"] = str()

        if "maskPath" not in deformBloodElement.keys():
            deformBloodElement["maskPath"] = str()

        if "threshold" not in deformBloodElement.keys():
            deformBloodElement["threshold"] = DEFAULT_STUCK_THRESHOLD

        if "condition" not in deformBloodElement.keys():
            deformBloodElement["condition"] = str()

        if "bloodLength" not in deformBloodElement.keys():
            deformBloodElement["bloodLength"] = DEFAULT_BLOODLENGTH

        if "filterSize" not in deformBloodElement.keys():
            deformBloodElement["filterSize"] = DEFAULT_FILTERSIZE

        if "maxPointNum" not in deformBloodElement.keys():
            deformBloodElement["maxPointNum"] = DEFAULT_MAXPOINTNUM

        if "elementName" not in deformBloodElement.keys():
            deformBloodElement["elementName"] = str()

        # 创建element的节点
        childElement = self.CreateTreeItem(key='element', value=deformBloodElement["elementName"], type=ITEM_TYPE_ELEMENT)

        if "elementID" not in deformBloodElement.keys():
            deformBloodElement["elementID"] = self.elementIDIndex
            self.elementIDIndex += 1

        # 根据elementID，得到project.json中的图像配置路径，将路径填到新创建的element节点的第四列（默认第四列隐藏）
        if str(deformBloodElement["elementID"]) in self.projectDict["TaskImagePath"]["element"].keys():
            childElement.setText(3, self.projectDict["TaskImagePath"]["element"][str(deformBloodElement["elementID"])])

        treeItemTask.addChild(childElement)

        # 以下为创建stuck的各个节点，如elementID（隐藏），ROI，intervalTime，threshold等
        childElement.addChild(self.CreateTreeItem(key='elementID', value=deformBloodElement["elementID"]))
        if deformBloodElement["elementID"] >= self.elementIDIndex:
             self.elementIDIndex = deformBloodElement["elementID"] + 1

        childElement.addChild(self.CreateTreeItem(key='elementName', value=deformBloodElement["elementName"]))

        childROI = self.CreateTreeItem(key='ROI')
        childElement.addChild(childROI)
        self.LoadRect(deformBloodElement["ROI"], childROI)

        childElement.addChild(self.CreateTreeItem(key='cfgPath', value=deformBloodElement["cfgPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='weightPath', value=deformBloodElement["weightPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='namePath', value=deformBloodElement["namePath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maskPath', value=deformBloodElement["maskPath"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='threshold', value=deformBloodElement["threshold"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='condition', value=deformBloodElement["condition"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='bloodLength', value=deformBloodElement["bloodLength"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='filterSize', value=deformBloodElement["filterSize"], edit=True))
        childElement.addChild(self.CreateTreeItem(key='maxPointNum', value=deformBloodElement["maxPointNum"], edit=True))


    '''
        导入模板，将模板字典转换为模板树结构
        输入参数：template表示模板字典
        输入参数：treeItemElement表示template树结构的父节点
    '''
    def LoadTemplate(self, template, treeItemElement):
        if treeItemElement is None:
            self.logger.error("LoadTemplate failed, treeItemElement is None")
            return

        if template is None:
            self.logger.error("LoadTemplate failed, template is None")
            return

        # 如果传入的字典不包含这些字段，则应该给它一个默认值
        if "threshold" not in template.keys():
            template["threshold"] = DEFAULT_TEMPLATE_THRESHOLD
        if "location" not in template.keys():
            template["location"] = OrderedDict()
        if "name" not in template.keys():
            template["name"] = str()
        if "path" not in template.keys():
            template["path"] = str()
        if "classID" not in template.keys():
            template["classID"] = 0
        if "templateID" not in template.keys():
            template["templateID"] = self.templateIDIndex
            self.templateIDIndex += 1
        if "templateName" not in template.keys():
            template["templateName"] = str()

        # 创建template节点
        childTemplate = self.CreateTreeItem(key='template', value=template["templateName"], type=ITEM_TYPE_TEMPLATE)

        # 根据templateID，得到project.json中的图像配置路径，将路径填到新创建的template节点的第四列（默认第四列隐藏）
        if str(template["templateID"]) in self.projectDict["TaskImagePath"]["template"].keys():
            childTemplate.setText(3, self.projectDict["TaskImagePath"]["template"][str(template["templateID"])])
        else:
            # 如果在project.json中没有找到对应的路径，则说明可能是导入之前手动配置的文件，则需要查找其template中的path，将path填至第四列
            if template["path"] != "":
                childTemplate.setText(3, self.projectDict["projectPath"] + "/v1.0/" + template["path"])
        treeItemElement.addChild(childTemplate)

        # 创建template树的其他节点，如templateID（隐藏），path，name，location，threshold等
        if int(template["templateID"]) >= self.templateIDIndex:
            self.templateIDIndex = int(template["templateID"]) + 1
        childTemplate.addChild(self.CreateTreeItem(key='templateID', value=template["templateID"]))
        childTemplate.addChild(self.CreateTreeItem(key='templateName', value=template["templateName"]))
        childTemplate.addChild(self.CreateTreeItem(key='path', value=template["path"], edit=True,
                                                   type=ITEM_TYPE_TASK_IMG_PATH))
        childTemplate.addChild(self.CreateTreeItem(key='name', value=template["name"], edit=True))

        childLocation = self.CreateTreeItem(key='location')
        childTemplate.addChild(childLocation)
        self.LoadRect(template["location"], childLocation)

        childTemplate.addChild(self.CreateTreeItem(key='threshold', value=template["threshold"], edit=True))
        childTemplate.addChild(self.CreateTreeItem(key='classID', value=template["classID"], edit=True))

    '''
        从refer.json中导入参考任务的内容，并生成树结构
        输入参数：referJsonDict表示refer字典
        输入参数：treeItemVersion表示version节点，生成的refer树会挂在对应的task的element节点下
    '''
    def LoadReferJson(self, referJsonDict, treeItemVersion):
        if referJsonDict is None:
            self.logger.error("LoadReferJson failed, referJsonDict is None")
            return

        if treeItemVersion is None:
            self.logger.error("LoadReferJson failed, treeItemVersion is None")
            return

        # 兼容alltask和allTask
        if "alltask" in referJsonDict.keys():
            referAllTask = referJsonDict["alltask"]
        elif "allTask" in referJsonDict.keys():
            referAllTask = referJsonDict["allTask"]
        else:
            self.logger.error("there is no alltask")
            return

        # 遍历每个refer任务
        for scene in referAllTask:
            groupID = scene["groupID"]
            # 每个version都遍历一遍，当树中的changjingID等于当前groupID时，才进行下面的步骤
            for itemIndex in range(treeItemVersion.childCount()):
                childItem = treeItemVersion.child(itemIndex)
                if childItem.text(0) != "scene":
                    continue

                childGroupID = int(self.GetChildItemValue(childItem, 0, "groupID", 1))
                # 当树中的changjingID等于当前groupID时，才进行下面的步骤
                if childGroupID != groupID:
                    continue

                # 兼容tasks和task
                if "tasks" in scene.keys():
                    taskKey = "tasks"
                elif "task" in scene.keys():
                    taskKey = "task"
                else:
                    taskKey = None

                if taskKey is None:
                    continue

                # 遍历refer中的每个task
                for task in scene[taskKey]:
                    objTaskID = task["objTask"]
                    # 遍历树结构场景中的每个task节点
                    for taskItemIndex in range(childItem.childCount()):
                        taskItem = childItem.child(taskItemIndex)
                        # 当节点的key为task时，说明是task节点
                        if taskItem.text(0) != "task":
                            continue

                        # 获取task树结构中的taskID
                        childTaskID = int(self.GetChildItemValue(taskItem, 0, "taskID", 1))
                        # 如果不与objTaskID相等，说明该refer任务不是当前task的
                        if childTaskID != objTaskID:
                            continue

                        objElementIndex = 0
                        # 遍历task节点下的每个子节点
                        for elementIndex in range(taskItem.childCount()):
                            elementItem = taskItem.child(elementIndex)
                            # 当节点的key为element时，将refer树结构挂在该节点下
                            if elementItem.text(0) != "element":
                                continue

                            # 兼容objElement和objElements
                            if "objElement" in task.keys():
                                objElementKey = "objElement"
                            elif "objElements" in task.keys():
                                objElementKey = "objElements"
                            else:
                                objElementKey = None

                            if objElementKey is None:
                                continue

                            # 当该element索引与字典中objElement索引相同时，
                            # 说明是该element下的refer任务，将refer树结构挂在该节点下
                            if objElementIndex != task[objElementKey][0]:
                                continue

                            # 创建refer树结构
                            referItem = self.CreateLocationRefer(task)
                            referTaskID = int(
                                self.GetChildItemValue(referItem, 0, "taskID", 1))

                            # 从project.json中获取refer图像的路径，将路径存在refer根节点的第四列（第四列隐藏）
                            if str(referTaskID) in self.projectDict[
                                "ReferImagePath"].keys():
                                referItem.setText(3, self.projectDict["ReferImagePath"][
                                    str(referTaskID)])
                            else:
                                # 当无法从project.json获取路径时，说明可能导入之前手动配置的refer
                                # 因此需要查找template中的路径，存在根节点的第四列（第四列隐藏）
                                templateItem = self.GetChildItem(referItem, "templates")
                                for itemIndex in range(templateItem.childCount()):
                                    treeItem = templateItem.child(itemIndex)
                                    path = self.GetChildItemValue(treeItem, 0, "path", 1)
                                    if path is not None and path != "":
                                        version = treeItemVersion.text(0)
                                        referItem.setText(3, self.projectDict["projectPath"] + "/" + version + "/" + path)
                                        break

                            elementItem.addChild(referItem)
                            self.HiddenReferItem(referItem)

                            objElementIndex += 1
        self.HiddenItem(treeItemVersion)


    '''
        创建location类型的refer树结构
        输入参数：locationDict表示location字典
        返回值：QTreeItem表示refer的树结构的根节点
    '''
    def CreateLocationRefer(self, locationDict):
        if locationDict is None:
            self.logger.error("CreateLocationRefer failed, locationDict is None")
            return

        # 创建refer根节点，并创捷其他子节点，如taskID，type，skipFrame等等
        child = self.CreateTreeItem(key='refer', type=ITEM_TYPE_REFER_TASK)
        child.addChild(self.CreateTreeItem(key='taskID', value=locationDict['taskID']))

        taskType = locationDict["type"]
        childTaskType = self.CreateTreeItem(key='type')
        child.addChild(childTaskType)
        qCombox = QComboBox()
        qCombox.addItems([
            TASK_TYPE_REFER_LOCATION,
            TASK_TYPE_REFER_BLOODLENGTHREG
        ])
        qCombox.setCurrentText(taskType)
        qCombox.currentTextChanged.connect(self.ReferTaskComboxChange)
        self.ui.treeWidget.setItemWidget(childTaskType, 1, qCombox)

        child.addChild(self.CreateTreeItem(key='description', value=locationDict['description'], edit=True))
        if "skipFrame" not in locationDict.keys():
            skipFrame = 1
        else:
            skipFrame = locationDict["skipFrame"]
        child.addChild(self.CreateTreeItem(key='skipFrame', value=skipFrame, edit=True))

        algoType = locationDict["algorithm"]
        childTaskType = self.CreateTreeItem(key='algorithm')
        child.addChild(childTaskType)
        qCombox = QComboBox()
        if taskType == "location":
            qCombox.addItems([
                ALGORITHM_LOCATION_DETECT,
                ALGORITHM_LOCATION_INFER
            ])
        elif taskType == "bloodlengthreg":
            qCombox.addItems([
                ALGORITHM_BLOODLENGTHREG_TAPLATEMATCH
            ])
        qCombox.setCurrentText(algoType)
        qCombox.currentTextChanged.connect(self.ReferAlgorithmComboxChange)
        self.ui.treeWidget.setItemWidget(childTaskType, 1, qCombox)

        # optimize refer task name
        # childLocation = self.CreateTreeItem(key='location')
        childLocation = self.CreateTreeItem(key='templateLocation')

        self.LoadRect(locationDict["location"], childLocation)
        child.addChild(childLocation)

        # 如果是location的infer方法，还需要多加两个框
        if taskType == "location" and algoType == "Infer":
            childInferROI = self.CreateTreeItem(key='inferROI')
            self.LoadRect(locationDict["inferROI"], childInferROI)
            child.addChild(childInferROI)

            # 命名更改：　inferLocations--->inferSubROIs，显示更改，存储的文件不更改
            # childInferLocations = self.CreateTreeItem(key='inferLocations')
            childInferSubROIS = self.CreateTreeItem(key='inferSubROIs')
            child.addChild(childInferSubROIS)
            for ROIItem in locationDict["inferLocations"]:
                # 命名更改　inferLocation--->inferSubROI
                # childLocation = self.CreateTreeItem(key='inferLocation')
                childSubROI = self.CreateTreeItem(key='inferSubROI')
                self.LoadRect(ROIItem, childSubROI)
                childInferSubROIS.addChild(childSubROI)

        # 添加节点
        child.addChild(self.CreateTreeItem(key='minScale', value=locationDict['minScale'], edit=True))
        child.addChild(self.CreateTreeItem(key='maxScale', value=locationDict['maxScale'], edit=True))
        child.addChild(self.CreateTreeItem(key='scaleLevel', value=locationDict['scaleLevel'], edit=True))
        child.addChild(self.CreateTreeItem(key='expandWidth', value=locationDict['expandWidth'], edit=True))
        child.addChild(self.CreateTreeItem(key="expandHeight", value=locationDict["expandHeight"], edit=True))
        child.addChild(self.CreateTreeItem(key="matchCount", value=locationDict["matchCount"], edit=True))

        # 如果是bloodlengthreg，需要加conditions节点，conditions节点中包含很多condition节点
        if taskType == "bloodlengthreg":
            childConditions = self.CreateTreeItem("conditions")
            child.addChild(childConditions)
            for condition in locationDict["Conditions"]:
                childConditions.addChild(self.CreateTreeItem("condition", condition, edit=True))

        # 导入template节点
        childTemplates = self.CreateTreeItem(key="templates", type=ITEM_TYPE_REFER_TEMPLATES)
        child.addChild(childTemplates)
        for template in locationDict["templates"]:
            self.LoadTemplate(template, childTemplates)
        return child

    '''
        添加场景节点，右键添加场景的槽函数
    '''
    def AddScene(self):
        sceneName = self.sceneNameDialog.popUp()
        if sceneName is None:
            self.logger.info('sceneName is empty')
            return

        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddScene failed, treeItem is None')
            return

        # 给groupID，name，tasks填值
        version = treeItem.text(0)
        scene = OrderedDict()
        scene["groupID"] = self.groupIDIndex
        scene["name"] = sceneName
        scene["tasks"] = list()
        # self.taskJsonFile[version]["alltask"].append(scene)

        # 创建scene节点，并添加为version节点的子节点
        child = self.CreateTreeItem(key='scene', value=sceneName, type=ITEM_TYPE_SCENE)
        treeItem.addChild(child)

        # 添加groupID和name节点
        child.addChild(self.CreateTreeItem(key='groupID', value=scene["groupID"]))
        child.addChild(self.CreateTreeItem(key='name', value=scene["name"]))

        # 创建task节点
        taskTreeItem = self.CreateTaskTree(self.GenerateTaskDict(TASK_TYPE_FIXOBJ))
        child.addChild(taskTreeItem)
        taskTreeItem.setExpanded(True)
        self.HiddenItem(treeItem)
        # self.writeTaskJsonFile()

    '''
        添加任务，右键添加任务的槽函数
    '''
    def AddTask(self):
        taskName = self.taskNameDialog.popUp()
        if taskName is None:
            self.logger.info('taskName is empty')
            return

        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddTask failed, treeItem is None')
            return

        # 默认添加的是fixobj的任务
        taskTreeItem = self.CreateTaskTree(self.GenerateTaskDict(TASK_TYPE_FIXOBJ), taskName)
        treeItem.addChild(taskTreeItem)
        taskTreeItem.setExpanded(True)
        self.HiddenItem(treeItem)

    '''
        添加element节点，右键添加元素的槽函数
    '''
    def AddElement(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddElement failed, treeItem is None')
            return

        # 获取当前task的type
        itemWidget = self.GetChildItemValue(treeItem, 0, "type", 1)
        taskType = itemWidget.currentText()

        element = OrderedDict()
        element["elementID"] = self.elementIDIndex
        self.elementIDIndex += 1

        # 根据task的type来生成对应的element
        self.LoadTaskFunc[taskType](element, treeItem)
        self.HiddenItem(treeItem)

    '''
        添加模板，右键添加模板的槽函数
    '''
    def AddTemplate(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error('AddTemplate failed, treeItem is None')
            return

        template = OrderedDict()
        template["templateID"] = self.templateIDIndex
        self.templateIDIndex += 1

        # 生成模板树
        self.LoadTemplate(template, treeItem)
        self.HiddenItem(treeItem)

    def CheckReferExist(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddReferTask failed, treeItem is None")
            return False

        if treeItem.text(2) != ITEM_TYPE_ELEMENT:
            return False

        for index in range(treeItem.childCount()):
            item = treeItem.child(index)
            if item.text(0) == "refer":
                self.logger.info("Refer is already exist, please check")
                dlg = CommonDialog(title="add wrong", text="refer item is already exist")
                dlg.popUp()
                return False

        return True

    '''
        添加refer，右键添加参考任务的槽函数
    '''
    def AddReferTask(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("AddReferTask failed, treeItem is None")
            return

        if treeItem.text(2) != ITEM_TYPE_ELEMENT:
            return

        if not self.CheckReferExist():
            return

        referDict = self.GenerateReferTaskDict(treeItem, TASK_TYPE_REFER_LOCATION, ALGORITHM_LOCATION_DETECT)

        referTaskTree = self.CreateLocationRefer(referDict)
        treeItem.addChild(referTaskTree)
        referTaskTree.setExpanded(True)
        self.HiddenItem(referTaskTree)

    def ShowDetailConf(self):
        treeItem = self.ui.treeWidget.currentItem()
        self.ShowDetailItem(treeItem)
        self.HiddenItem(treeItem)
        # self.HiddenReferItem(treeItem)

    def HiddenReferConf(self):
        treeItem = self.ui.treeWidget.currentItem()
        self.HiddenReferItem(treeItem)
    '''
        创建task树
        输入参数：taskDict表示任务的字典数据
        输入参数：taskName表示任务名字
        返回值：QTreeItem表示任务树结构的根节点
    '''
    def CreateTaskTree(self, taskDict, taskName=None):
        if taskDict is None:
            self.logger.error("CreateTaskTree failed, taskDict is None")
            return

        # 获取taskID
        taskID = taskDict["taskID"]
        if taskID >= self.taskIDIndex:
            self.taskIDIndex = taskID + 1              # 加1的原因是防止导入已有的手动配置的配置文件，ID出错的情况
        taskType = taskDict["type"]
        if "taskName" not in taskDict:
            taskDict["taskName"] = taskName
        taskName = taskDict["taskName"]
        description = taskDict["description"]
        skipFrame = taskDict["skipFrame"]

        # 创建树结构的根节点，并创建taskID，taskName，type等子节点
        childTask = self.CreateTreeItem(key='task', value=taskName, type=ITEM_TYPE_TASK, edit=True)
        childTask.addChild(self.CreateTreeItem(key='taskID', value=taskID, edit=True))
        childTask.addChild(self.CreateTreeItem(key='taskName', value=taskName, edit=True))

        childTaskType = self.CreateTreeItem(key='type')
        childTask.addChild(childTaskType)
        qCombox = QComboBox()
        qCombox.addItems([
            TASK_TYPE_FIXOBJ,
            TASK_TYPE_PIX,
            TASK_TYPE_STUCK,
            TASK_TYPE_DEFORM,
            TASK_TYPE_NUMBER,
            TASK_TYPE_FIXBLOOD,
            TASK_TYPE_DEFORMBLOOD
        ])
        qCombox.setCurrentText(taskType)
        qCombox.currentTextChanged.connect(self.TaskComboxTextChange)
        self.ui.treeWidget.setItemWidget(childTaskType, 1, qCombox)

        childTask.addChild(self.CreateTreeItem(key='description', value=description, edit=True))
        childTask.addChild(self.CreateTreeItem(key='skipFrame', value=skipFrame, edit=True))

        # 根据type的不同创建不同的element
        for element in taskDict["elements"]:
            self.LoadTaskFunc[taskType](element, childTask)

        return childTask

    '''
        refer结构中，algorithm节点的combox下拉选项发生改变时触发的槽函数（infer和detect）
        触发后会根据选择的算法来修改树结构
    '''
    def ReferAlgorithmComboxChange(self, text):
        if text is None:
            self.logger.error("ReferAlgorithmComboxChange failed, text is {}".format(text))
            return

        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("ReferAlgorithmComboxChange failed, treeItem is None")
            return

        referItem = treeItem.parent()
        if referItem is None:
            self.logger.error("ReferAlgorithmComboxChange failed, referItem is None")
            return

        self.mainWindow.canvas.resetState()
        # 如果选择的是detect
        if text == ALGORITHM_LOCATION_DETECT:
            referItem.setText(3, "")
            for itemIndex in range(referItem.childCount()):
                child = referItem.child(itemIndex)
                # 命名更改：　inferLocations--->inferSubROIs
                if child.text(0) in ["inferROI", "inferLocations", "inferSubROIs"]:
                    referItem.takeChild(itemIndex)
                    break

            for itemIndex in range(referItem.childCount()):
                child = referItem.child(itemIndex)
                # 命名更改：　inferLocations--->inferSubROIs
                if child.text(0) in ["inferROI", "inferLocations", "inferSubROIs" ]:
                    referItem.takeChild(itemIndex)
                    break
        # 如果选择的是infer
        elif text == ALGORITHM_LOCATION_INFER:
            referItem.setText(3, "")
            for itemIndex in range(referItem.childCount()):
                child = referItem.child(itemIndex)
                # 命名修改, 'location'--->'templateLocation',找到此项，并再后面添加'inferROI', 'inferSubROIs'
                if child.text(0) in["location", "templateLocation"]:
                    childInferROI = self.CreateTreeItem(key='inferROI')
                    self.LoadRect(OrderedDict(), childInferROI)
                    referItem.insertChild(itemIndex + 1, childInferROI)
                    itemIndex += 1

                    # 命名修改，inferLocations--->inferSubROIs
                    # childInferLocations = self.CreateTreeItem(key='inferLocations')
                    childInferLocations = self.CreateTreeItem(key='inferSubROIs')
                    referItem.insertChild(itemIndex + 1, childInferLocations)
                    # 命名修改，inferLocation--->inferSubROI
                    #childLocation = self.CreateTreeItem(key='inferLocation')
                    childLocation = self.CreateTreeItem(key='inferSubROI')
                    self.LoadRect(OrderedDict(), childLocation)
                    childInferLocations.addChild(childLocation)

        self.HiddenReferItem(referItem)

    '''
        refer任务中类型的下拉选项框改变时触发的槽函数
        location或bloodlengthreg
    '''
    def ReferTaskComboxChange(self, text):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("ReferTaskComboxChange failed, treeItem is None")
            return

        referItem = treeItem.parent()
        if referItem is None:
            self.logger.error("ReferTaskComboxChange failed, referItem is None")
            return

        elementItem = referItem.parent()
        if referItem is None:
            self.logger.error("ReferTaskComboxChange failed, elementItem is None")
            return

        self.mainWindow.canvas.resetState()
        for itemIndex in range(elementItem.childCount()):
            taskItem = elementItem.child(itemIndex)
            if taskItem.text(0) == "refer":
                elementItem.takeChild(itemIndex)
                referDict = OrderedDict()
                # 生成location的字典
                if text == TASK_TYPE_REFER_LOCATION:
                    referDict = self.GenerateReferTaskDict(elementItem, text, ALGORITHM_LOCATION_DETECT)
                # 生成bloodlengthreg的字典
                elif text == TASK_TYPE_REFER_BLOODLENGTHREG:
                    referDict = self.GenerateReferTaskDict(elementItem, text, ALGORITHM_BLOODLENGTHREG_TAPLATEMATCH)

                # 创建refer任务树结构
                referTaskTreeItem = self.CreateLocationRefer(referDict)
                elementItem.insertChild(itemIndex, referTaskTreeItem)
                referTaskTreeItem.setExpanded(True)
                self.HiddenReferItem(referTaskTreeItem)
                self.HiddenItem(referTaskTreeItem)
                self.mainWindow.canvas.resetState()
                break

    '''
        task任务的类型下拉选项框发生变化时，触发的槽函数
        生成新的task树
    '''
    def TaskComboxTextChange(self, text):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.logger.error("TaskComboxTextChange failed, treeItem is None")
            return

        taskTypeTree = treeItem.parent()
        if taskTypeTree is None:
            self.logger.error("TaskComboxTextChange failed, taskTypeTree is None")
            return

        sceneTree = taskTypeTree.parent()
        if sceneTree is None:
            self.logger.error("TaskComboxTextChange failed, sceneTree is None")
            return

        taskID = self.GetChildItemValue(taskTypeTree, 0, "taskID", 1)

        for itemIndex in range(sceneTree.childCount()):
            taskItem = sceneTree.child(itemIndex)
            itemTaskID = self.GetChildItemValue(taskItem, 0, "taskID", 1)
            if itemTaskID == taskID:
                taskName = taskItem.text(1)
                sceneTree.takeChild(itemIndex)
                taskTreeItem = self.CreateTaskTree(self.GenerateTaskDict(text), taskName)
                sceneTree.insertChild(itemIndex, taskTreeItem)
                taskTreeItem.setExpanded(True)
                taskTypeTree.setExpanded(True)
                self.HiddenItem(sceneTree)
                self.mainWindow.canvas.resetState()
                break

    '''
        生成默认的refer字典
        输入参数：treeItem表示element节点
        输入参数：taskType表示location或bloodlengthreg
        输入参数：algorithm表示detect或infer
        返回值：refer字典
    '''
    def GenerateReferTaskDict(self, treeItem, taskType, algorithm):
        if treeItem is None:
            self.logger.error("GenerateReferTaskDict failed, treeItem is None")
            return

        taskID = int(self.GetChildItemValue(treeItem.parent(), 0, "taskID", 1))
        referTaskDict = OrderedDict()
        referTaskDict["taskID"] = self.GetReferTaskID(treeItem, taskID)
        if referTaskDict["taskID"] == -1:
            self.logger.error("get refer taskID failed, taskID is {}".format(taskID))
            return
        referTaskDict["type"] = taskType
        referTaskDict["description"] = ""
        referTaskDict["skipFrame"] = DEFAULT_SKIPFRAME
        referTaskDict["algorithm"] = algorithm
        referTaskDict["location"] = self.GenerateRect()
        if taskType == "location" and algorithm == "Infer":
            referTaskDict["inferROI"] = self.GenerateRect()

            referTaskDict["inferLocations"] = list()
            referTaskDict["inferLocations"].append(self.GenerateRect())

        referTaskDict["minScale"] = DEFAULT_REFER_MINSCALE
        referTaskDict["maxScale"] = DEFAULT_REFER_MAXSCALE
        referTaskDict["scaleLevel"] = DEFAULT_REFER_SCALELEVEL
        referTaskDict["expandWidth"] = DEFAULT_EXPANDWIDTH
        referTaskDict["expandHeight"] = DEFAULT_EXPANDHEIGHT
        referTaskDict["matchCount"] = DEFAULT_MATCHCOUNT

        if taskType == "bloodlengthreg":
            referTaskDict["Conditions"] = list()

        referTaskDict["templates"] = list()
        referTaskDict["templates"].append(self.GenerateTemplate())

        return referTaskDict

    '''
        获取referTaskID，规则如下：
        taskID为1，referID为10001
    '''
    def GetReferTaskID(self, treeItem, taskID):
        if treeItem is None or taskID < 0:
            self.logger.error('wrong param: treeItem: {}, taskID: {}'.format(treeItem, taskID))
            return -1

        preElementItem = treeItem.parent()
        elementIndex = preElementItem.indexOfChild(treeItem)
        taskIDPrefix = taskID * 10000
        taskReferID = 1
        for itemIndex in range(preElementItem.childCount()):
            item = preElementItem.child(itemIndex)
            if item.text(0) == "element":
                if itemIndex == elementIndex:
                    break

                for elementItemIndex in range(item.childCount()):
                    elementItem = item.child(elementItemIndex)
                    if elementItem.text(0) == "refer":
                        taskReferID += 1

        return taskIDPrefix + taskReferID

    '''
        生成task任务的dict
        输入参数：type为task类型，fixobj，pixel等等
        返回值：task任务的字典
    '''
    def GenerateTaskDict(self, type):
        if type not in [TASK_TYPE_FIXOBJ, TASK_TYPE_PIX, TASK_TYPE_STUCK, TASK_TYPE_DEFORM, TASK_TYPE_NUMBER,
                        TASK_TYPE_FIXBLOOD, TASK_TYPE_DEFORMBLOOD]:
            self.logger.error("GenerateTaskDict failed, type is {}".format(type))
            return

        taskDict = OrderedDict()
        taskDict["taskID"] = self.taskIDIndex
        self.taskIDIndex += 1
        taskDict["type"] = type
        taskDict["description"] = str()
        taskDict["skipFrame"] = DEFAULT_SKIPFRAME
        taskDict["elements"] = list()
        if type == TASK_TYPE_FIXOBJ:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["algorithm"] = DEFAULT_FIXOBJ_ALGORITHM
            element["minScale"] = DEFAULT_MINSCALE
            element["maxScale"] = DEFAULT_MAXSCALE
            element["scaleLevel"] = DEFAULT_SCALELEVEL
            element["templates"] = list()
            element["templates"].append(self.GenerateTemplate())
            taskDict["elements"].append(element)
        elif type == TASK_TYPE_PIX:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["condition"] = str()
            element["filterSize"] = DEFAULT_FILTERSIZE
            element["maxPointNum"] = DEFAULT_MAXPOINTNUM
            taskDict["elements"].append(element)
        elif type == TASK_TYPE_STUCK:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["intervalTime"] = DEFAULT_INTERVALTIME
            element["threshold"] = DEFAULT_STUCK_THRESHOLD
            taskDict["elements"].append(element)
        elif type == TASK_TYPE_DEFORM:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["cfgPath"] = str()
            element["weightPath"] = str()
            element["namePath"] = str()
            element["maskPath"] = str()
            element["threshold"] = DEFAULT_DEFORM_THRESHOLD
            taskDict["elements"].append(element)
        elif type == TASK_TYPE_NUMBER:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["algorithm"] = DEFAULT_FIXOBJ_ALGORITHM
            element["minScale"] = DEFAULT_MINSCALE
            element["maxScale"] = DEFAULT_MAXSCALE
            element["scaleLevel"] = DEFAULT_SCALELEVEL
            element["templates"] = list()
            element["templates"].append(self.GenerateTemplate())
            element["templates"][0]["classID"] = 0
            element["templates"][0]["name"] = "0"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][1]["classID"] = 1
            element["templates"][1]["name"] = "1"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][2]["classID"] = 2
            element["templates"][2]["name"] = "2"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][3]["classID"] = 3
            element["templates"][3]["name"] = "3"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][4]["classID"] = 4
            element["templates"][4]["name"] = "4"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][5]["classID"] = 5
            element["templates"][5]["name"] = "5"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][6]["classID"] = 6
            element["templates"][6]["name"] = "6"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][7]["classID"] = 7
            element["templates"][7]["name"] = "7"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][8]["classID"] = 8
            element["templates"][8]["name"] = "8"
            element["templates"].append(self.GenerateTemplate())
            element["templates"][9]["classID"] = 9
            element["templates"][9]["name"] = "9"
            taskDict["elements"].append(element)

        elif type == TASK_TYPE_FIXBLOOD:
            element = OrderedDict()
            element["condition"] = str()
            element["ROI"] = self.GenerateRect()
            element["bloodLength"] = DEFAULT_BLOODLENGTH
            element["filterSize"] = DEFAULT_FILTERSIZE
            element["maxPointNum"] = DEFAULT_MAXPOINTNUM
            taskDict["elements"].append(element)

        elif type == TASK_TYPE_DEFORMBLOOD:
            element = OrderedDict()
            element["ROI"] = self.GenerateRect()
            element["cfgPath"] = str()
            element["weightPath"] = str()
            element["namePath"] = str()
            element["maskPath"] = str()
            element["threshold"] = DEFAULT_DEFORM_THRESHOLD
            element["condition"] = str()
            element["bloodLength"] = DEFAULT_BLOODLENGTH
            element["filterSize"] = DEFAULT_FILTERSIZE
            element["maxPointNum"] = DEFAULT_MAXPOINTNUM
            taskDict["elements"].append(element)

        return taskDict

    '''
        检查taskID是否合法，是否重复
    '''
    def CheckTaskID(self, treeItem, taskID):
        if treeItem is None:
            self.logger.error("CheckTaskID failed, treeItem is None")
            return

        sceneItem = treeItem.parent().parent()
        if sceneItem is None:
            self.logger.error("CheckTaskID failed, sceneItem is None")
            return

        for itemIndex in range(sceneItem.childCount()):
            taskItem = sceneItem.child(itemIndex)
            if taskItem == treeItem.parent():
                continue
            if taskItem.text(0) == "task":
                treeTaskID = int(taskItem.child(0).text(1))
                if treeTaskID == taskID:
                    return False

        return True

    '''
        生成模板字典
    '''
    def GenerateTemplate(self):
        template = OrderedDict()
        template["path"] = str()
        template["name"] = str()
        template["location"] = self.GenerateRect()
        template["threshold"] = DEFAULT_TEMPLATE_THRESHOLD
        template["classID"] = 0
        return template

    def HiddenReferItem(self, treeItem):
        # print("**********begin hidden refer Item**************")
        iterator = QTreeWidgetItemIterator(treeItem)
        while iterator.value() is not None:
            # print("##############text 0 {}###############".format(iterator.value().text(0)))
            if iterator.value().text(0) in ["description", "skipFrame", "inferSubROIs", "minScale", "maxScale",
                                            "scaleLevel", "expandWidth", "expandHeight", 'matchCount']:

                # print("hidden item {}".format(iterator.value().text(0)))
                iterator.value().setHidden(True)

            if iterator.value().text(0) in ['templates']:
                templatesItem = iterator.value()
                for index in range(templatesItem.childCount()):
                    templateItem = templatesItem.child(index)
                    for index2 in range(templateItem.childCount()):
                        child = templateItem.child(index2)
                        if child.text(0) in ['name', 'location', 'classID']:
                            # print("hidden item {}".format(child.text(0)))
                            child.setHidden(True)

            iterator.__iadd__(1)

    def HiddenReferTemplate(self, treeItem):
        iterator = QTreeWidgetItemIterator(treeItem)
        while iterator.value() is not None:
            if iterator.value().text(0) in ['name', 'location', 'classID']:
                iterator.value().setHidden(True)
            iterator.__iadd__(1)

    def ShowDetailItem(self, treeItem):
        iterator = QTreeWidgetItemIterator(treeItem)
        while iterator.value() is not None:
            iterator.value().setHidden(False)
            iterator.__iadd__(1)

