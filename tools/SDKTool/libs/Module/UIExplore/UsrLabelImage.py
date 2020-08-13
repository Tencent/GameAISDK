# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import cv2
import shutil
import logging
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from libs.CommonDialog import *
from libs.utils import GetFileList, MakeTargz, NormFolderImage
from libs.Module.UIExplore.canvasUtils import LoadLabelImage
from define import ITEM_TYPE_IMAGE, ITEM_TYPE_IMAGE_FLODER


class UsrLabelImage(object):
    def __init__(self, usrLabelPath, canvas, zoomWidget, ui):
        self.__usrLabelPath = usrLabelPath
        self.__logger = logging.getLogger('sdktool')
        self.__zoomWidget = zoomWidget
        self.__canvas = canvas
        self.__ui = ui
        self.__imageList = []
        self.__imageIndex = -1

    def SetPath(self, path):
        self.__usrLabelPath = path

    def GetImageList(self):
        return self.__imageList

    def SetImageList(self, imageList):
        self.__imageList = imageList

    def GetImageIndex(self):
        return self.__imageIndex

    def SetImageIndex(self, index):
        self.__imageIndex = index

    def _CheckValid(self, name):
        item = self.__ui.treeWidget.currentItem()
        # parent = item.parent()
        for index in range(item.childCount()):
            childItem = item.child(index)
            self.__logger.debug("text {} name {}".format(childItem.text(0), name))
            if childItem.text(0) == name:
                return False
        return True

    def AddUsrImage(self):
        try:
            item = self.__ui.treeWidget.currentItem()
            imagePath, _ = QFileDialog.getOpenFileName(None, "选择文件", None, "*.*")

            # read image and judge is empty
            self.__logger.debug("image path is {}".format(imagePath))

            # image = cv2.imread(imagePath)
            image = cv2.imdecode(np.fromfile(imagePath, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                dlg = CommonDialog(text="加入图片错误")
                dlg.popUp()
            else:
                folder = item.text(3)
                _, fileName = os.path.split(imagePath)
                newPath = os.path.join(folder, fileName)
                cv2.imwrite(newPath, image)

                # normlize image to 720P
                NormFolderImage(newPath)

                child = QTreeWidgetItem()
                if self._CheckValid(fileName):
                    # 0: image file name, 2:type, 3:image path
                    child.setText(0, fileName)
                    child.setText(2, ITEM_TYPE_IMAGE)
                    child.setText(3, newPath)
                    icon = QIcon()
                    icon.addPixmap(QPixmap(":/menu/image.jpg"), QIcon.Normal, QIcon.Off)
                    child.setIcon(0, icon)
                    item.addChild(child)
                else:
                    dlg = CommonDialog(text="图像{}已存在，请检查".format(fileName))
                    dlg.popUp()

        except Exception as error:
            self.__logger.info("add usr image failed, error {}".format(error))

    def ChgUsrImage(self):
        try:
            self.__logger.info("ActionChgUsrImage")
            item = self.__ui.treeWidget.currentItem()
            imagePath = item.text(3)
            self.__logger.debug("image path is {}".format(imagePath))
            image = cv2.imdecode(np.fromfile(imagePath, dtype=np.uint8), cv2.IMREAD_COLOR)
            # image = cv2.imread(imagePath)

            # whether clicked image is right
            if image is None:
                dlg = CommonDialog(text="读取图片失败")
                dlg.popUp()
                return

            # selected a new image
            newImgPath, _ = QFileDialog.getOpenFileName(None, "选择图片", None, "*.*")
            newImage = cv2.imdecode(np.fromfile(newImgPath, dtype=np.uint8), cv2.IMREAD_COLOR)
            # newImage = cv2.imread(newImgPath)
            if newImage is None:
                dlg = CommonDialog(text="读取图片失败")
                dlg.popUp()
                return

            # write new image
            cv2.imwrite(imagePath, newImage)

        except Exception as error:
            self.__logger.info("change image failed, error {}".format(error))

    def DelUsrImage(self):
        try:
            self.__logger.info("add action ActionDelUsrImag")
            item = self.__ui.treeWidget.currentItem()
            imagePath = item.text(3)

            if not os.path.exists(imagePath):
                dlg = CommonDialog(text="图片不存在")
                dlg.popUp()
                return

            os.remove(imagePath)
            self.__logger.info("remove image path {}".format(imagePath))

            # reomve current item node
            parent = item.parent()
            parent.removeChild(item)

            # find suffix string
            index = imagePath.rfind('.')
            if index == -1:
                self.__logger.info("find json file to image {} failed".format(imagePath))
                return

            # build json path, and remove json file
            jsonPath = imagePath[0:index] + '.json'
            self.__logger.debug("json Path is {}".format(jsonPath))

            if os.path.exists(jsonPath):
                os.remove(jsonPath)

        except Exception as error:
            self.__logger.info("change image failed, error {}".format(error))

    def DelUsrDir(self):
        try:
            self.__logger.info("add action ActionDelUsrDir")
            item = self.__ui.treeWidget.currentItem()
            floderDir = item.text(3)

            if not os.path.exists(floderDir):
                dlg = CommonDialog(text="目录不存在")
                dlg.popUp()
                return

            shutil.rmtree(floderDir)

            # os.remove(imagePath)
            self.__logger.info("remove image path {}".format(floderDir))

            # remove current item node
            parent = item.parent()
            parent.removeChild(item)

        except Exception as error:
            self.__logger.info(" remove folder failed, error {}".format(error))

    def AddFolder(self):
        try:
            self.__logger.info("add action sample folder")
            dlg = QFileDialog()
            dlg.setFileMode(QFileDialog.Directory)
            dlg.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            if dlg.exec():
                # get folder name
                folderName = dlg.selectedFiles()[0]
                self.__logger.debug("open fild name {}".format(folderName))
                if folderName == "":
                    return

                if False in [os.path.isdir(folderName), os.path.isdir(self.__usrLabelPath)]:
                    self.__logger.error("{} or {} is not directory".format(folderName, self.__usrLabelPath))
                    return

                # if image in folder, normalize it
                NormFolderImage(folderName)

                # build new and remove dst path
                _, name = os.path.split(folderName)

                if self._CheckValid(name):
                    dstPath = os.path.join(self.__usrLabelPath, name)
                    if os.path.exists(dstPath):
                        self.__logger.info("remove tree {}".format(dstPath))
                        shutil.rmtree(dstPath)

                    # copy folder
                    shutil.copytree(folderName, dstPath)

                    item = self.__ui.treeWidget.currentItem()
                    child = QTreeWidgetItem()
                    child.setText(0, name)
                    child.setText(2, ITEM_TYPE_IMAGE_FLODER)
                    child.setText(3, dstPath)
                    icon = QIcon()
                    icon.addPixmap(QPixmap(":/menu/floder.jpg"), QIcon.Normal, QIcon.Off)
                    child.setIcon(0, icon)
                    GetFileList(dstPath, child, 1)
                    item.addChild(child)
                else:
                    dlg = CommonDialog(text="文件夹{}已存在，请检查".format(name))
                    dlg.popUp()

        except Exception as error:
            self.__logger.info("change image failed, error {}".format(error))

    def UsrLabelImage(self):
        self.__logger.info("begin label....")
        #labelImageIndex = 0
        # indexFlag = True
        for root, dirs, files in os.walk(self.__usrLabelPath):
            for file in files:
                if os.path.splitext(file)[1] in [".png", ".bmp", ".jpg"]:
                    path = os.path.join(root, file)
                    if path not in self.__imageList:
                        self.__imageList.append(path)

        if len(self.__imageList) <= 0:
            dialog = CommonDialog("LabelImage", "no image in fold {}, please check".format(self.__usrLabelPath))
            dialog.popUp()
            return

        self.__canvas.resetState()
        self.__canvas.addUIGraph(None)
        fileName = self.__imageList[0]
        LoadLabelImage(self.__canvas, self.__zoomWidget, self.__ui, fileName)

        self.__canvas.setTreeWidget(self.__ui.treeWidget)
        self.__canvas.setUI(self.__ui)

        self.__ui.pushButton_prev.setEnabled(True)
        self.__ui.pushButton_next.setEnabled(True)
        return

    def PackageSample(self):
        try:
            name = "{}.tar".format(self.__usrLabelPath)
            self.__logger.debug("outFile {} source File {}".format(name, self.__usrLabelPath))
            MakeTargz(name, self.__usrLabelPath)
            restStr = "success, 保存路径：{}".format(name)
        except Exception as e:
            restStr = "打包错误，原因：{}".format(e)

        dlg = CommonDialog(title="package", text=restStr)
        dlg.popUp()

