# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import json
import logging
import logging.config
import traceback
import importlib
import configparser
import subprocess
import platform
import signal

import time
from SDKTool import *

from libs.Module.MapGraphPath import *
from libs.Module.ActionSample import *
from libs.Module.UIConfig import *
from libs.Module.TaskConfig import *
from libs.Module.MapPath import *
from define import *
from libs.Graph import UIGraph, UIGRAPH
from libs.AIPluginDialog import AIPluginDialog
from libs.Module.UIExplore.UIExplore import UIExplore
from libs.Module.UIExplore.canvasUtils import GetLabelImageItem
from libs.utils import *
from libs.CommonDialog import *

platform = sys.platform

# mode
MODE_NONE = 0
MODE_UIEXPLORE = 1


class SDKMainWindow(QMainWindow):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))
    def __init__(self, ui=None):
        super(SDKMainWindow, self).__init__()
        self.ui = ui
        self.filePath = None
        self.canvas = None                              # 画布
        self.image = QImage()
        self.projectName = str()                        # 当前项目名
        self.taskJsonFile = OrderedDict()               # task配置文件内容
        self.UIJsonFile = OrderedDict()                 # UI配置文件内容
        self.referJsonFile = OrderedDict()              # refer配置文件内容
        self.actionSampleJsonFile = OrderedDict()       # 动作配置文件内容（用于模仿学习）
        self.mapPathJsonDict = OrderedDict()            # 地图路径配置文件内容
        self.mapGraphPathJsonDict = OrderedDict()       # 图结构的地图路径配置文件内容
        self.projectVersion = list()                    # 项目版本list，有多个
        self.preTaskID = 0                              # 之前的taskID，如果配置taskID重复或不合法，则恢复之前的taskID
        self.preItemValue = str()                       # 之前的item的值，同上，用于恢复
        self.DebugInstance = None                       # 调试的实例

        # 树结构节点的icon
        self.treeIcon = QtGui.QIcon()
        self.treeIcon.addPixmap(QtGui.QPixmap(":/menu/treeIcon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.labelModel = False       # 当前是否为UI标注
        self.labelScale = 1.
        self.__logger = None
        self.projectDict = None
        self.actionSamplePro = None
        # self.uiExploreDlg = None
        self.__uiExplore = None
        self.labelImageList = []
        self.labelImageIndex = -1
        self.mode = MODE_NONE

    def Init(self):
        self.__logger = logging.getLogger('sdktool')

        # connect槽函数
        self.ui.treeWidget.customContextMenuRequested.connect(self.showRightMenu)
        self.ui.treeWidget.itemDoubleClicked.connect(self.ItemDoubleClick)
        self.ui.treeWidget.currentItemChanged.connect(self.CurrentItemChange)
        self.ui.treeWidget.itemChanged.connect(self.ItemValueChange)
        self.ui.actionSave.triggered.connect(self.SaveFile)
        self.ui.actionTest.triggered.connect(self.TestGameReg)
        self.ui.actionImport.triggered.connect(self.ImportLabelImage)
        self.ui.actionUIGraph.triggered.connect(self.ImportUIGraph)

        self.ui.pushButton_prev.clicked.connect(lambda: self.ChangeLabelImage(False))
        self.ui.pushButton_next.clicked.connect(lambda: self.ChangeLabelImage(True))
        self.ui.fileListWidget.currentItemChanged.connect(self.FileListItemChange)
        self.zoomWidget = ZoomWidget()
        self.zoomWidget.valueChanged.connect(self.paintCanvas)
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow
        }
        # menu
        self.ui.actionSampleStart.triggered.connect(self.RunActionSample)
        self.ui.actionSampleExit.triggered.connect(self.ExitActionSample)

        self.ui.generatePluginAction.triggered.connect(self.GeneratePlugin)
        self.ui.UIExploreAction.triggered.connect(self.UIExplore)

        # 初始化弹框
        self.versionDialog = customDialog(text = "输入版本号", parent=self)
        self.projectNameDialog = customDialog(text = "输入工程名", parent=self)
        self.taskIDRepeatDialog = confirmDialog(text="taskID重复", parent=self)
        self.projectNameExistDialog = confirmDialog(text="工程已存在", parent=self)
        self.saveDialog = confirmDialog(text="保存成功", parent=self)
        self.numberDialog = confirmDialog(text="请填入数字", parent=self)
        self.jsonWidget = fileDialog()

        # 实例化每个功能模块
        self.graphPath = CMapGraphPath(MainWindow, self.ui)
        self.actionSample = CActionSample(MainWindow, self.ui)
        self.taskConfig = CTaskConfig(MainWindow, self.ui)
        self.uiConfig = CUIConfig(MainWindow, self.ui)
        self.mapPath = CMapPath(MainWindow, self.ui)

        self.canvas.setUIWorker(self)

        # 读取配置文件内容，决定是否开启调试功能
        self.config = configparser.ConfigParser()
        self.config.read(CFGPATH)
        self.debugFlag = self.config.get("debug", "flag")

        self.ui.actionTest.setEnabled(False)
        if self.debugFlag == 'True':
            # 如果开启调试功能，则动态导入调试模块
            debugModule = importlib.import_module('libs.Debug.DebugFactory')
            self.DebugFactory = debugModule.DebugFactory()
            self.DebugFactory.initialize(self.canvas, self.ui)

            # 在工厂类获取实例时会根据配置文件的内容实例化对应的调试实例（GameReg调试类的实例或UIRecognize调试类的实例）
            self.DebugInstance = self.DebugFactory.get_product_instance()
            self.ui.actionTest.setEnabled(True)

        # 以下均为给action添加槽函数
        self.rightMenu = QMenu(self.ui.treeWidget)
        self.actionNewProject = QAction(MainWindow)
        self.actionNewProject.setText("新建项目")
        self.actionNewProject.triggered.connect(lambda: self.LoadImgDir("v1.0"))

        self.actionLoadProject = QAction(MainWindow)
        self.actionLoadProject.setText("导入项目")
        self.actionLoadProject.triggered.connect(self.ImportProject)

        self.actionAddVersion = QAction(MainWindow)
        self.actionAddVersion.setText("添加版本")
        self.actionAddVersion.triggered.connect(self.AddVersion)

        self.actionDelVersion = QAction(MainWindow)
        self.actionDelVersion.setText("删除")
        self.actionDelVersion.triggered.connect(self.DeletVersion)

        self.actionDelItem = QAction(MainWindow)
        self.actionDelItem.setText("删除")
        self.actionDelItem.triggered.connect(self.DelItem)

        self.actionChangeFilePath = QAction(MainWindow)
        self.actionChangeFilePath.setText("修改图像")
        self.actionChangeFilePath.triggered.connect(self.ChangeFilePath)

        self.actionImportImage = QAction(MainWindow)
        self.actionImportImage.setText("导入文件")
        self.actionImportImage.triggered.connect(self.ImportImageFile)

        self.__logger.info("init finished")

        return True

    def Finish(self):
        self.ExitActionSample()
        if self.DebugInstance is not None:
            self.DebugInstance.finish()

        if self.__uiExplore is not None:
            self.__uiExplore.Finish()

    def RunActionSample(self):
        currentPath = os.getcwd()
        os.chdir("bin/ActionSampler/")
        args = [
            'python',
            'main.py',
        ]
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                self.actionSamplePro = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.actionSamplePro = subprocess.Popen(args)
        else:
            self.actionSamplePro = subprocess.Popen("python main.py", shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)

        if self.actionSamplePro is None:
            LOG.error("open action sample failed")
            return
        else:
            self.__logger.info('Run ActionSample Create PID: {} SubProcess'.format(self.actionSamplePro.pid))

    def ExitActionSample(self):
        if self.actionSamplePro is not None:
            if platform == 'win32':
                if hasattr(os.sys, 'winver'):
                    # os.kill(self.actionSamplePro.pid, signal.SIGINT)
                    os.kill(self.actionSamplePro.pid, signal.CTRL_BREAK_EVENT)
                else:
                    self.actionSamplePro.send_signal(signal.SIGTERM)
            else:
                os.killpg(self.actionSamplePro.pid, signal.SIGINT)

            self.__logger.info("Exit Action Sample")

    def GeneratePlugin(self):
        dialog = AIPluginDialog()
        dialog.popUp()
        gameName = dialog.getGameName()
        template = dialog.getTemplateName()
        self.__logger.info("begin to generate game:{} plugin code".format(gameName, template))
        if None in [gameName, template] or '' in [gameName, template]:
            self.__logger.error("game name:{} or template:{} is invalid".format(gameName, template))
            return

        currentPath = os.getcwd()
        os.chdir("bin/Generator/")
        args = [
            'python',
            'Generator.py',
            gameName,
            template
        ]
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                pro = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                pro = subprocess.Popen(args)
        else:
            pro = subprocess.Popen("python Generator.py {} {}".format(gameName, template), shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)
        if pro is None:
            self.__logger.error("generate {} plugin code failed".format(gameName))
            return
        else:
            self.__logger.info("finish generate {} plugin code".format(gameName))

    def UIExplore(self):
        # self.uiExploreDlg = UIExploreDialog(canvas=self.canvas, ui=self.ui)
        # self.uiExploreDlg.popUp()
        self.__uiExplore = UIExplore(canvas=self.canvas, ui=self.ui, zoomWidget=self.zoomWidget)
        self.mode = MODE_UIEXPLORE

    '''
       导入UI标签的图像和生存样本
    '''
    def ImportUIGraph(self):
        self.ClearTreeWidget()

        foldDiag = QFileDialog()
        foldDiag.setFileMode(QFileDialog.Directory)
        foldDiag.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        if not foldDiag.exec():
            return

        dirName = foldDiag.selectedFiles()[0]
        if dirName == "":
            self.__logger.error("open dir wrong")
            return

        fileList = os.listdir(dirName)
        UIImageList = [item for item in fileList if item.split('.')[1] in ['jpg']]
        UILabelList = [item for item in fileList if '.json' in item]

        imageLabelDict = dict()
        for item in UIImageList:
            key = item.split('.')[0]
            jsonfile = "{}.json".format(key)
            if jsonfile in UILabelList:
                imageLabelDict[key] = dict()
                imageLabelDict[key]["image"] = item
                imageLabelDict[key]["label"] = jsonfile

        uiGraph = UIGraph()
        # create graph
        for key, value in imageLabelDict.items():
            with open("{0}/{1}".format(dirName, value.get("label")), 'r') as UILabelFile:
                content = json.load(UILabelFile)
                labelList = content.get("labels")
                curImage = content.get("fileName")
                if not labelList:
                    self.__logger.error("{} label is none".format(UILabelFile))
                    continue

                for button in labelList:
                    nextUI = button.get("nextUI")
                    # labelName = button.get("label")
                    x = button.get("x")
                    y = button.get("y")
                    w = button.get("w")
                    h = button.get("h")
                    number = int(button.get("clickNum"))
                    uiGraph.AddNodeButton(curImage, (x, y, w, h), nextUI, number)
                    # if (nextUI is not '') and (labelName not in ['return']):
                    if nextUI is not '':
                        # uiGraph.AddEdge(value.get("image"), nextUI)
                        uiGraph.AddEdge(curImage, nextUI)

        self.__logger.info("edges num {} node num {}".format(len(uiGraph.Edges()), len(uiGraph.Nodes())))

        for node in uiGraph.Nodes():
            imgPath = dirName + '/' + str(node)
            uiGraph.AddNodeImage(node, imgPath)

        uiGraph.Process()
        uiGraph.SetTextEdit(self.ui.textEdit)

        self.canvas.addUIGraph(uiGraph)
        self.PaintImage("Resource/White.jpeg")
        self.canvas.currentModel.append(UIGRAPH)
        self.canvas.update()

    def ClearTreeWidget(self):
        self.ui.treeWidget.clear()
        if self.__uiExplore is not None:
            self.__uiExplore.Finish()
            self.__uiExplore = None
            self.mode = None

    '''
       导入UI标签的图像
    '''
    def ImportLabelImage(self):
        self.ClearTreeWidget()

        # 弹出导入文件夹的弹框
        FileDialog = QFileDialog()
        FileDialog.setFileMode(QFileDialog.Directory)
        FileDialog.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        if FileDialog.exec():
            # 获取到导入文件夹的名字
            directoryName = FileDialog.selectedFiles()[0]
            if directoryName == "":
                return
        else:
            return

        self.labelImageList = list()       # 所有图像的list
        self.labelImageIndex = 0           # 当前显示的图像在所有图像list中的索引

        # 读取所有图像，如果图像有对应的标签，则不显示它，将labelImageIndex设置为第一个没有标签的图像，从第一个没有标签的图像开始显示
        indexFlag = True
        for root, dirs, files in os.walk(directoryName):
            for file in files:
                if os.path.splitext(file)[1] in [".png", ".bmp", ".jpg", ".jpeg"]:
                    self.labelImageList.append(os.path.join(root, file))
                    self.ui.fileListWidget.addItem(os.path.join(root, file))
                    #if os.path.exists(root + '/' + file[: file.rfind('.')] + ".json") and indexFlag is True:
                    self.labelImageIndex += 1
                    #else:
                    indexFlag = False

        if self.labelImageIndex >= len(self.labelImageList):
            self.labelImageIndex = 0

        # 导入当前图像，也就是导入索引为self.labelImageIndex的图像
        self.canvas.resetState()
        self.canvas.addUIGraph(None)
        self.LoadLabelImage()

        self.canvas.setTreeWidget(ui.treeWidget)
        self.canvas.setUI(self.ui)

        self.labelModel = True

        self.ui.pushButton_prev.setEnabled(True)
        self.ui.pushButton_next.setEnabled(True)

    '''
        所有图像名都会显示在界面上一个filelist中，当点击不同的项，会触发该函数
    '''
    def FileListItemChange(self, current, previos):
        self.SaveLabelFile()                                              # 保存当前图像的标签
        self.labelImageIndex = self.ui.fileListWidget.currentRow()        # 更新labelImageIndex到新图像
        self.LoadLabelImage()                                             # 显示新图像

    '''
        按钮next和按钮prev的槽函数
    '''
    def ChangeLabelImage(self, nextFlag):
        if len(self.labelImageList) <= 0 and self.__uiExplore is not None:
            # self.labelImageList = labelImageList
            self.labelImageList = self.__uiExplore.GetUsrLabelImgList()
            self.labelImageIndex = max(0, self.__uiExplore.GetUsrLabelImgIndex())
            # if self.labelImageIndex < 0:
            #     self.labelImageIndex = 0
            if None in [self.labelImageList, self.labelImageIndex]:
                self.__logger.error("get image failed")
                return
            else:
                self.__logger.info("get image list success index is {}".format(self.labelImageIndex ))
        self.SaveLabelFile()                 # 保存当前图像的标签

        # 判断是点击prev还是next，对应labelImageIndex自加或自减
        if nextFlag is True:
            self.labelImageIndex += 1
            if self.labelImageIndex > len(self.labelImageList) - 1:
                self.labelImageIndex = len(self.labelImageList) - 1

        else:
            self.labelImageIndex -= 1
            if self.labelImageIndex < 0:
                self.labelImageIndex = 0

        self.LoadLabelImage()                  # 显示下一张图像
        # todo:show to show the plain text
        # self.ui.textEdit.setPlainText("当前/总数: {}/{}".format(self.labelImageIndex + 1,
        #                                                                len(self.labelImageList)))

    '''
        保存当前图像的标签，可参照具体标签的结构来读代码
    '''
    def SaveLabelFile(self):
        if self.mode == MODE_UIEXPLORE:
            time1 = time.time()
            labelItem = GetLabelImageItem(self.ui)
            fileNameItem = labelItem.child(0)
            fileName = fileNameItem.text(1)
            sceneItem = labelItem.child(1)
            sceneName = sceneItem.text(1)
        else:
            # 获取图像名
            fileNameItem = self.ui.treeWidget.topLevelItem(0)
            fileName = fileNameItem.text(1)

            # 获取场景名
            sceneItem = self.ui.treeWidget.topLevelItem(1)
            sceneName = sceneItem.text(1)

        # 构造标签的字典
        labelJsonDict = {}
        labelJsonDict["fileName"] = fileName
        labelJsonDict["scene"] = sceneName
        labelJsonDict["labels"] = list()

        # 对于每个框，都要存储对应的项
        for shape in self.canvas.shapes:
            labelDict = OrderedDict()

            if shape not in self.canvas.shapeItem.keys():
                continue

            labelNameItem = self.canvas.shapeItem[shape]
            labelText = labelNameItem.text(0)            # 获取框的标签类
            # labelName = shape.label[0]                   # 获取框的名称
            if len(shape.label) > 1:
                labelClickNum = shape.label[1]
            else:
                labelClickNum = 0

            # 填每个框对应的字段
            labelDict["label"] = labelText
            labelDict["name"] = ""
            labelDict["clickNum"] = labelClickNum

            # 填框的坐标
            labelDict["x"] = min(int(shape.points[0].x()), int(shape.points[1].x()))
            labelDict["y"] = min(int(shape.points[0].y()), int(shape.points[2].y()))
            labelDict["w"] = abs(int(shape.points[1].x() - shape.points[0].x()))
            labelDict["h"] = abs(int(shape.points[2].y() - shape.points[0].y()))

            labelJsonDict["labels"].append(labelDict)

        # 存储标签为json文件
        jsonFileName = fileNameItem.text(2)
        jsonFileName = jsonFileName[: jsonFileName.rfind('.')] + ".json"
        if len(labelJsonDict["labels"]) > 0:
            with open(jsonFileName, "w") as f:
                json.dump(labelJsonDict, f, indent=4, separators=(',', ':'))

        # todo:show to show the plain text
        # self.ui.textEdit.setPlainText("当前/总数: {}/{}".format(self.labelImageIndex + 1,
        #                                                                 len(self.labelImageList)))

    '''
        如果UI标签图像有对应的标签文件，则需要导入该标签文件
    '''
    def LoadLabelJson(self, labelImageName, fileNameItem, sceneItem, labelsItem):
        # 清除画布的一些数据
        self.canvas.shapeItem.clear()
        self.canvas.itemShape.clear()

        # 读取json文件
        labelJsonPath = labelImageName[:labelImageName.rfind('.')] + ".json"
        if os.path.exists(labelJsonPath) is False:
            return

        try:
            with open(labelJsonPath, 'r') as f:
                labelJsonDict = json.load(f)
        except Exception as e:
            self.__logger.error(e)
            self.__logger.error(traceback.format_exc())
            return

        sceneName = labelJsonDict["scene"]
        sceneItem.setText(1, sceneName)
        # self.ui.treeWidget.topLevelItem(1).setText(1, sceneName)

        # 对每个label，读取其内容并展示在画布上
        for labelShape in labelJsonDict["labels"]:
            labelText = labelShape["label"]
            # labelName = labelShape["name"]
            if "clickNum" in labelShape.keys():
                labelClickNum = int(labelShape["clickNum"])
            else:
                labelClickNum = 0
            self.canvas.labelDialog.addLabelHistory(labelText)
            treeLabelItem = None
            labelFlag = False
            # labelTreeItem = self.ui.treeWidget.topLevelItem(2)
            labelTreeItem = labelsItem
            for itemIndex in range(labelTreeItem.childCount()):
                treeItem = labelTreeItem.child(itemIndex)
                if treeItem.text(0) == labelText:
                    labelFlag = True
                    treeLabelItem = treeItem
                    break

            if labelFlag is False:
                treeLabelItem = self.CreateTreeItem(key=labelText)
                labelTreeItem.addChild(treeLabelItem)

            # 创建shape（方框），表示标签，展示在画布上
            shape = Shape(name=Shape.RECT)

            # shape.setLabel(labelName)
            shape.setLabel(labelText)

            if labelClickNum > 0:
                shape.setLabel(str(labelClickNum))
            width = labelShape['w']
            height = labelShape['h']
            if width < 0 or height < 0:
                self.__logger.error("{}file is wrong".format(labelJsonPath))

            point1 = QPoint(int(labelShape['x']), int(labelShape['y']))
            point2 = QPoint(int(labelShape['x']) + int(labelShape['w']),
                            int(labelShape['y']))
            point3 = QPoint(int(labelShape['x']) + int(labelShape['w']),
                            int(labelShape['y']) + int(labelShape['h']))
            point4 = QPoint(int(labelShape['x']),
                            int(labelShape['y']) + int(labelShape['h']))
            shape.addPoint(point1)
            shape.addPoint(point2)
            shape.addPoint(point3)
            shape.addPoint(point4)
            self.canvas.shapes.append(shape)
            self.canvas.shapeItem[shape] = treeLabelItem
            if labelText not in self.canvas.itemShape.keys():
                self.canvas.itemShape[labelText] = list()
            self.canvas.itemShape[labelText].append(shape)

    '''
        展示UI标签图像
    '''
    def LoadLabelImage(self):
        # for index in range(self.ui.treeWidget.topLevelItemCount()):
        #     self.ui.treeWidget.takeTopLevelItem(0)
        if self.labelImageIndex < 0:
            raise ("image index is less than 0")

        if len(self.labelImageList) < 1:
            raise ("imageList length is 0")

        if len(self.labelImageList) < self.labelImageIndex:
            raise ("length of labelImageList {} is larger than image　index {}".format(
                len(self.labelImageList),  self.labelImageIndex))

        fileName = self.labelImageList[self.labelImageIndex]
        time1 = time.time()
        self.PaintImage(fileName)

        if self.mode == MODE_UIEXPLORE:
            labelItem = GetLabelImageItem(self.ui)

            if labelItem is None:
                return

            for index in range(labelItem.childCount()):
                labelItem.takeChild(0)

            fileNameItem = self.CreateTreeItem(key='fileName', value=fileName)
            fileNameItem.setText(1, os.path.basename(fileName))
            fileNameItem.setText(2, fileName)
            labelItem.addChild(fileNameItem)

            sceneItem = self.CreateTreeItem(key='scene', edit=True)
            labelItem.addChild(sceneItem)

            labelsItem = self.CreateTreeItem(key='labels')
            labelItem.addChild(labelsItem)
            labelItem.setExpanded(True)
            time2 = time.time()
        else:
            for index in range(self.ui.treeWidget.topLevelItemCount()):
                self.ui.treeWidget.takeTopLevelItem(0)
            fileNameItem = self.CreateTreeItem(key='fileName', value=fileName)
            fileNameItem.setText(1, os.path.basename(fileName))
            fileNameItem.setText(2, fileName)
            self.ui.treeWidget.addTopLevelItem(fileNameItem)
            sceneItem = self.CreateTreeItem(key='scene', edit=True)
            self.ui.treeWidget.addTopLevelItem(sceneItem)
            labelsItem = self.CreateTreeItem(key='labels')
            self.ui.treeWidget.addTopLevelItem(labelsItem)

        self.LoadLabelJson(fileName, fileNameItem, sceneItem, labelsItem)
        self.canvas.setLabel()
        self.canvas.labelFlag = True
        self.canvas.update()

    '''
        调试按钮的槽函数
    '''
    def TestGameReg(self):
        # topLevelItem = self.ui.treeWidget.topLevelItem(0)
        # if topLevelItem is None:
        #     return

        # 检查AI_SDK_PATH环境变量的路径下是否有某些配置文件，如果没有，那么创建（但并不是所有配置文件都能创建）
        checkFlag = self.ui.actionTest.isChecked()
        if checkFlag is True:
            env_dist = os.environ
            sdkPath = env_dist.get('AI_SDK_PATH')
            if sdkPath is None:
                logging.error('there is no AI_SDK_PATH')
                return

            if os.path.exists(sdkPath + "/cfg") is False:
                os.mkdir(sdkPath + "/cfg")

            if os.path.exists(sdkPath + "/cfg/task") is False:
                os.mkdir(sdkPath + "/cfg/task")

            if os.path.exists(sdkPath + "/cfg/task/gameReg") is False:
                os.mkdir(sdkPath + "/cfg/task/gameReg")

            if os.path.exists(sdkPath + "/cfg/task/gameReg/gameReg_mgr1.json") is False:
                gameRegDict = {
                    "worker":
                        {
                            "count": 8
                        },
                    "multiResolution":
                        {
                            "flag": False
                        },
                    "maxResultQueueSize": 5
                }
                with open(sdkPath + "/cfg/task/gameReg/gameReg_mgr1.json", "w") as f:
                    json.dump(gameRegDict, f, indent=4, separators=(',', ':'))

            if os.path.exists(sdkPath + "/cfg/task/ui") is False:
                os.mkdir(sdkPath + "/cfg/task/ui")

            # 拷贝task.json,refer.json.UIConfig.json还有data路径下的图片到AI_SDK_PATH路径下
            shutil.copy(self.projectPath + "/v1.0/jsonFile/task.json", sdkPath + "/cfg/task/gameReg/task_SDKTool.json")
            shutil.copy(self.projectPath + "/v1.0/jsonFile/refer.json", sdkPath + "/cfg/task/gameReg/refer_SDKTool.json")
            shutil.copy(self.projectPath + "/v1.0/jsonFile/UIConfig.json", sdkPath + "/cfg/task/ui/UIConfig.json")
            if not os.path.exists(sdkPath + "/data"):
                os.makedirs(sdkPath + "/data")
                # shutil.rmtree(sdkPath + "/data")

            self.copyFile(self.projectPath + "/v1.0/data", sdkPath + "/data")

            # 开始调试
            self.DebugInstance.start_test()
        else:
            # 停止调试
            self.DebugInstance.stop_test()

    '''
        导入图片，右键image项，可导入单张图片
    '''
    def ImportImageFile(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.__logger.error("ImportImageFile failed, treeItem is None")
            
            return

        if treeItem.text(2) != ITEM_TYPE_IMAGE_FLODER:
            return

        version = ""
        floderPath = ""
        treeItemTmp = treeItem
        while True:
            if treeItemTmp.parent() is None:
                break

            if treeItemTmp.parent().text(0) == self.projectName:
                version = treeItemTmp.text(0)
                break

            floderPath = treeItemTmp.text(0) + "/" + floderPath
            treeItemTmp = treeItemTmp.parent()

        targetPath = self.projectPath + "/" + version + "/" + floderPath
        image, Type = QFileDialog.getOpenFileName(None, "导入图片", self.projectPath, "*.*")
        if image == "":
            self.__logger.info('image is empty in ImportImageFile')
            return

        _, fileName = os.path.split(image)
        try:
            shutil.copy(image, targetPath + fileName)
        except Exception:
            self.__logger.error("copy {}--->{} failed".format(image, targetPath + fileName))

        child = QTreeWidgetItem()
        child.setText(0, fileName)
        extension = os.path.splitext(fileName)[1]
        if extension in [".jpg", ".png", ".bmp", ".jpeg"]:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/menu/image.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            child.setIcon(0, icon)
        elif extension in ["", ".0", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9"]:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/menu/floder.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            child.setIcon(0, icon)
        elif extension in [".json"]:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/menu/json.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            child.setIcon(0, icon)
        elif extension in [".mp4", ".rmvb", ".avi"]:
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/menu/video.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            child.setIcon(0, icon)
        treeItem.addChild(child)

    '''
        获取element或template对应的图像路径,key名为targetImg
        图像路径存在名字为element或template的item的第四列中，因此会通过treeItem.text(3)来获取图像路径
        输入参数：treeItem，任意QTreeItem类型
        输出参数：str()表示图像路径，QTreeItem表示图像路径QTreeItem的父QTreeItem
    '''
    def GetImagePathFromItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetImagePathFromItem failed, treeItem is None")
            return

        rootTree = treeItem
        while True:
            if rootTree is None:
                return False, None

            if rootTree.text(2) in [ITEM_TYPE_TEMPLATE, ITEM_TYPE_UI_ELEMENT, ITEM_TYPE_ELEMENT, ITEM_TYPE_REFER_TASK,
                                    ITEM_TYPE_ACTIONSAMPLE_ELEMENT]:
                if rootTree.text(2) == ITEM_TYPE_ELEMENT and rootTree.text(3) == "":
                    childItem = self.GetChildItem(rootTree, "targetImg")
                    if childItem is not None:
                        if childItem.text(1) != "":
                            version = self.GetVersionItem(rootTree).text(0)
                            imagePath = self.projectPath + "/" + version + "/" + childItem.text(1)
                            return imagePath, rootTree
                return rootTree.text(3), rootTree
            rootTree = rootTree.parent()

    '''
         获取template的rect项（包含x,y,w,h）的QTreeItem，可能有多个
         输入参数：QTreeItem
         输出参数：QTreeItem的list
    '''
    def GetTemplateRectItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetTemplateRectItem failed, treeItem is None")
            
            return

        rectItemList = list()
        for itemIndex in range(treeItem.childCount()):
            childItem = treeItem.child(itemIndex)
            if childItem.text(0) == "location":
                rectItemList.append(childItem)

        return rectItemList

    '''
        获取referItem下的rect项（包含x,y,w,h）的QTreeItem，可能有多个
        输入参数：QTreeItem
        输出参数：QTreeItem的list
    '''
    def GetReferRectItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetReferRectItem failed, treeItem is None")
            
            return

        rectItemList = list()
        for itemIndex in range(treeItem.childCount()):
            childItem = treeItem.child(itemIndex)

            # 命名更改: location--->"templateLocation"
            if childItem.text(0) in ["location", "inferROI", "templateLocation"]:
                rectItemList.append(childItem)

            # 命名更改： "inferLocations"--->"inferSubROIs"
            elif childItem.text(0) in ["inferLocations", "inferSubROIs"]:
                if not childItem.isHidden():
                    for inferIndex in range(childItem.childCount()):
                        rectItemList.append(childItem.child(inferIndex))

        return rectItemList

    '''
        获取element下的rect项（包含x,y,w,h）的QTreeItem，可能有多个
        输入参数：QTreeItem
        输出参数：QTreeItem的list
    '''
    def GetElementRectItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetElementRectItem failed, treeItem is None")
            return

        rectItemList = list()
        for itemIndex in range(treeItem.childCount()):
            childItem = treeItem.child(itemIndex)
            if childItem.text(0) in ["ROI", "startRect", "endRect"]:
                rectItemList.append(childItem)

        return rectItemList

    '''
        获取QTreeItem下所有rect项（包含x,y,w,h），可能有多个
        输入参数：QTreeItem
        输出参数：QTreeItem的list
    '''
    def GetRectItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetRectItem failed, treeItem is None")
            return

        key = treeItem.text(0)
        if key in ["element", "target"]:
            return self.GetElementRectItem(treeItem)
        elif key == "template":
            return self.GetTemplateRectItem(treeItem)
        elif key == "refer":
            return self.GetReferRectItem(treeItem)

    '''
        获取当前version的QTreeItem（v1.0等等）
        输入参数：QTreeItem
        输出参数：QtreeItem，version的QTreeItem
    '''
    def GetVersionItem(self, treeItem):
        if treeItem is None:
            self.__logger.error("GetRectItem failed, treeItem is None")
            
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
        双击树结构中QtreeItem项的槽函数
    '''
    def ItemDoubleClick(self, treeItem, column):
        if self.mode == MODE_UIEXPLORE:
            self.__uiExplore.OnTreeClicked()
            return

        # 如果正在做UI标注，则直接返回
        if self.labelModel is True:
            return

        if treeItem is None:
            self.__logger.error("ItemDoubleClick failed, treeItem is None")
            return

        # 重置一下画布状态
        self.canvas.mouseMoveFlag = False
        self.canvas.resetState()
        self.canvas.currentModel.clear()

        # 获取当前的version名，类似v1.0
        version = self.GetVersionItem(treeItem).text(0)

        # 获取当前双击的item的type，通过树结构的第三列来区分item的type，对应的type可参考define.py里的定义
        type = treeItem.text(2)

        # 如果正在双击图结构路径的QTreeItem，则执行图结构路径模块的PaintGraphPath函数
        if type == ITEM_TYPE_MAPPATH_GRAPH:
            self.graphPath.PaintGraphPath()
            return

        # 如果是地图路径的path
        if type == ITEM_TYPE_MAPPATH_SINGLE_LINE:
            imageName = treeItem.parent().parent().text(0)                           # 获取图像名
            imagePath = self.projectPath + "/" + version + "/mapImage/" + imageName  # 获取图像路径

            self.PaintImage(imagePath)                                               # 画图

            # 画路径
            # 先定义shape，然后向shape中插入点
            shape = Shape(name=Shape.POLYGONLINE)
            self.canvas.setPolygonLineItem(treeItem)
            for itemIndex in range(treeItem.childCount()):
                childItem = treeItem.child(itemIndex)
                x = int(childItem.child(0).text(1))
                y = int(childItem.child(1).text(1))
                shape.addPoint(QPoint(x, y))

            self.canvas.AddShape(shape)
            self.canvas.setEditing(True)
            self.canvas.repaint()

            return

        taksID = None
        if type == ITEM_TYPE_UI_SCRIPT_TASK_ACTION:
            taskParent = treeItem.parent()
            taskID = self.uiConfig.GetChildItemValue(taskParent, 0, "taskid", 1)

        # 如果双击的QTreeItem，是json配置文件，则展示json配置文件
        keyName = treeItem.text(0)
        if os.path.splitext(keyName)[1] == ".json":
            while True:
                if treeItem.parent().text(0) == "jsonFile":
                    break

                keyName = treeItem.parent().text(0) + "/" + keyName
                treeItem = treeItem.parent()
            jsonPath = "./project/" + self.projectName + "/" + version + "/jsonFile/" + keyName
            self.jsonWidget.show_text(jsonPath)
            return

        # 如果双击的QTreeItem的key值表示路径时，则执行ChangeFilePath函数，修改图像路径
        if keyName in ["path", "cfgPath", "weightPath", "namePath", "maskPath", "imgPath", "scriptPath"]:
            self.ChangeFilePath()
            return

        # 如果双击的QTreeItem的key值为“taskID”时，说明要修改taskID，为了避免修改的值不合法，要记录之前的taskID值，以便恢复
        if keyName == "taskID":
            self.preTaskID = int(treeItem.text(1))
            return

        # 如果双击的QTreeItem项的value值应为数字，则记录修改前的value值
        if keyName in Number_Key:
            self.preItemValue = treeItem.text(1)

        # 获取双击的QTreeItem的子item中的图像路径，以及图像路径子item的父item
        ImagePath, parentItem = self.GetImagePathFromItem(treeItem)

        # 如果找不到图像路径，则重置画布状态
        if ImagePath is False:
            self.canvas.resetState()
        # 如果找得到图像路径
        else:
            self.canvas.resetState()
            # 获取该TreeItem下所有的rect项的item的集合
            rectItemList = self.GetRectItem(parentItem)

            # 如果path为空，说明还没有配置图像，需要配置
            if ImagePath == "":
                # 遍历所有rect项的Item，每一项都需要一个标注一个框
                for rectItem in rectItemList:
                    self.canvas.currentModel.append(Shape.RECT)
                    self.canvas.setRectTreeItem(rectItem)

                # 因为还没有配置图像，所以先弹出配置图像的窗口
                imgPath = "./project/" + self.projectName + "/" + version + "/data/"
                pathPart = "/project/" + self.projectName + "/" + version + "/data/"
                image, Type = QFileDialog.getOpenFileName(None, "选择标注图片", imgPath, "*.jpg *.png *.bmp *.jpeg")
                dirPath, imageName = os.path.split(image)
                fileIndex = image.find(pathPart)
                if fileIndex == -1:
                    filePathName = imgPath + imageName                       # filePathName为图像绝对路径
                    fileShowName = "/data/" + imageName                      # fileShowName为/data/XXX路径的图像，会被写入json文件中
                else:
                    filePathName = imgPath + image[fileIndex + len(pathPart):]
                    fileShowName = "/data/" + image[fileIndex + len(pathPart):]

                # 如果用户没有选择图像，则直接返回
                if image == "":
                    return

                parentItem.setText(3, filePathName)                          # 将图像的绝对路径写到QTreeItem的第三列中（第三列和第四列是隐藏的）

                # 如果类型为template
                if parentItem.text(2) == ITEM_TYPE_TEMPLATE:
                    parentItem.child(2).setText(1, fileShowName)
                # 如果类型为element
                elif parentItem.text(2) == ITEM_TYPE_ELEMENT:
                    if parentItem.child(0).text(0) == "targetImg":
                        parentItem.child(0).setText(1, fileShowName)
                # 如果是UI中的Item
                if parentItem.parent().parent().text(0) in ["UI"]:
                    # 获取UI中的动作Item，actionItem
                    actionItem = None
                    for itemIndex in range(parentItem.childCount()):
                        item = parentItem.child(itemIndex)
                        if item.text(0) == "imgPath":
                            item.setText(1, fileShowName)
                        elif item.text(0) in ["action", "dragPoint"]:
                            actionItem = item
                        elif item.text(0) in ["tasks"]:
                            item.setText(3, fileShowName)
                            for taskIndex in range(item.childCount()):
                                task = item.child(taskIndex)
                                task.setText(3, fileShowName)
                            parentItem.setText(3, fileShowName)

                    if treeItem.text(2) in [ITEM_TYPE_UI_SCRIPT_TASK_ACTION]:
                        actionItem = treeItem

                    if actionItem is not None:
                        # 如果动作item的子item有四个，说明是滑动动作，则应该画线
                        if actionItem.childCount() == len(Drag_Key):
                            self.canvas.currentModel.append(Shape.LINE)
                            self.canvas.setLineTreeItem(actionItem)
                        # 如果动作item的子item是两个，说明时点击动作，则应该画点
                        elif actionItem.childCount() in[len(Click_Key), len(Drag_Check_Key)]:
                            self.canvas.currentModel.append(Shape.POINT)
                            self.canvas.setPointTreeItem(actionItem)

                if not os.path.exists(filePathName):
                    shutil.copy(image, filePathName)

                self.PaintImage(filePathName)
                self.canvas.setEditing(False)
            # 如果path不为空，说明已配置过了，那就需要将其配置的内容展示出来
            else:
                try:
                    shapes = []
                    self.PaintImage(ImagePath)                       # 画出图像
                    # 对于所有的rectItem都应该画对应的框
                    for rectItem in rectItemList:
                        x = int(rectItem.child(0).text(1))
                        y = int(rectItem.child(1).text(1))
                        w = int(rectItem.child(2).text(1))
                        h = int(rectItem.child(3).text(1))

                        # 如果x,y,w,h有大于零的，说明画过框，则只需要创建对应框的shape就行
                        if x > 0 or y > 0 or w > 0 or h > 0:
                            self.canvas.setEditing()
                            shape = self.CreateShape([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
                            shapes.append(shape)
                            self.canvas.shapeTree[shape] = rectItem
                        else:
                            # 如果x,y,w,h都为零，说明还没有画过，因此需要画框
                            self.canvas.currentModel.append(Shape.RECT)
                            self.canvas.setRectTreeItem(rectItem)
                            # activate canvas for editing
                            self.canvas.setEditing(False)

                    # 如果是UI中的item
                    if parentItem.parent().parent().text(0) in["UI", "uiStates"]:
                        # 获取UI中的动作Item，actionItem
                        actionItem = None
                        for itemIndex in range(parentItem.childCount()):
                            item = parentItem.child(itemIndex)
                            if item.text(0) in ["action", "dragPoint"]:
                                actionItem = item
                                break

                            elif item.text(0) in ["tasks"]:
                                item.setText(3, ImagePath)
                                for taskIndex in range(item.childCount()):
                                    task = item.child(taskIndex)
                                    task.setText(3, ImagePath)
                                parentItem.setText(3, ImagePath)

                        if treeItem.text(2) in [ITEM_TYPE_UI_SCRIPT_TASK_ACTION]:
                            actionItem = treeItem
                            # imgPath = "./project/" + self.projectName + "/" + version + ImagePath
                            self.PaintImage(ImagePath)
                            self.canvas.setEditing(False)

                        if actionItem is not None:
                            # 如果动作item的子item有四个，说明是滑动动作，创建shape，将item中的线画到画布上
                            if actionItem.childCount() == len(Drag_Key):
                                x1 = int(actionItem.child(0).text(1))
                                y1 = int(actionItem.child(1).text(1))
                                x2 = int(actionItem.child(7).text(1))
                                y2 = int(actionItem.child(8).text(1))

                                self.canvas.setLineTreeItem(actionItem)
                                if x1 > 0 or y1 > 0 or x2 > 0 or y2 > 0:
                                    self.canvas.setEditing()
                                    shape = self.CreateShape([(x1, y1), (x2, y2)])
                                    shapes.append(shape)
                                    self.canvas.shapeTree[shape] = actionItem
                                else:
                                    self.canvas.setEditing(False)
                                    self.canvas.currentModel.append(Shape.LINE)
                                    self.canvas.setLineTreeItem(actionItem)
                            # 如果动作item的子item有两个，说明是点击动作，创建shape，将item中的点画到画布上
                            elif actionItem.childCount() in[len(Click_Key), len(Drag_Check_Key)]:
                                x = int(actionItem.child(0).text(1))
                                y = int(actionItem.child(1).text(1))

                                self.canvas.setPointTreeItem(actionItem)
                                if x > 0 or y > 0:
                                    self.canvas.setEditing()
                                    shape = self.CreateShape([(x, y)])
                                    shapes.append(shape)
                                    self.canvas.shapeTree[shape] = actionItem
                                else:
                                    self.canvas.setEditing(False)
                                    self.canvas.currentModel.append(Shape.POINT)
                                    self.canvas.setPointTreeItem(actionItem)

                    self.canvas.loadShapes(shapes)
                except Exception as err:
                    self.__logger.error("exception: {}".format(err))

        if keyName in ["ROI", "location", "element", "template", "refer"]:
            treeItem.setExpanded(False)

    '''
        根据点的个数创建shape
        输入参数：point的list
        输出参数：shape
    '''
    def CreateShape(self, points, close=True):
        if points is None:
            self.__logger.error("CreateShape failed, points is None")
            return

        # 如果点个数是1，则说明是点的shape
        if len(points) == 1:
            shape = Shape(name=Shape.POINT)
        # 如果点个数是2，则说明是线的shape
        elif len(points) == 2:
            shape = Shape(name=Shape.LINE)
        # 如果点个数时4，则说明是框的shape
        elif len(points) == 4:
            shape = Shape()

        # 将所有点插入shape
        for x, y in points:
            x, y, snapped = self.canvas.snapPointToCanvas(x, y)
            shape.addPoint(QPointF(x, y))

        return shape

    '''
        当前选中的QTreeItem改变时触发的槽函数
    '''
    def CurrentItemChange(self, currentItem, preItem):
        if currentItem is None:
            self.__logger.warn("CurrentItemChange failed, currentItem is None")
            return

        # 如果正在进行UI标签标注
        if self.labelModel is True:
            for shape in self.canvas.shapes:
                shape.selected = False

            # 选中不同的label类型的item，会高亮对应类型的shape
            labelText = currentItem.text(0)
            if labelText in self.canvas.itemShape.keys():
                for shape in self.canvas.itemShape[labelText]:
                    shape.selected = True

            self.canvas.update()
            return

        parentItem = currentItem.parent()
        if parentItem is None:
            return

        # 如果是切换了地图路径点的item，则会高亮对应的点
        if parentItem.text(2) == ITEM_TYPE_MAPPATH_SINGLE_LINE:
            index = parentItem.indexOfChild(currentItem)

            if len(self.canvas.shapes) == 0:
                self.__logger.warning('shapes is empty')
                return
            shape = self.canvas.shapes[0]
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            self.canvas.hVertex = index
            self.canvas.update()
            return

    '''
        当前选中的item的值发生变化时，触发的槽函数
        输入参数：currentItem表示当前选中的QTreeItem
        输入参数：column表示值发生改变的列
    '''
    def ItemValueChange(self, currentItem, column):
        if currentItem is None:
            self.__logger.error("ItemValueChange failed, currentItem is None")
            return

        if self.__uiExplore is not None:
            self.__uiExplore.OnItemValueChg(currentItem, column)
            return

        # 如果修改的是key值，直接返回
        if column == 0:
            return

        if self.canvas.mouseMoveFlag:
            return

        # 如果修改的值为数字，则需要进行检查，如果为非法值，会弹出提示窗口
        if currentItem.text(0) in Number_Key:
            if self._IsNumber(currentItem.text(column)) is False:
                self.__logger.error("{} should be number".format(currentItem.text(0)))
                self.numberDialog.popUp()
                if currentItem.text(0) == "taskID":
                    currentItem.setText(1, str(self.preTaskID))
                else:
                    currentItem.setText(1, self.preItemValue)
                return

        parentItem = currentItem.parent()
        if parentItem is None:
            self.__logger.warn('parent of currentItem is None')
            return

        if currentItem.text(0) == "task":
            currentItem.child(1).setText(1, currentItem.text(1))
            return

        # 如果修改的是taskID，则不仅需要检查是否合法，还需要检查是否重复，
        # 如果非法或重复，则需要恢复之前的taskID，如果合法且不重复，则完成修改，并同时修改对应的refertaskID
        # refertaskID命名规则如下
        # taskID为3时，referTaskID为30001
        if currentItem.text(0) == "taskID":
            taskID = int(currentItem.text(1))
            # 检查taskID是否为数字，且是否重复
            checkFlag = self.taskConfig.CheckTaskID(currentItem, taskID)
            # 如果不是，则弹出提示框
            if checkFlag is False:
                self.taskIDRepeatDialog.popUp()
                currentItem.setText(1, str(self.preTaskID))
            # 如果是，再修改对应的referTaskID
            else:
                for itemIndex in range(currentItem.parent().childCount()):
                    childItem = currentItem.parent().child(itemIndex)
                    if childItem.text(0) == "element":
                        for elementIndex in range(childItem.childCount()):
                            elementItem = childItem.child(elementIndex)
                            if elementItem.text(0) == "refer":
                                referTaskID = self.GetReferTaskID(childItem, taskID)
                                if referTaskID == -1:
                                    self.__logger.error('get refer taskID failed')
                                    return
                                elementItem.child(0).setText(1, str(referTaskID))

        # 如果修改的时框的值，则应该更新画布上shape的坐标
        if parentItem.text(0) in ["ROI", "location"]:
            x = int(parentItem.child(0).text(1))
            y = int(parentItem.child(1).text(1))
            w = int(parentItem.child(2).text(1))
            h = int(parentItem.child(3).text(1))

            shape = self.CreateShape([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
            self.canvas.loadShapes([shape])

    '''
        递归获取文件名，并根据其后缀名特点来创建对应的树结构
        输入参数：dir表示路径
        输入参数：treeItem表示树的根节点
        输入参数：level表示文件所处的树的层数
    '''
    def GetFileList(self, dir, treeItem, level):
        if treeItem is None:
            self.__logger.error("GetFileList failed, treeItem is None")
            return

        if dir is None or dir == "":
            self.__logger.error("GetFileList failed, dir is {}".format(dir))
            return

        # 获取文件名
        child = QTreeWidgetItem()
        filePath = dir
        _, fileName = os.path.split(filePath)
        child.setText(0, fileName)
        if level > 1:
            # 过滤某些特定文件
            if fileName in ["project.json", "task.json~", "project.json~"]:
                return

            # 创建树的节点，根据后缀名类型的不同来设置不同的icon
            treeItem.addChild(child)
            extension = os.path.splitext(fileName)[1]
            if extension in [".jpg", ".png", ".bmp", ".jpeg"]:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/menu/image.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                child.setIcon(0, icon)
            elif extension in ["", ".0", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9"]:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/menu/floder.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                child.setIcon(0, icon)
            elif extension in [".json"]:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/menu/json.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                child.setIcon(0, icon)
            elif extension in [".mp4", ".rmvb", ".avi"]:
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/menu/video.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                child.setIcon(0, icon)
        # 若dir为目录，则递归
        if os.path.isdir(dir):
            child.setText(2, ITEM_TYPE_IMAGE_FLODER)
            for s in os.listdir(dir):
                newDir=os.path.join(dir,s)
                if level > 1:
                    self.GetFileList(newDir, child, level + 1)
                else:
                    self.GetFileList(newDir, treeItem, level + 1)

    '''
        保存按钮的槽函数，将标注的信息保存为对应配置文件内容
    '''
    def SaveFile(self):
        topLevelItem = self.ui.treeWidget.topLevelItem(0)
        if topLevelItem is None:
            return

        self.taskJsonFile, self.referJsonFile = self.taskConfig.SaveTaskFile()        # 获取task和refer的内容
        self.UIJsonFile = self.uiConfig.SaveUITree()                                  # 获取UIConfig的内容
        self.mapGraphPathJsonDict = self.graphPath.SaveGraphPathFile()                # 获取图结构路径的配置文件内容
        self.actionSampleJsonFile = self.actionSample.SaveActionSampleRootFile()      # 获取动作配置文件的内容
        self.mapPathJsonDict = self.mapPath.SaveMapPathFile()                         # 获取地图路径配置文件的内容

        self.writeTaskJsonFile()                                                      # 写task.json配置文件
        self.writeUIJsonFile()                                                        # 写UIConfig.json配置文件
        self.writeReferJsonFile()                                                     # 写refer.json配置文件
        self.writeActionSampleJsonFile()                                              # 写动作配置文件
        self.writeMapPathJsonFile()                                                   # 写地图路径配置文件
        self.writeMapGraphPathJsonFile()                                              # 写图结构地图路径配置文件

        self.writeProjectFile()                                                       # 写project.json配置文件，记录一些图像路径等信息
        self.saveDialog.popUp(False)                                                  # 弹出保存成功提示框

    '''
        右键树结构界面时弹出菜单栏
    '''
    def showRightMenu(self):
        currentItem = self.ui.treeWidget.currentItem()

        self.rightMenu.clear()
        if currentItem is not None:
            if self.__uiExplore is not None:
                self.__uiExplore.onRightClick()
                return

            # 根据点击不同的地方，不同的QTreeItem来添加不同的动作，即弹出不同的菜单
            # 其中所有的action都会有对应的槽函数
            # 其中currentItem.text(2)表示该QTreeItem的类型
            # 在创建QTreeItem时会将其类型存在第三列中，也就是对应索引为2的text，第三列是隐藏的
            if currentItem.text(2) == ITEM_TYPE_PROJECT:
                self.rightMenu.addAction(self.actionAddVersion)
            elif currentItem.text(2) == ITEM_TYPE_VERSION:
                self.rightMenu.addAction(self.taskConfig.actionAddScene)
                self.rightMenu.addAction(self.uiConfig.actionAddUI)
                self.rightMenu.addAction(self.actionSample.actionAddActionSampleRoot)
                self.rightMenu.addAction(self.mapPath.actionAddMapPath)
                self.rightMenu.addAction(self.graphPath.actionAddGraphPath)
                self.rightMenu.addAction(self.actionDelVersion)
                self.canvas.resetState()
            elif currentItem.text(2) == ITEM_TYPE_SCENE:
                self.rightMenu.addAction(self.taskConfig.actionAddTask)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_TASK:
                self.rightMenu.addAction(self.taskConfig.actionAddElement)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_ELEMENT:
                self.rightMenu.addAction(self.actionChangeFilePath)
                self.rightMenu.addAction(self.taskConfig.actionAddTemplate)
                self.rightMenu.addAction(self.taskConfig.actionAddRefer)
                self.rightMenu.addAction(self.actionDelItem)

            elif currentItem.text(2) == ITEM_TYPE_REFER_TEMPLATES:
                self.rightMenu.addAction(self.taskConfig.actionAddTemplate)
                self.rightMenu.addAction(self.taskConfig.actionDetailConf)
                self.rightMenu.addAction(self.taskConfig.actionHiddenConf)

            elif currentItem.text(2) == ITEM_TYPE_TEMPLATE:
                self.rightMenu.addAction(self.actionChangeFilePath)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_GAMEOVER:
                self.rightMenu.addAction(self.uiConfig.actionAddGameOver)
            elif currentItem.text(2) == ITEM_TYPE_CLOSEICONS:
                self.rightMenu.addAction(self.uiConfig.actionAddCloseIcon)
            elif currentItem.text(2) == ITEM_TYPE_UISTATES:
                self.rightMenu.addAction(self.uiConfig.actionAddUIState)

            elif currentItem.text(2) ==ITEM_TYPE_UI_SCRIPT_TASK:
                self.rightMenu.addAction(self.uiConfig.actionAddScriptTask)

            elif currentItem.text(2) in [ITEM_TYPE_UISTATE_ID, ITEM_TYPE_UI_ELEMENT]:
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(0) in ["MatchStartState", "MatchEndStateFromUIStates"]:
                self.rightMenu.addAction(self.uiConfig.actionAddUIStateID)
            elif currentItem.text(2) == ITEM_TYPE_IMAGE_FLODER:
                self.rightMenu.addAction(self.actionImportImage)
            elif currentItem.text(2) == ITEM_TYPE_REFER_TASK:
                self.rightMenu.addAction(self.actionChangeFilePath)
                self.rightMenu.addAction(self.actionDelItem)
                self.rightMenu.addAction(self.taskConfig.actionDetailConf)
                self.rightMenu.addAction(self.taskConfig.actionHiddenConf)

            elif currentItem.text(2) == ITEM_TYPE_ACTIONSAMPLE:
                self.rightMenu.addAction(self.actionSample.actionAddActionSingle)
            elif currentItem.text(2) == ITEM_TYPE_ACTIONSAMPLE_ROOT:
                self.rightMenu.addAction(self.actionSample.actionAddActionSample)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_ACTIONSAMPLE_ELEMENT:
                self.rightMenu.addAction(self.actionChangeFilePath)
            elif currentItem.text(2) == ITEM_TYPE_MAPPATH_LINEPATH:
                self.rightMenu.addAction(self.mapPath.actionAddSinglePath)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_MAPPATH_SINGLE_LINE:
                self.rightMenu.addAction(self.mapPath.actionChangePath)
                self.rightMenu.addAction(self.actionDelItem)
            elif currentItem.text(2) == ITEM_TYPE_MAPPATH_IMAGE:
                self.rightMenu.addAction(self.mapPath.actionAddPathType)
            elif currentItem.parent() is not None and currentItem.parent().text(2) == ITEM_TYPE_MAPPATH_SINGLE_LINE:
                self.rightMenu.addAction(self.mapPath.actionDelPathPoint)
            elif currentItem.text(2) == ITEM_TYPE_MAPPATH_GRAPH:
                self.rightMenu.addAction(self.graphPath.actionAddGraphPathPoint)
            elif currentItem.text(0) in ["UI", "MapPath", "MapGraphPath", "task"]:
                self.rightMenu.addAction(self.actionDelItem)
        else:
            self.rightMenu.addAction(self.actionNewProject)
            self.rightMenu.addAction(self.actionLoadProject)
        self.rightMenu.exec_(QCursor.pos())
        self.ui.treeWidget.setCurrentItem(None)

    '''
        响应按键
    '''
    def keyPressEvent(self, QKeyEvent):
        if (QKeyEvent.key() == Qt.Key_S) and QApplication.keyboardModifiers() == Qt.ControlModifier:
            print("save")
            self.SaveFile()

        if (QKeyEvent.key() == Qt.Key_Escape):
            print("esc")
            self.canvas.setEditing(True)
            self.canvas.repaint()

    '''
        当窗口大小改变时，会自适应改变图像大小
    '''
    def resizeEvent(self, QResizeEvent):
        if self.canvas and not self.image.isNull():
            self.adjustScale()

    '''
        调整画布中图像的scale
    '''
    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW]()       # 相当于执行self.scaleFitWindow()
        # self.paintCanvas()
        if self.canvas.uiGraph:
            (scaleX, scaleY) = self.canvas.uiGraph.GetWindowScale()
            value = value * max(scaleX, scaleY)
        self.zoomWidget.setValue(int(100 * value))

    def paintCanvas(self, scale=1.0):
        if self.__uiExplore is not None:
            # self.__uiExplore.paintCanvas()
            return

        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    '''
        图像自适应窗口
    '''
    def scaleFitWindow(self):
        # e = 2.0  # So that no scrollbars are generated.
        e = 0.0
        w1 = self.ui.scroll.width() - e
        h1 = self.ui.scroll.height() - e
        a1 = w1 / h1

        # Calculate a new scale value based on the pixmap's aspect ratio.
        if self.canvas.pixmap is not None:
            w2 = self.canvas.pixmap.width() - 0.0
            h2 = self.canvas.pixmap.height() - 0.0
            a2 = w2 / h2
            return w1 / w2 if a2 >= a1 else h1 / h2
        else:
            return 1

    '''
        新建项目时，导入图像等操作
        输入参数：version表示版本号，类似v1.0
        输入参数：dialogFlag表示是否弹出“输入项目名”弹框，因为添加版本时也会导入图像，但是不需要写项目名
    '''
    def LoadImgDir(self, version, dialogFlag = True):
        self.labelModel = False
        self.ClearTreeWidget()
        if version is None:
            self.__logger.error("LoadImgDir failed, version is None")
            return

        # 弹出“输入项目名”弹框
        if dialogFlag:
            self.projectName = self.projectNameDialog.popUp()
            if self.projectName is None:
                return

            if os.path.exists("./project/" + self.projectName):
                self.projectNameExistDialog.popUp()
                self.__logger.info("project exist")
                return

        # 输入图像路径的弹框
        FileDialog = QFileDialog()
        FileDialog.setFileMode(QFileDialog.Directory)
        FileDialog.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        if FileDialog.exec():
            directoryName = FileDialog.selectedFiles()[0]
            if directoryName == "":
                return
        else:
            return

        self.projectPath = "./project/" + self.projectName                # project的路径

        isExist = os.path.exists(self.projectPath)
        # 如果当前的项目文件夹存在，则读取project.json中的内容
        if isExist:
            with open(self.projectPath + "/project.json", "r") as f:
                self.projectDict = json.load(f)
                if version not in self.projectDict["version"]:
                    os.makedirs(self.projectPath + "/" + version + "/data")
                    os.makedirs(self.projectPath + "/" + version + "/jsonFile")
                    self.projectDict["version"].append(version)
        # 如果当前你的项目文件夹不存在，则创建一些列需要的文件
        else:
            os.makedirs(self.projectPath)
            os.makedirs(self.projectPath + "/" + version + "/data")
            os.makedirs(self.projectPath + "/" + version + "/jsonFile")
            self.projectDict = {
                "projectPath": self.projectPath,
                "version": [version],
                "groupIDStart": 1,
                "taskIDStart": 1,
                "elementIDStart": 1,
                "templateIDStart": 1,
                "TaskImagePath": {
                    "element": {},
                    "template": {}
                },
                "GameOverIDStart": 1,
                "CloseIconIDStart": 1,
                "DeviceCloseIDStart":1,
                "UIStatesIDStart": 1,
                "UIImagePath": {
                    "gameOver": {},
                    "closeIcons": {},
                    "devicesCloseIcons": {},
                    "uiStates": {}
                },
                "ReferImagePath": {

                },
                "ActionSampleImagePath": {

                }
            }

        # 将project.json中的内容传给各个模块，以便各模块的函数使用
        self.mapPath.SetProjectInfo(self.projectName, self.projectPath)
        self.taskConfig.SetProjectDict(self.projectDict)
        self.uiConfig.SetProjectDict(self.projectDict)
        self.actionSample.SetProjectDict(self.projectDict)

        self.projectVersion = self.projectDict["version"]
        self.writeProjectFile()

        # 拷贝文件
        self.copyFile(directoryName, self.projectPath + "/" + version + "/data")
        taskJsonFileDict = {
            "allTask": []
        }

        # 初始化配置文件的dictionary
        self.taskJsonFile[version] = taskJsonFileDict
        self.writeTaskJsonFile()
        self.referJsonFile[version] = taskJsonFileDict
        self.writeReferJsonFile()
        self.UIJsonFile[version] = {}
        self.writeUIJsonFile()
        self.actionSampleJsonFile[version] = {}
        self.writeActionSampleJsonFile()
        self.mapPathJsonDict[version] = {}
        self.writeMapPathJsonFile()
        self.mapGraphPathJsonDict[version] = {}
        self.writeMapGraphPathJsonFile()

        # 建立项目的树结构
        self.ui.treeWidget.clear()
        root = QTreeWidgetItem(self.ui.treeWidget)
        root.setText(0, self.projectName)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/menu/floder.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        root.setIcon(0, icon)
        self.GetFileList(self.projectPath, root, 1)
        root.setText(2, ITEM_TYPE_PROJECT)
        for itemIdx in range(root.childCount()):
            treeItemVersion = root.child(itemIdx)
            version = treeItemVersion.text(0)
            if version not in ["project.json", "project.json~"]:
                treeItemVersion.setText(2, ITEM_TYPE_VERSION)
                # 导入task配置文件，建立对应的树结构
                self.taskConfig.LoadTaskJson(self.taskJsonFile[version], treeItemVersion)

                treeItemVersion.setExpanded(True)

        root.setExpanded(True)
        self.ui.pushButton_prev.setEnabled(False)
        self.ui.pushButton_next.setEnabled(False)
        self.canvas.resetState()

    '''
        写project.json文件
    '''
    def writeProjectFile(self):
        if self.projectDict is None:
            self.__logger.error('writeProjectFile failed, projectDict is None')
            return

        self.projectDict["groupIDStart"] = self.taskConfig.groupIDIndex
        self.projectDict["taskIDStart"] = self.taskConfig.taskIDIndex
        self.projectDict["elementIDStart"] = self.taskConfig.elementIDIndex
        self.projectDict["templateIDStart"] = self.taskConfig.templateIDIndex
        self.projectDict["GameOverIDStart"] = self.uiConfig.UIGameOverIDIndex
        self.projectDict["CloseIconIDStart"] = self.uiConfig.UICloseIconsIDIndex
        self.projectDict["UIStatesIDStart"] = self.uiConfig.UIStatesIDIndex
        self.projectDict["ActionIDStart"] = self.actionSample.ActionIDIndex
        with open(self.projectPath + "/project.json", "w") as f:
            json.dump(self.projectDict, f, indent = 4, separators=(',', ':'))

    '''
        写task.json文件
    '''
    def writeTaskJsonFile(self):
        for version in self.projectVersion:
            with open(self.projectPath + "/" + version + "/jsonFile/task.json", "w") as f:
                json.dump(self.taskJsonFile[version], f, indent=4, separators=(',', ':'))

    '''
        写UIConfig.json文件
    '''
    def writeUIJsonFile(self):
        for version in self.projectVersion:
            with open(self.projectPath + "/" + version + "/jsonFile/UIConfig.json", "w") as f:
                json.dump(self.UIJsonFile[version], f, indent=4, separators=(',', ':'))

    '''
        写refer.json文件
    '''
    def writeReferJsonFile(self):
        for version in self.projectVersion:
            with open(self.projectPath + "/" + version + "/jsonFile/refer.json", "w") as f:
                json.dump(self.referJsonFile[version], f, indent=4, separators=(',', ":"))

    '''
        写动作配置文件
    '''
    def writeActionSampleJsonFile(self):
        for version in self.projectVersion:
            if os.path.exists(self.projectPath + "/" + version + "/jsonFile/actionSample") is False:
                os.mkdir(self.projectPath + "/" + version + "/jsonFile/actionSample")
            with open(self.projectPath + "/" + version + "/jsonFile/actionSample/cfg.json", "w") as f:
                cfgJson = self.actionSampleJsonFile[version].copy()
                if "ActionCfgFile" in cfgJson.keys():
                    cfgJson['ActionCfgFile'] += '.json'
                if "ActionSample" in cfgJson.keys():
                    del cfgJson['ActionSample']
                json.dump(cfgJson, f, indent=4, separators=(',', ":"))
                # shutil.copy(self.projectPath + "/" + version + "/jsonFile/actionSample/cfg.json", "bin/ActionSampler/cfg/cfg.json")

            if "ActionSample" in self.actionSampleJsonFile[version].keys():
                for actionSample in self.actionSampleJsonFile[version]['ActionSample']:
                    fileName = actionSample['fileName']
                    del actionSample['fileName']
                    with open(self.projectPath + "/" + version + "/jsonFile/actionSample/" + fileName + ".json", "w") as f:
                        json.dump(actionSample, f, indent=4, separators=(',', ":"))
                        # shutil.copy(self.projectPath + "/" + version + "/jsonFile/actionSample/" + fileName + ".json", "bin/ActionSampler/cfg/" + fileName + ".json")

    '''
        写地图路径配置文件
    '''
    def writeMapPathJsonFile(self):
        for version in self.projectVersion:
            with open(self.projectPath + "/" + version + "/jsonFile/mapPathTemp.json", "w") as f:
                json.dump(self.mapPathJsonDict[version], f, indent=4, separators=(',', ":"))

            fPre = open(self.projectPath + "/" + version + "/jsonFile/mapPathTemp.json", "r")
            fCur = open(self.projectPath + "/" + version + "/jsonFile/mapPath.json", "w")
            for line in fPre.readlines():
                lineOut = line.replace('\"[', '[')
                lineOut = lineOut.replace(']\"', ']')
                fCur.write(lineOut)
            fCur.close()
            fPre.close()

            os.remove(self.projectPath + "/" + version + "/jsonFile/mapPathTemp.json")

    '''
        写图结构的地图路径配置文件
    '''
    def writeMapGraphPathJsonFile(self):
        for version in self.projectVersion:
            with open(self.projectPath + "/" + version + "/jsonFile/GraphPath.json", "w") as f:
                json.dump(self.mapGraphPathJsonDict[version], f, indent=4, separators=(',', ":"))

    '''
        拷贝文件
    '''
    def copyFile(self, sourcePath, targetPath):
        for file in os.listdir(sourcePath):
            sourceFile = os.path.join(sourcePath, file)
            targetFile = os.path.join(targetPath, file)

            if os.path.isdir(sourceFile):
                if os.path.exists(targetFile) is False:
                    os.makedirs(targetFile)

                self.copyFile(sourceFile, targetFile)

            if os.path.isfile(sourceFile):
                extension = os.path.splitext(file)[1]
                # if extension in ['.jpg', '.png', '.bmp', '.jpeg']:
                #     try:
                #         NormaImage(sourceFile, targetFile)
                #
                #     except Exception as error:
                #         dlg = CommonDialog(title="ImportError", text="error {}".format(error))
                #         dlg.popUp()

                # elif extension in [".names", ".cfg", ".weights"]:
                #     shutil.copy(sourceFile, targetFile)

                if extension in [".jpg", ".png", ".bmp", ".jpeg", ".names", ".cfg", ".weights"]:
                    shutil.copy(sourceFile, targetFile)

    '''
        导入已有的项目
    '''
    def ImportProject(self):
        self.labelModel = False
        # self.__uiExplore = None
        # self.ClearTreeWidget()
        if self.__uiExplore is not None:
             self.__uiExplore.Finish()
             self.__uiExplore = None
             self.mode = None
             self.canvas.update()

        projectFileName, Type = QFileDialog.getOpenFileName(None, "打开工程文件", "", "*.json;;*.json;;All Files(*)")
        if projectFileName == "":
            self.__logger.info('project file path is empty')
            return

        # 读取项目文件 project.json中的内容
        with open(projectFileName, "r") as f:
            self.projectDict = json.load(f)
            if "groupIDStart" not in self.projectDict.keys():
                self.projectDict["groupIDStart"] = 1
            if "taskIDStart" not in self.projectDict.keys():
                self.projectDict["taskIDStart"] = 1
            if "elementIDStart" not in self.projectDict.keys():
                self.projectDict["elementIDStart"] = 1
            if "templateIDStart" not in self.projectDict.keys():
                self.projectDict["templateIDStart"] = 1
            if "GameOverIDStart" not in self.projectDict.keys():
                self.projectDict["GameOverIDStart"] = 1
            if "CloseIconIDStart" not in self.projectDict.keys():
                self.projectDict["CloseIconIDStart"] = 1
            if "UIStatesIDStart" not in self.projectDict.keys():
                self.projectDict["UIStatesIDStart"] = 1
            if "TaskImagePath" not in self.projectDict.keys():
                self.projectDict["TaskImagePath"] = {
                    "element": {},
                    "template": {}
                }
            if "UIImagePath" not in self.projectDict.keys():
                self.projectDict["UIImagePath"] = {
                    "gameOver": {},
                    "closeIcons": {},
                    "uiStates": {}
                }
            if "ReferImagePath" not in self.projectDict.keys():
                self.projectDict["ReferImagePath"] = {}
            if "ActionSampleImagePath" not in self.projectDict.keys():
                self.projectDict["ActionSampleImagePath"] = {}

            # 将project.json内容传给各个模块，以便其成员函数使用
            self.projectVersion = self.projectDict["version"]
            self.projectPath = self.projectDict["projectPath"]
            self.taskConfig.SetProjectDict(self.projectDict)
            self.uiConfig.SetProjectDict(self.projectDict)
            self.actionSample.SetProjectDict(self.projectDict)

            # 导入所有已存在的配置文件
            for version in self.projectDict["version"]:
                # 读取task.json配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/task.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/task.json", "r") as taskfile:
                        self.taskJsonFile[version] = json.load(taskfile)
                else:
                    self.taskJsonFile[version] = {"allTask": []}
                    self.writeTaskJsonFile()

                # 读取UIConfig.json配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/UIConfig.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/UIConfig.json", "r") as UIFile:
                        self.UIJsonFile[version] = json.load(UIFile)
                elif os.path.exists(self.projectPath + "/" + version + "/jsonFile/UI.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/UI.json", "r") as UIFile:
                        self.UIJsonFile[version] = json.load(UIFile)
                else:
                    self.UIJsonFile[version] = OrderedDict()
                    self.writeUIJsonFile()

                # 读取refer.json配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/refer.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/refer.json", "r") as referFile:
                        self.referJsonFile[version] = json.load(referFile)
                else:
                    self.referJsonFile[version] = {"allTask": []}
                    self.writeReferJsonFile()

                # 读取动作配置相关的配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/actionSample/cfg.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/actionSample/cfg.json", "r") as actionFile:
                        self.actionSampleJsonFile[version] = json.load(actionFile)
                        if self.actionSampleJsonFile[version] != {}:
                            if "ActionCfgFile" in self.actionSampleJsonFile[version].keys():
                                fileName = self.actionSampleJsonFile[version]['ActionCfgFile']
                                self.actionSampleJsonFile[version]['ActionCfgFile'] = os.path.splitext(fileName)[0]
                            self.actionSampleJsonFile[version]['ActionSample'] = list()

                    for fileName in os.listdir(self.projectPath + "/" + version + "/jsonFile/actionSample"):
                        if fileName == "cfg.json":
                            continue

                        actionSampleDict = OrderedDict()
                        with open(self.projectPath + "/" + version + "/jsonFile/actionSample/" + fileName, "r") as actionFile:
                            actionSampleDict = json.load(actionFile)
                            actionSampleDict["fileName"] = os.path.splitext(fileName)[0]
                            self.actionSampleJsonFile[version]['ActionSample'].append(actionSampleDict)
                else:
                    self.actionSampleJsonFile[version] = {}
                    self.writeActionSampleJsonFile()

                # 读取mapPth.json配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/mapPath.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/mapPath.json", "r") as mapPathFile:
                        self.mapPathJsonDict[version] = json.load(mapPathFile)
                else:
                    self.mapPathJsonDict[version] = {}
                    self.writeMapPathJsonFile()

                # 读取GraphPath.json配置文件
                if os.path.exists(self.projectPath + "/" + version + "/jsonFile/GraphPath.json"):
                    with open(self.projectPath + "/" + version + "/jsonFile/GraphPath.json", "r") as graphPathFile:
                        self.mapGraphPathJsonDict[version] = json.load(graphPathFile)
                else:
                    self.mapGraphPathJsonDict[version] = {}
                    self.writeMapGraphPathJsonFile()

        _, self.projectName = os.path.split(self.projectPath)       # 读取项目名

        self.mapPath.SetProjectInfo(self.projectName, self.projectPath)

        # 根据读取的各个配置文件，生成每个配置文件对应的树结构
        self.ui.treeWidget.clear()
        root = QTreeWidgetItem(self.ui.treeWidget)
        root.setText(0, self.projectName)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/menu/floder.jpg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        root.setIcon(0, icon)
        self.GetFileList(self.projectPath, root, 1)
        root.setText(2, ITEM_TYPE_PROJECT)

        for itemIdx in range(root.childCount()):
            treeItemVersion = root.child(itemIdx)
            version = treeItemVersion.text(0)
            if version not in ["project.json", "project.json~"]:
                treeItemVersion.setText(2, ITEM_TYPE_VERSION)
                # 生成task任务的树结构
                self.taskConfig.LoadTaskJson(self.taskJsonFile[version], treeItemVersion)
                # 生成UI任务的树结构
                if self.UIJsonFile[version] != {}:
                    self.uiConfig.LoadUIJson(self.UIJsonFile[version], treeItemVersion)

                # 生成refer任务的树结构
                self.taskConfig.LoadReferJson(self.referJsonFile[version], treeItemVersion)
                # 生成动作配置任务的树结构
                if self.actionSampleJsonFile[version] != {}:
                    self.actionSample.LoadActionSample(self.actionSampleJsonFile[version], treeItemVersion)

                # 生成地图路径任务的树结构
                if self.mapPathJsonDict[version] != {}:
                    self.mapPath.CreateMapPathTree(self.mapPathJsonDict[version], treeItemVersion)

                # 生成图结构的地图路径任务的树结构
                if self.mapGraphPathJsonDict[version] != {}:
                    self.graphPath.CreateMapGraphPathTree(self.mapGraphPathJsonDict[version], treeItemVersion)
                treeItemVersion.setExpanded(True)

        root.setExpanded(True)
        self.ui.pushButton_prev.setEnabled(False)
        self.ui.pushButton_next.setEnabled(False)
        self.canvas.resetState()

    '''
        获取对应key值的子Item
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
        添加version的槽函数
    '''
    def AddVersion(self):
        version = self.versionDialog.popUp()
        if version == "":
            self.__logger.info('version is empty')
            return
        self.LoadImgDir(version, False)

    '''
        删除version的槽函数
    '''
    def DeletVersion(self):
        treeItemVersion = self.ui.treeWidget.currentItem()
        if treeItemVersion is None:
            self.__logger.error('DeletVersion failed, treeItemVersion is None')
            
            return

        version = treeItemVersion.text(0)

        # 弹出“确认删除”对话框
        confirmDia = confirmDialog("确认删除")
        confirmFlag = confirmDia.popUp()
        if confirmFlag == True:
            # 删除对应文件
            treeItemVersion.parent().removeChild(treeItemVersion)
            self.taskJsonFile.pop(version)
            self.projectDict["version"].remove(version)
            self.writeProjectFile()
            if os.path.exists(self.projectPath + "/" + version):
                shutil.rmtree(self.projectPath + "/" + version)

    '''
        删除某一item
    '''
    def DelItem(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.__logger.error('DelItem failed, treeItem is None')
            return

        treeItem.parent().removeChild(treeItem)

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
        修改图片路径
    '''
    def ChangeFilePath(self):
        treeItem = self.ui.treeWidget.currentItem()
        if treeItem is None:
            self.__logger.error('ChangeFilePath failed, treeItem is None')
            
            return

        # 判断当前的item的key值是否在以下集合中，不在则返回
        keyName = treeItem.text(0)
        if keyName not in ["target", "element", "template", "path", "cfgPath", "weightPath",
                           "namePath", "maskPath", "imgPath", "refer", "scriptPath"]:
            self.__logger.info('ChangeFilePath failed, keyName is {}'.format(keyName))
            return
        
        version = self.GetVersionItem(treeItem).text(0)       # 获取当前version

        # 弹出导入图像的对话框
        filePath = "./project/" + self.projectName + "/" + version + "/data/"
        pathPart = "/project/" + self.projectName + "/" + version + "/data/"
        file, Type = QFileDialog.getOpenFileName(None, "选择文件", filePath, "*.*")
        dirPath, fileName = os.path.split(file)
        # fileShowName = filePath + fileName
        fileIndex = file.find(pathPart)
        if fileIndex == -1:
            fileShowName = filePath + fileName
            filePathName = "/data/" + fileName
        else:
            fileShowName = filePath + file[fileIndex + len(pathPart): ]
            filePathName = "/data/" + file[fileIndex + len(pathPart): ]
        if file == "":
            return

        # 如果导入的图片不在创建项目时导入的图片中，则将其拷贝至data目录下
        if not os.path.exists(fileShowName):
            shutil.copy(file, fileShowName)

        # 如果双击的item的key是"element"或 "refer"
        if keyName in ["element", "refer"]:
            # 获取item中所有rect项的子item
            rectItemList = self.GetRectItem(treeItem)
            self.PaintImage(fileShowName)               # 画出修改后的图像
            treeItem.setText(3, fileShowName)           # 将其绝对路径记录在tree中的第四列（被隐藏）

            # 在图像上画出每个框
            for rectItem in rectItemList:
                self.canvas.setRectTreeItem(rectItem)
                self.canvas.currentModel.append(Shape.RECT)
                self.canvas.setEditing(False)
    
                x = int(rectItem.child(0).text(1))
                y = int(rectItem.child(1).text(1))
                w = int(rectItem.child(2).text(1))
                h = int(rectItem.child(3).text(1))

                # 创建shape，设置为框的坐标，画在画布上
                if x > 0 or y > 0 or w > 0 or h > 0:
                    self.canvas.setEditing()
                    shape = self.CreateShape([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
                    self.canvas.AddShape(shape)
                    self.canvas.shapeTree[shape] = rectItem
                    self.canvas.update()
        # 如果双击的item的key是"template"或 "target"
        elif keyName in ["template", "target"]:
            # 获取item中所有rect项的子item
            rectItemList = self.GetRectItem(treeItem)

            self.PaintImage(fileShowName)                           # 画出修改后的图像

            # 在图像上画出每个框
            for rectItem in rectItemList:
                self.canvas.setRectTreeItem(rectItem)
                self.canvas.currentModel.append(Shape.RECT)
                treeItem.setText(3, fileShowName)

                self.canvas.setEditing(False)
    
                x = int(rectItem.child(0).text(1))
                y = int(rectItem.child(1).text(1))
                w = int(rectItem.child(2).text(1))
                h = int(rectItem.child(3).text(1))

                # 创建shape，设置为框的坐标，画在画布上
                if x > 0 or y > 0 or w > 0 or h > 0:
                    self.canvas.setEditing()
                    shape = self.CreateShape([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
                    self.canvas.AddShape(shape)
                    self.canvas.shapeTree[shape] = rectItem
                    self.canvas.update()

                # 将路径显示在path中，template的path项对应的是第三个子item，target的path项对应的是第一个子item
                if keyName == "template":
                    treeItem.child(2).setText(1, filePathName)
                elif keyName == "target":
                    treeItem.child(0).setText(1, filePathName)
        # 如果双击的item的key值是”path“
        elif keyName == "path":
            if treeItem.parent().text(0) == "template":
                rectItemList = self.GetRectItem(treeItem.parent())

                # 修改显示的图像
                treeItem.parent().setText(3, fileShowName)
                self.PaintImage(fileShowName)
                for rectItem in rectItemList:
                    self.canvas.setRectTreeItem(rectItem)
                    self.canvas.currentModel.append(Shape.RECT)
                    self.canvas.setEditing(False)
                    treeItem.setText(1, filePathName)
        # 如果双击的item的key值是”imgPath“
        elif keyName == "imgPath":
            parentItem = treeItem.parent()
            if parentItem.text(0) == "element":
                # 获取item中所有rect项的子item，并遍历，设置为需要画框
                rectItemList = self.GetRectItem(treeItem.parent())
                for rectItem in rectItemList:
                    self.canvas.setRectTreeItem(rectItem)
                    self.canvas.currentModel.append(Shape.RECT)

                # 如果是UI下的item，则获取其动作的item（actionItem），画出对应的shape
                if parentItem.parent().parent().text(0) == "UI":
                    actionItem = None
                    for itemIndex in range(parentItem.childCount()):
                        item = parentItem.child(itemIndex)
                        if item.text(0) == "action":
                            actionItem = item

                    if actionItem is not None:
                        # 如果actionItem的子item数量为4，说明是滑动动作，因此需要画线
                        if actionItem.childCount() == 4:
                            self.canvas.currentModel.append(Shape.LINE)
                            self.canvas.setLineTreeItem(actionItem)
                        # 如果actionItem的子item数量为2，说明是点击动作，因此需要点
                        elif actionItem.childCount() == 2:
                            self.canvas.currentModel.append(Shape.POINT)
                            self.canvas.setPointTreeItem(actionItem)
                
                parentItem.setText(3, fileShowName)
                self.PaintImage(fileShowName)
                self.canvas.setEditing(False)
                treeItem.setText(1, filePathName)
                
        elif keyName in ["cfgPath", "weightPath", "namePath", "maskPath", "scriptPath"]:
            treeItem.setText(1, filePathName)

        # self.SetTreeImageState()

    def PaintImage(self, imgPath):
        if imgPath == "" or imgPath is None:
            self.__logger.error('wrong imgPath: {}'.format(imgPath))
            return

        try:
            if not os.path.exists(imgPath):
                imgPath = "./project/" + self.projectName + "/v1.0/"  + imgPath
            if not os.path.exists(imgPath):
                raise Exception("there is no file {}".format(imgPath))

            # NormaImage(imgPath, imgPath)
            frame = QImage(imgPath)
            if 0 in [frame.width(), frame.height()]:
                raise Exception("image {} is invalid".format(imgPath))

            if self.canvas.uiGraph is not None:
                scaleW, scaleH = self.canvas.uiGraph.GetWindowScale()
                frame = frame.scaled(frame.width() * scaleW, frame.height() * scaleH)

            self.image = frame
            pix = QPixmap.fromImage(frame)
            self.canvas.loadPixmap(pix)
            self.canvas.setEnabled(True)
            self.adjustScale(initial=True)
            self.paintCanvas()

        except Exception as error:
            self.__logger.error('read image failed, imgPath: {}'.format(imgPath))
            self.__logger.error(traceback.format_exc())
            dlg = CommonDialog(title="ImportError", text="error {}".format(error))
            dlg.popUp()

    def PaintCVImage(self, frame):
        if frame is None:
            self.__logger.error('frame is None')
            return

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        QtImg = QImage(img_rgb.data, img_rgb.shape[1], img_rgb.shape[0], QtGui.QImage.Format_RGB32)
        self.image = QtImg
        try:
            pix = QPixmap.fromImage(QtImg)
            self.canvas.loadPixmap(pix)
            self.canvas.setEnabled(True)
            self.adjustScale(initial=True)
            self.paintCanvas()
        except Exception as e:
            self.__logger.error('read image failed')
            self.__logger.error(e)

    def _GetDictValue(self, dic, keyList):
        for key in keyList:
            if key in dic.keys():
                return dic[key]

        return None

    def _IsNumber(self, s):
        if self._IsIntNumber(s) or self._IsFloatNumber(s):
            return True
        else:
            self.__logger.error('{} is not number'.format(s))
            return False

    def _IsIntNumber(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def _IsFloatNumber(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


if __name__ == "__main__":
    logging.config.fileConfig(LOGPATH)
    LOG = logging.getLogger('sdktool')
    try:
        app = QtWidgets.QApplication(sys.argv)
        ui = Ui_MainWindow()

        MainWindow = SDKMainWindow(ui)

        def SigHandle(sigNum, _):
            LOG.info('signal {0} recved, sampler is going to shut...'.format(sigNum))
            MainWindow.Finish()
            exit(-1)

        signal.signal(signal.SIGINT, SigHandle)

        ui.setupUi(MainWindow)
        MainWindow.Init()

        MainWindow.showMaximized()
        app.exec_()
        MainWindow.Finish()
        time.sleep(1)
    except Exception as e:
        LOG.error(e)
        LOG.error(traceback.format_exc())