# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import shutil
import logging
import numpy as np
import cv2

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog, QTreeWidgetItem
from PyQt5.QtGui import QIcon, QPixmap

from .define import ITEM_TYPE_IMAGE, ITEM_TYPE_IMAGE_FLODER
from ....dialog.tip_dialog import show_warning_tips
from ....utils import get_file_list, make_tar_gz


class UsrLabelImage(object):
    def __init__(self, usr_label_path, canvas, ui):
        self.__usr_label_path = usr_label_path
        self.__logger = logging.getLogger('sdktool')
        # self.__zoomWidget = zoomWidget
        self.__canvas = canvas
        self.__ui = ui
        self.__image_list = []
        self.__image_index = 0

    def set_path(self, path):
        self.__usr_label_path = path

    def get_image_list(self):
        return self.__image_list

    def set_image_list(self, image_list):
        self.__image_list = image_list

    @property
    def image_list(self):
        return self.__image_list

    def get_image_index(self):
        return self.__image_index

    def set_image_index(self, index):
        self.__image_index = index

    def acc_image_index(self):
        self.__image_index += 1
        self.__image_index = min(len(self.__image_list) - 1, self.__image_index)

    def dec_image_index(self):
        self.__image_index -= 1
        self.__image_index = max(self.__image_index, 0)

    def get_cur_image_name(self):
        cnt = len(self.__image_list)
        if self.__image_index < cnt and cnt > 0:
            return self.__image_list[self.__image_index]
        return None

    def _check_valid(self, name):
        item = self.__ui.tree_widget_left.currentItem()
        for index in range(item.childCount()):
            childItem = item.child(index)
            self.__logger.debug("text %s name %s", childItem.text(0), name)
            if childItem.text(0) == name:
                return False
        return True

    def add_usr_image(self):
        try:
            item = self.__ui.tree_widget_left.currentItem()
            image_path, _ = QFileDialog.getOpenFileName(None, "选择文件", None, "*.*")

            # read image and judge is empty
            self.__logger.debug("image path is %s", image_path)

            # image = cv2.imread(imagePath)
            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                show_warning_tips("加入图片错误")
            else:
                folder = item.text(3)
                _, file_name = os.path.split(image_path)
                new_path = os.path.join(folder, file_name)
                cv2.imwrite(new_path, image)

                child = QTreeWidgetItem()
                if self._check_valid(file_name):
                    # 0: image file name, 2:type, 3:image path
                    child.setText(0, file_name)
                    child.setText(2, ITEM_TYPE_IMAGE)
                    child.setText(3, new_path)
                    icon = QIcon()
                    icon.addPixmap(QPixmap(":/menu/image-gallery.png"), QIcon.Normal, QIcon.Off)
                    child.setIcon(0, icon)
                    item.addChild(child)
                else:
                    show_warning_tips("图像{}已存在，请检查".format(file_name))

        except RuntimeError as error:
            self.__logger.error("add usr image failed, error %s", error)

    def chg_usr_image(self):
        try:
            self.__logger.info("ActionChgUsrImage")
            item = self.__ui.tree_widget_left.currentItem()
            image_path = item.text(3)
            self.__logger.debug("image path is %s", image_path)
            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)

            # whether clicked image is right
            if image is None:
                show_warning_tips("读取图片失败")
                return

            # selected a new image
            new_img_path, _ = QFileDialog.getOpenFileName(None, "选择图片", None, "*.*")
            if new_img_path == "":
                return
            new_image = cv2.imdecode(np.fromfile(new_img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            # newImage = cv2.imread(newImgPath)
            if new_image is None:
                show_warning_tips("读取图片失败")
                return

            # write new image
            cv2.imwrite(image_path, new_image)

        except RuntimeError as error:
            self.__logger.error("change image failed, error %s", error)

    def del_usr_image(self):
        try:
            self.__logger.info("add action ActionDelUsrImag")
            item = self.__ui.tree_widget_left.currentItem()
            image_path = item.text(3)

            if not os.path.exists(image_path):
                show_warning_tips("图片不存在")
                return

            os.remove(image_path)
            self.__logger.info("remove image path %s", image_path)

            # reomve current item node
            parent = item.parent()
            parent.removeChild(item)

            # find suffix string
            index = image_path.rfind('.')
            if index == -1:
                self.__logger.info("find json file to image %s failed", image_path)
                return

            for postfix in ['json', 'xml']:
                # build postfix path, and remove file
                target_file = "%s.%s" % (image_path[0:index], postfix)
                self.__logger.debug("%s Path is %s", postfix, target_file)

                if os.path.exists(target_file):
                    os.remove(target_file)

        except RuntimeError as error:
            self.__logger.error("change image failed, error %s", error)

    def del_usr_dir(self):
        try:
            self.__logger.info("add action ActionDelUsrDir")
            item = self.__ui.tree_widget_left.currentItem()
            floder_dir = item.text(3)

            if not os.path.exists(floder_dir):
                show_warning_tips("目录不存在")
                return

            shutil.rmtree(floder_dir)

            # os.remove(imagePath)
            self.__logger.info("remove image path %s", floder_dir)

            # remove current item node
            parent = item.parent()
            parent.removeChild(item)

        except RuntimeError as error:
            self.__logger.error("remove folder failed, error %s", error)

    def add_folder(self):
        try:
            self.__logger.info("add action sample folder")
            dlg = QFileDialog()
            dlg.setFileMode(QFileDialog.Directory)
            dlg.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
            if dlg.exec():
                # get folder name
                folder_name = dlg.selectedFiles()[0]
                self.__logger.debug("open file name %s", folder_name)
                if folder_name == "":
                    return

                if False in [os.path.isdir(folder_name), os.path.isdir(self.__usr_label_path)]:
                    self.__logger.error("%s or %s is not directory", folder_name, self.__usr_label_path)
                    return

                # if image in folder, normalize it
                # NormFolderImage(folderName)
                # build new and remove dst path
                _, name = os.path.split(folder_name)

                if self._check_valid(name):
                    dst_path = os.path.join(self.__usr_label_path, name)
                    if os.path.exists(dst_path):
                        self.__logger.info("remove tree %s", dst_path)
                        shutil.rmtree(dst_path)

                    # copy folder
                    shutil.copytree(folder_name, dst_path)

                    item = self.__ui.tree_widget_left.currentItem()
                    child = QTreeWidgetItem()
                    child.setText(0, name)
                    child.setText(2, ITEM_TYPE_IMAGE_FLODER)
                    child.setText(3, dst_path)
                    icon = QIcon()
                    icon.addPixmap(QPixmap(":/menu/file.png"), QIcon.Normal, QIcon.Off)
                    child.setIcon(0, icon)
                    get_file_list(dst_path, child, 1)
                    item.addChild(child)
                else:
                    show_warning_tips("文件夹{}已存在，请检查".format(name))
                    dlg.popUp()

        except RuntimeError as error:
            self.__logger.info("change image failed, error %s", error)

    def package_sample(self):
        """ 打包样本

        :return:
        """
        try:
            name = "{}.tar".format(self.__usr_label_path)
            self.__logger.debug("outFile %s source File %s", name, self.__usr_label_path)
            make_tar_gz(name, self.__usr_label_path)
            rest_str = "success, 保存路径：{}".format(name)
        except RuntimeError as e:
            rest_str = "打包错误，原因：{}".format(e)
        show_warning_tips(rest_str)
