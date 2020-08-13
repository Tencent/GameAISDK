# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import re
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt
import labelme
from PyQt5.QtWidgets import *
import json
import traceback
import platform
import subprocess
from libs.shape import *

platform = sys.platform
labelImageIndex = 0
labelImageList = []


# QMainWindow是QWidget的派生类
# class UIExploreDialog(QMainWindow):
class UIExploreDialog(QDialog):
    def __init__(self, canvas=None,  ui=None):
        super().__init__()

        self.__logger = logging.getLogger('sdktool')
        self.__samplePath = './data/UIExplore/sample'
        self.__canvas = canvas
        self.__ui = ui
        icon = QIcon()
        icon.addPixmap(QPixmap(":/menu/import.jpg"), QIcon.Normal, QIcon.Off)

        vBoxOpenFile = QVBoxLayout()
        labelBegin = QLabel('UI自动化探索: step1-->step5, 请依次进行\n')
        label1 = QLabel("Step1: 打开样本文件夹：")
        btnOpenFile = QPushButton()
        btnOpenFile.setIcon(icon)

        btnOpenFile.setToolTip("打开样本图像路径！")
        # btnOpenFIle.setStatusTip("打开样本图像路径StatusTip！")
        btnOpenFile.clicked.connect(self.funOpenFile)

        hBoxOpenFile = QHBoxLayout()
        # 单行文本框
        self.lineEdit = QLineEdit(self.__samplePath)
        self.lineEdit.selectAll()
        self.lineEdit.returnPressed.connect(self.funOK)
        hBoxOpenFile.addWidget(self.lineEdit)
        hBoxOpenFile.addWidget(btnOpenFile)

        vBoxOpenFile.addWidget(labelBegin)
        vBoxOpenFile.addWidget(label1)
        vBoxOpenFile.addLayout(hBoxOpenFile)

        # 布局
        vBoxAutoLabel = QVBoxLayout()
        label2 = QLabel("Step2: 样本自动标记")
        self.progressBar = QProgressBar(self)
        vBoxAutoLabel.addWidget(label2)
        vBoxAutoLabel.addWidget(self.progressBar)

        vBoxLabelImg = QVBoxLayout()
        label3 = QLabel("Step3: 样本重标记")
        vBoxLabelImg.addWidget(label3)
        reLabelBtn = QPushButton("开始标记")
        vBoxLabelImg.addWidget(reLabelBtn)
        reLabelBtn.clicked.connect(self.LabelImage)

        vBoxTrain = QVBoxLayout()
        label4 = QLabel("Step4: 训练")
        vBoxTrain.addWidget(label4)
        trainBtn = QPushButton("开始训练")
        vBoxTrain.addWidget(trainBtn)
        trainBtn.clicked.connect(self.train)

        vBoxUIGraph = QVBoxLayout()
        labelGraph = QLabel("Step5: UI自动化探索结果")
        vBoxUIGraph.addWidget(labelGraph)
        btn5 = QPushButton("结果分析")
        vBoxUIGraph.addWidget(btn5)
        # 布局
        vBox = QVBoxLayout()
        vBox.addLayout(vBoxOpenFile)
        vBox.addLayout(vBoxAutoLabel)
        # vBox.addWidget(label2)
        # vBox.addWidget(self.progressBar)
        vBox.addLayout(vBoxLabelImg)
        vBox.addLayout(vBoxTrain)
        vBox.addLayout(vBoxUIGraph)

        # widget = QWidget()
        # self.setCentralWidget(widget)  # 建立的widget在窗体的中间位置
        # widget.setLayout(vBox)

        # 布局完毕后，才可得到焦点
        # self.lineEdit.setFocus()

        # Window设置
        self.resize(500, 150)
        self.center()
        self.setFont(QFont('宋体', 14))
        self.setWindowTitle('UI Explore')

        buttonBox = bb = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        vBox.addWidget(buttonBox)
        self.setLayout(vBox)
        # self.setWindowIcon(QIcon('10.png'))
        self.show()

        # self.labelImageIndex = -1
        # self.labelImageList = []

        self.image = None

    def validate(self):
        self.confirmFlag = True
        self.accept()

    def center(self):
        # 得到主窗体的框架信息
        qr = self.frameGeometry()
        # 得到桌面的中心
        cp = QDesktopWidget().availableGeometry().center()
        # 框架的中心与桌面中心对齐
        qr.moveCenter(cp)
        # 自身窗体的左上角与框架的左上角对齐
        self.move(qr.topLeft())

    def funOK(self):
        try:
            text = self.lineEdit.text()
            self.textBrowser.append("{} = <b>{}</b>".format(text, eval(text)))
        except:
            self.textBrowser.append("输入的表达式<font color=red>“{}”</font>无效!".format(text))

    def funCancel(self):
        self.lineEdit.clear()

    def GetfilesCount(self, directoryName, formatList=[".png", ".bmp", ".jpg"]):

        file_count = 0
        for dirPath, dirNames, fileNames in os.walk(directoryName):
            for file in fileNames:
                if os.path.splitext(file)[1] in formatList:
                    file_count = file_count + 1

        return file_count

    def funOpenFile(self):
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

        self.__samplePath = directoryName
        self.lineEdit.setText(directoryName)

        self.progressBar.setMinimum(0)
        picNumber = self.GetfilesCount(directoryName)
        self.progressBar.setMaximum(picNumber)

        self.RunAutoLabelImage()
        self.__logger.info("run over label image....")
        jsonFileNumber = self.GetfilesCount(directoryName, formatList=[".json"])
        self.progressBar.setValue(jsonFileNumber)
        self.__logger.info("picture number is {}, json file number is {}".format(picNumber, jsonFileNumber))

    def RunAutoLabelImage(self):
        currentPath = os.getcwd()
        os.chdir("bin/RefineDet/")
        args = [
            'python',
            'detect_one_image.py',
        ]
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                pro = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                pro = subprocess.Popen(args)
        else:
            pro = subprocess.Popen("python detect_one_image.py", shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)

        if pro is None:
            self.__logger.error("open action sample failed")
            return
        else:
            self.__logger.info('Run ActionSample Create PID: {} SubProcess'.format(pro.pid))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, QCloseEvent):
        reply = QMessageBox.question(self,
                                     'UI自动化探索配置项',
                                     "是否要退出？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()

    def LabelImage(self):
        self.__logger.info("begin label....")
        # self.labelImageList = list()  # 所有图像的list
        labelImageIndex = 0  # 当前显示的图像在所有图像list中的索引

        # 读取所有图像，如果图像有对应的标签，则不显示它，将labelImageIndex设置为第一个没有标签的图像，从第一个没有标签的图像开始显示
        indexFlag = True
        for root, dirs, files in os.walk(self.__samplePath):
            for file in files:
                if os.path.splitext(file)[1] in [".png", ".bmp", ".jpg"]:
                    # self.labelImageList.append(os.path.join(root, file))
                    labelImageList.append(os.path.join(root, file))
                    # self.ui.fileListWidget.addItem(os.path.join(root, file))
                    if os.path.exists(root + '/' + file[: file.rfind('.')] + ".json") and indexFlag is True:
                        # self.labelImageIndex += 1
                        labelImageIndex += 1
                    else:
                        indexFlag = False

        # if self.labelImageIndex >= len(self.labelImageList):
        #     self.labelImageIndex = 0
        self.__logger.info("image list len is {}, index is {} ".format(len(labelImageList), labelImageIndex))
        if labelImageIndex >= len(labelImageList):
            labelImageIndex = 0
        self.__logger.info("image list len is {}, index is {} ".format(len(labelImageList), labelImageIndex))

        self.__canvas.resetState()
        self.__canvas.addUIGraph(None)
        self.LoadLabelImage()

        self.__canvas.setTreeWidget(self.__ui.treeWidget)
        self.__canvas.setUI(self.__ui)

        self.__ui.pushButton_prev.setEnabled(True)
        self.__ui.pushButton_next.setEnabled(True)

    def train(self):
        loss_x = []
        loss_y = []

        plt.ion()
        plt.figure(figsize=(15, 9))

        font1 = {'family': 'Times New Roman',
                 'weight': 'normal',
                 'size': 23
                 }
        try:
            with open("./data/log.txt") as f:  # 根据自己的目录做对应的修改
                preEpoch = 0
                lossList = []
                for line in f:
                    line = line.strip(' ')
                    self.__logger.debug("line {}".format(line))

                    if len(line.split("AL:")) == 2:
                        strLossList = re.findall(r"AL:(.+?) AC", line)
                        if len(strLossList) < 1:
                            exit()
                        curLoss = float(strLossList[0].strip())
                        lossList.append(curLoss)

                        strEpoch = re.findall(r"Epoch:(.+?) \|| epochiter:", line)
                        if len(strEpoch) < 1:
                            exit()
                        curEpoch = float(strEpoch[0].strip())
                        if curEpoch > preEpoch:
                            loss = np.mean(lossList)
                            loss_y.append(loss)
                            loss_x.append(curEpoch)
                            preEpoch = curEpoch
                            lossList.clear()
                            plt.plot(loss_x, loss_y, '', c='g')
                            plt.title('RefinDet Training', font1)
                            plt.xlabel('epoch', font1)
                            plt.ylabel('loss', font1)
                            plt.grid(loss_x)
                            plt.pause(0.1)
                        else:
                            continue
            plt.ioff()
            plt.show()

        except Exception as e:
            self.__logger.error("train error {}".format(e))

    def popUp(self, move=True):
        if move:
            self.move(QCursor.pos())
        return self.confirmFlag if self.exec() else None

    def getFilePath(self):
        return self.__samplePath

    '''
        展示UI标签图像
    '''
    def LoadLabelImage(self):
        self.__logger.info("image list len is {}".format(len(labelImageList)))

        if len(labelImageList) < 0:
            self.__logger.error("folder{} has no image, please check".format(self.__samplePath))
            return
        labelImageIndex = 0
        fileName = labelImageList[labelImageIndex]
        self.PaintImage(fileName)
        sceneTreeItem = self.CreateTreeItem(key='fileName')
        sceneTreeItem.setText(1, os.path.basename(fileName))
        sceneTreeItem.setText(2, fileName)
        self.__ui.treeWidget.addTopLevelItem(sceneTreeItem)
        sceneTreeItem = self.CreateTreeItem(key='scene', edit=True)
        self.__ui.treeWidget.addTopLevelItem(sceneTreeItem)
        sceneTreeItem = self.CreateTreeItem(key='labels')
        self.__ui.treeWidget.addTopLevelItem(sceneTreeItem)
        self.LoadLabelJson(fileName)
        self.__canvas.setLabel()
        self.__canvas.labelFlag = True

    def CreateTreeItem(self, key, value=None, type=None, edit=False):
        child = QTreeWidgetItem()
        child.setText(0, str(key))

        if value is not None:
            child.setText(1, str(value))

        if type is not None:
            child.setText(2, type)
        # child.setIcon(0, self.treeIcon)
        if edit is True:
            child.setFlags(child.flags() | Qt.ItemIsEditable)

        return child

    def PaintImage(self, imgPath):
        if imgPath == "" or imgPath is None:
            self.__logger.error('wrong imgPath: {}'.format(imgPath))
            return

        try:
            if not os.path.exists(imgPath):
                imgPath = "./project/" + self.projectName + "/v1.0/" + imgPath
            if not os.path.exists(imgPath):
                raise Exception("there is no file {}".format(imgPath))

            frame = QImage(imgPath)
            if self.__canvas.uiGraph is not None:
                scaleW, scaleH = self.canvas.uiGraph.GetWindowScale()
                frame = frame.scaled(frame.width() * scaleW, frame.height() * scaleH)

            self.image = frame
            pix = QPixmap.fromImage(frame)
            self.__canvas.loadPixmap(pix)
            self.__canvas.setEnabled(True)
            # self.adjustScale(initial=True)
            self.paintCanvas()
        except Exception as e:
            self.__logger.error('read image failed, imgPath: {}'.format(imgPath))
            self.__logger.error(traceback.format_exc())

    def LoadLabelJson(self, labelImageName):
        # 清除画布的一些数据
        self.__canvas.shapeItem.clear()
        self.__canvas.itemShape.clear()

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
        self.__ui.treeWidget.topLevelItem(1).setText(1, sceneName)

        # 对每个label，读取其内容并展示在画布上
        for labelShape in labelJsonDict["labels"]:
            labelText = labelShape["label"]
            # labelName = labelShape["name"]
            if "clickNum" in labelShape.keys():
                labelClickNum = int(labelShape["clickNum"])
            else:
                labelClickNum = 0
            self.__canvas.labelDialog.addLabelHistory(labelText)
            treeLabelItem = None
            labelFlag = False
            labelTreeItem = self.__ui.treeWidget.topLevelItem(2)
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
            self.__canvas.shapes.append(shape)
            self.__canvas.shapeItem[shape] = treeLabelItem
            if labelText not in self.__canvas.itemShape.keys():
                self.__canvas.itemShape[labelText] = list()
            self.__canvas.itemShape[labelText].append(shape)

    # def adjustScale(self, initial=False):
    #     value = self.scalers[self.FIT_WINDOW]()       # 相当于执行self.scaleFitWindow()
    #     # self.paintCanvas()
    #     if self.__canvas.uiGraph:
    #         (scaleX, scaleY) = self.__canvas.uiGraph.GetWindowScale()
    #         value = value * max(scaleX, scaleY)
    #     self.zoomWidget.setValue(int(100 * value))

    def paintCanvas(self, scale=1.0):
        assert not self.image.isNull(), "cannot paint null image"
        # self.__canvas.scale = 0.01 * self.zoomWidget.value()
        self.__canvas.adjustSize()
        self.__canvas.update()

    @staticmethod
    def GetFileList(parent=None):
        dialog = UIExploreDialog(parent)
        # result = dialog.exec_()
        return dialog.labelImageList, dialog.labelImageIndex


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = UIExploreDialog()
    sys.exit(app.exec_())