# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from libs.confirmDialog import confirmDialog

from libs.Module.UIExplore.canvasUtils import *
from libs.Module.UIExplore.CNNTrainSample import CNNTrainSample
from libs.Module.UIExplore.UsrLabelImage import UsrLabelImage
from libs.Module.UIExplore.ExploreResult import ExploreResult
from libs.Module.UIExplore.AutoLabelImage import AutoLabelImage


class UIExplore(QWidget):
    def __init__(self, canvas=None,  ui=None, zoomWidget=None):
        super().__init__()

        self.__logger = logging.getLogger('sdktool')
        cwd = os.getcwd()
        self.__autoLabelPath = '{}/data/UIExplore/sample'.format(cwd)
        self.__usrLabelPath = '{}/data/UIExplore/sample'.format(cwd)
        self.__trainSamplePath = '{}/data/UIExplore/sample'.format(cwd)
        self.__exploreRetPath = '{}/data/UIExplore/results'.format(cwd)
        self.__canvas = canvas
        self.__ui = ui
        self.__ui.treeWidget.setColumnWidth(0, 200)
        self.__ui.treeWidget.setColumnWidth(1, 250)
        self.__zoomWidget = zoomWidget
        self.__trainItem = None

        for index in range(self.__ui.treeWidget.topLevelItemCount()):
            self.__ui.treeWidget.takeTopLevelItem(0)

        self.__UsrLabelSampleTree = None

        self._BuildTree(self.__ui.treeWidget)
        self._RegisterHandler()

        self.__ui.treeWidget.clicked.connect(self.OnTreeClicked)

        self.progressBar = None
        self.image = None
        self.__mode = None
        self.__trainSample = CNNTrainSample(self.__trainSamplePath, self.__canvas, self.__zoomWidget, self.__ui)

        self.__usrLabelImage = UsrLabelImage(self.__usrLabelPath, self.__canvas, self.__zoomWidget, self.__ui)
        self.__ExploreResult = ExploreResult(self.__canvas, self.__zoomWidget, self.__ui)
        self.__autoLabelImage = AutoLabelImage(self.__canvas, self.__zoomWidget, self.__ui)
        # todo QMenu means
        self.__rightMenu = QMenu(self.__ui.treeWidget)

        self.__actionAddImg = None
        self.__actionChgImg = None
        self.__actionDelImg = None
        self.__actionDelDir = None
        self.__addSampleFolder = None
        self.InitAction()

    def _BuildTree(self, tree):
        # step 1 样本自动标记
        autoLabelItem = CreateTreeItem(key=TOP_LEVEL_TREE_KEYS[AUTO_LABEL], edit=False)
        pathItem = CreateTreeItem(key=CHILD_ITEM_KEYS[AUTO_LABEL][0], value=self.__autoLabelPath, edit=True)
        pathItem.setIcon(0, QIcon(":/menu/import.jpg"))
        autoLabelItem.addChild(pathItem)
        start = CreateTreeItem(key=CHILD_ITEM_KEYS[AUTO_LABEL][1], value='', edit=False)
        start.setIcon(0, QIcon(":/menu/开始.png"))
        autoLabelItem.addChild(start)
        tree.addTopLevelItem(autoLabelItem)
        autoLabelItem.setExpanded(True)

        # step 2 样本重标记
        relabelItem = CreateTreeItem(key=TOP_LEVEL_TREE_KEYS[USR_LABEL], edit=False)
        pathItem1 = CreateTreeItem(key=CHILD_ITEM_KEYS[USR_LABEL][0], value=self.__usrLabelPath, edit=True)
        pathItem1.setIcon(0, QIcon(":/menu/import.jpg"))
        relabelItem.addChild(pathItem1)

        self.__UsrLabelSampleTree = CreateTreeItem(key=CHILD_ITEM_KEYS[USR_LABEL][1], value='', edit=False)
        self.__UsrLabelSampleTree.setIcon(0, QIcon(":/menu/floder.jpg"))
        relabelItem.addChild(self.__UsrLabelSampleTree)
        GetFileList(self.__usrLabelPath, self.__UsrLabelSampleTree, 1)
        self.__logger.info("###############create label sample tree###############")

        start = CreateTreeItem(key=CHILD_ITEM_KEYS[USR_LABEL][2], value='', edit=False)
        start.setIcon(0, QIcon(":/menu/开始.png"))
        relabelItem.addChild(start)

        start = CreateTreeItem(key=CHILD_ITEM_KEYS[USR_LABEL][3], value='', edit=False)
        start.setIcon(0, QIcon(":/menu/保存.jpg"))
        relabelItem.addChild(start)

        tree.addTopLevelItem(relabelItem)
        relabelItem.setExpanded(True)

        # step 3 训练
        self.__trainItem = CreateTreeItem(key=TOP_LEVEL_TREE_KEYS[TRAIN], edit=False)
        pathItem2 = CreateTreeItem(key=CHILD_ITEM_KEYS[TRAIN][0], value=self.__trainSamplePath, edit=True)
        pathItem2.setIcon(0, QIcon(":/menu/import.jpg"))
        self.__trainItem.addChild(pathItem2)

        trainParam = CreateTreeItem(key=CHILD_ITEM_KEYS[TRAIN][1], value='', edit=False)
        trainParam.setIcon(0, QIcon(":/menu/set.jpg"))
        for key, value in TRAIN_PARAMS.items():
            param = CreateTreeItem(key=key, value=value, edit=True)
            trainParam.addChild(param)
        self.__trainItem.addChild(trainParam)
        self.__trainItem.addChild(start)

        start = CreateTreeItem(key=CHILD_ITEM_KEYS[TRAIN][2], value='', edit=False)
        start.setIcon(0, QIcon(":/menu/开始.png"))
        self.__trainItem.addChild(start)
        result = CreateTreeItem(key=CHILD_ITEM_KEYS[TRAIN][3], value='', edit=False)
        result.setIcon(0, QIcon(":/menu/switch.jpg"))
        self.__trainItem.addChild(result)
        tree.addTopLevelItem(self.__trainItem)
        self.__trainItem.setExpanded(True)

        # step 4 UI自动化探索结果
        resultItem = CreateTreeItem(key=TOP_LEVEL_TREE_KEYS[EXPLORE_RESULT], edit=False)
        result = CreateTreeItem(key=CHILD_ITEM_KEYS[EXPLORE_RESULT][0], value=self.__exploreRetPath, edit=False)
        result.setIcon(0, QIcon(":/menu/import.jpg"))
        resultItem.addChild(result)
        result1 = CreateTreeItem(key=CHILD_ITEM_KEYS[EXPLORE_RESULT][1], value='', edit=False)
        result1.setIcon(0, QIcon(":/menu/graph.jpg"))
        resultItem.addChild(result1)
        result2 = CreateTreeItem(key=CHILD_ITEM_KEYS[EXPLORE_RESULT][2], value='', edit=False)
        result2.setIcon(0, QIcon(":/menu/switch.jpg"))
        resultItem.addChild(result2)
        result3 = CreateTreeItem(key=CHILD_ITEM_KEYS[EXPLORE_RESULT][3], value='', edit=False)
        result3.setIcon(0, QIcon(":/menu/switch.jpg"))
        resultItem.addChild(result3)

        tree.addTopLevelItem(resultItem)
        resultItem.setExpanded(True)

    def _RegisterHandler(self):
        self.__funcHander = dict()

        # Step1: auto label image
        self.__funcHander[TOP_LEVEL_TREE_KEYS[AUTO_LABEL] + CHILD_ITEM_KEYS[AUTO_LABEL][0]] = self.FuncOpenFile
        self.__funcHander[TOP_LEVEL_TREE_KEYS[AUTO_LABEL] + CHILD_ITEM_KEYS[AUTO_LABEL][1]] = self.OnAutoLabelImage

        # Step2: label image by user
        self.__funcHander[TOP_LEVEL_TREE_KEYS[USR_LABEL] + CHILD_ITEM_KEYS[USR_LABEL][0]] = self.FuncOpenFile
        self.__funcHander[TOP_LEVEL_TREE_KEYS[USR_LABEL] + CHILD_ITEM_KEYS[USR_LABEL][1]] = self.FuncChangeLabelImage
        self.__funcHander[TOP_LEVEL_TREE_KEYS[USR_LABEL] + CHILD_ITEM_KEYS[USR_LABEL][2]] = self.OnUsrLabelImage
        self.__funcHander[TOP_LEVEL_TREE_KEYS[USR_LABEL] + CHILD_ITEM_KEYS[USR_LABEL][3]] = self.OnPackageSample

        # Step3 : train
        self.__funcHander[TOP_LEVEL_TREE_KEYS[TRAIN] + CHILD_ITEM_KEYS[TRAIN][0]] = self.FuncOpenFile
        self.__funcHander[TOP_LEVEL_TREE_KEYS[TRAIN] + CHILD_ITEM_KEYS[TRAIN][2]] = self.OnTrain
        self.__funcHander[TOP_LEVEL_TREE_KEYS[TRAIN] + CHILD_ITEM_KEYS[TRAIN][3]] = self.OnTrainResult

        # Step4 : UI explore result
        self.__funcHander[TOP_LEVEL_TREE_KEYS[EXPLORE_RESULT] + CHILD_ITEM_KEYS[EXPLORE_RESULT][0]] = self.FuncOpenFile
        self.__funcHander[TOP_LEVEL_TREE_KEYS[EXPLORE_RESULT] + CHILD_ITEM_KEYS[EXPLORE_RESULT][1]] = self.OnUIGraph
        self.__funcHander[TOP_LEVEL_TREE_KEYS[EXPLORE_RESULT] + CHILD_ITEM_KEYS[EXPLORE_RESULT][2]] = self.OnCoverage
        self.__funcHander[TOP_LEVEL_TREE_KEYS[EXPLORE_RESULT] + CHILD_ITEM_KEYS[EXPLORE_RESULT][3]] = self.OnUICoverage

    def InitAction(self):
        self.__actionAddImg = QAction(self.__ui.mainWindow)
        self.__actionAddImg.setText("增加图片")

        self.__actionAddImg.triggered.connect(self.onActionAddUsrImage)

        self.__actionChgImg = QAction(self.__ui.mainWindow)
        self.__actionChgImg.setText("替换图片")
        self.__actionChgImg.triggered.connect(self.onActionChgUsrImage)

        self.__actionDelImg = QAction(self.__ui.mainWindow)
        self.__actionDelImg.setText("删除图片")
        self.__actionDelImg.triggered.connect(self.onActionDelUsrImage)

        self.__actionDelDir = QAction(self.__ui.mainWindow)
        self.__actionDelDir.setText("删除目录")
        self.__actionDelDir.triggered.connect(self.onActionDelUsrDir)

        self.__addSampleFolder = QAction(self.__ui.mainWindow)
        self.__addSampleFolder.setText("增加目录")
        self.__addSampleFolder.triggered.connect(self.onActionAddFolder)

    def onRightClick(self):
        try:
            self.__logger.debug("UI Explore on right click")
            item = self.__ui.treeWidget.currentItem()
            key = item.text(0)
            type = item.text(2)
            self.__logger.debug("item 0 {} item 2 {}".format(item.text(0), item.text(2)))
            self.__rightMenu.clear()

            if key in []:
                self.__rightMenu.addAction(self.__addSampleFolder)
            if item.text(2) == ITEM_TYPE_IMAGE:
                self.__rightMenu.addAction(self.__actionChgImg)
                self.__rightMenu.addAction(self.__actionDelImg)

            elif item.text(2) == ITEM_TYPE_IMAGE_FLODER:
                self.__rightMenu.addAction(self.__actionAddImg)
                self.__rightMenu.addAction(self.__actionDelDir)

            # CHILD_ITEM_KEYS[1][1], '样本修改'
            elif item.text(0) in [CHILD_ITEM_KEYS[1][1]]:
                self.__rightMenu.addAction(self.__addSampleFolder)

            # todo, add action first and exe right Mune
            self.__rightMenu.exec_(QCursor.pos())

            # reset current  item None
            self.__ui.treeWidget.setCurrentItem(None)

        except Exception as e:
            self.__logger.error(e)

    def onActionAddUsrImage(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.AddUsrImage()
        except Exception as e:
            self.__logger.error(e)
        
    def onActionChgUsrImage(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.ChgUsrImage()
        except Exception as e:
            self.__logger.error(e)

    def onActionDelUsrImage(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.DelUsrImage()
        except Exception as e:
            self.__logger.error(e)

    def onActionDelUsrDir(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.DelUsrDir()
        except Exception as e:
            self.__logger.error(e)

    def onActionAddFolder(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.AddFolder()
        except Exception as e:
            self.__logger.error(e)

    def OnClickImageItem(self):
        item = self.__ui.treeWidget.currentItem()
        imgPath = item.text(3)
        self.__logger.debug("imgPath is {}".format(imgPath))
        labelImageList = self.__usrLabelImage.GetImageList()
        if imgPath not in labelImageList:
            labelImageList.append(imgPath)
            self.__usrLabelImage.SetImageList(labelImageList)

        try:
            labelImageIndex = labelImageList.index(imgPath)
            self.__usrLabelImage.SetImageIndex(labelImageIndex)
            self.__logger.info("image list len is {}, index is {} ".format(len(labelImageList), labelImageIndex))
            self.__canvas.resetState()
            self.__canvas.addUIGraph(None)
            # print("labelImageList is {}".format(labelImageList))
            fileName = labelImageList[labelImageIndex]
            LoadLabelImage(self.__canvas, self.__zoomWidget, self.__ui, fileName)
            # self.LoadLabelImage()

            self.__canvas.setTreeWidget(self.__ui.treeWidget)
            self.__canvas.setUI(self.__ui)

            self.__ui.pushButton_prev.setEnabled(True)
            self.__ui.pushButton_next.setEnabled(True)
        except Exception as error:
            self.__logger.error("find image {} faild error {}".format(imgPath, error))

    def OnTreeClicked(self):
        try:
            self._ResetState()
            item = self.__ui.treeWidget.currentItem()
            key = item.text(0)

            # top Level
            if key in TOP_LEVEL_TREE_KEYS:
                self.__logger.info("key in top level tree")
                return

            type = item.text(2)
            self.__logger.debug("type is {}".format(type))
            if type in [ITEM_TYPE_IMAGE]:
                self.OnClickImageItem()
                return

            # childKeys
            parent = item.parent()
            if parent.text(0) in TOP_LEVEL_TREE_KEYS:
                # self.__logger.error("key {} not in trees".format(parent.text(0)))
                # return

                pKey = parent.text(0)
                self.__logger.info("on tree click {}....".format(key + pKey))
                self.__mode = TOP_LEVEL_TREE_KEYS.index(pKey)
                self.__funcHander[pKey+key]()
                self.__logger.info("key is {}".format(key))
                if key in PATH_NAME_LIST:
                    if self.__mode in [AUTO_LABEL]:
                        item.setText(1, self.__autoLabelPath)
                    elif self.__mode in [USR_LABEL]:
                        item.setText(1, self.__usrLabelPath)
                    elif self.__mode in [TRAIN]:
                        item.setText(1, self.__trainSamplePath)
                    elif self.__mode in [EXPLORE_RESULT]:
                        item.setText(1, self.__exploreRetPath)
            # elif key in TRAIN_PARAMS.keys():
            #     # item.setText(1, )
            #     TRAIN_PARAMS[key] = item.text(1)
            #     print("change value {} as {}".format(key, TRAIN_PARAMS[key]))

        except Exception as e:
            self.__logger.error(e)

    def FuncOpenFile(self):
        try:
            FileDialog = QFileDialog()
            FileDialog.setFileMode(QFileDialog.Directory)
            FileDialog.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            if FileDialog.exec():
                directory = FileDialog.selectedFiles()[0]
                self.__logger.debug("open fild name {}".format(directory))
                if directory == "":
                    return
            else:
                return

            # if image in folder, normalize it
            NormFolderImage(directory)

            if self.__mode in [AUTO_LABEL]:
                self.__autoLabelPath = directory
            elif self.__mode in [USR_LABEL]:
                self.__usrLabelPath = directory
                self.__logger.debug("usr label path is {}".format(self.__usrLabelPath))
                ClearTreeItem(self.__UsrLabelSampleTree)
                GetFileList(self.__usrLabelPath, self.__UsrLabelSampleTree, 1)

            elif self.__mode in [TRAIN]:
                self.__trainSamplePath = directory
            elif self.__mode in [EXPLORE_RESULT]:
                self.__exploreRetPath = directory

            return
        except Exception as e:
            self.__logger.error(e)

    def OnAutoLabelImage(self):
        try:
            self.__autoLabelImage.SetPath(self.__autoLabelPath)
            self.__autoLabelImage.Label()
        except Exception as e:
            self.__logger.error(e)

    def FuncChangeLabelImage(self):
        try:
            self.__logger.debug("FunChangeLabelImage")
        except Exception as e:
            self.__logger.error(e)

    def OnUsrLabelImage(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.UsrLabelImage()
        except Exception as e:
            self.__logger.error(e)

    def OnPackageSample(self):
        try:
            self.__usrLabelImage.SetPath(self.__usrLabelPath)
            self.__usrLabelImage.PackageSample()
        except Exception as e:
            self.__logger.error(e)

    def OnTrain(self):
        try:
            self.__trainSample.SetSamplePath(self.__trainSamplePath)
            for index in range(self.__trainItem.childCount()):
                item = self.__trainItem.child(index)
                if item.text(0) == CHILD_ITEM_KEYS[2][1]:
                    for subIndex in range(item.childCount()):
                        subItem = item.child(subIndex)
                        TRAIN_PARAMS[subItem.text(0)] = subItem.text(1)
            self.__logger.info("train params {}".format(TRAIN_PARAMS))

            self.__trainSample.SetTrainParam(TRAIN_PARAMS)
            self.__trainSample.Run()
        except Exception as e:
            self.__logger.error(e)

    def OnTrainResult(self):
        try:
            self.__trainSample.SetSamplePath(self.__trainSamplePath)
            self.__trainSample.AnalyseResult()
        except Exception as e:
            self.__logger.error(e)

    def OnUIGraph(self):
        try:
            self.__ExploreResult.SetPath(self.__exploreRetPath)
            self.__ExploreResult.UIGraph()
        except Exception as e:
            self.__logger.error(e)

    def OnCoverage(self):
        try:
            self.__ExploreResult.SetPath(self.__exploreRetPath)
            self.__ExploreResult.Coverage()
        except Exception as e:
            self.__logger.error(e)

    def OnUICoverage(self):
        try:
            self.__ExploreResult.SetPath(self.__exploreRetPath)
            self.__ExploreResult.UICoverage()
        except Exception as e:
            self.__logger.error(e)

    def GetUsrLabelImgList(self):
        try:
            return self.__usrLabelImage.GetImageList()
        except Exception as e:
            self.__logger.error(e)

    def GetUsrLabelImgIndex(self):
        try:
            return self.__usrLabelImage.GetImageIndex()
        except Exception as e:
            self.__logger.error(e)

    def _ResetState(self):
        self.__ExploreResult.Reset()
        self.__canvas.resetState()
        self.__canvas.addUIGraph(None)

    def Finish(self):
        self.__trainSample.FinishTrain()

    def _IsIntNumber(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def OnItemValueChg(self, currentItem, column):
        print("value chg {}-->{}".format(currentItem.text(0), currentItem.text(1)))
        if currentItem.text(0) in int_Number_Key:
            if self._IsIntNumber(currentItem.text(column)) is False:
                currentItem.setText(1, str(0))
                self.__logger.error("{} should be number".format(currentItem.text(0)))
                dlg = confirmDialog(text="请填入整数", parent=self)
                dlg.popUp()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = UIExplore()
    sys.exit(app.exec_())