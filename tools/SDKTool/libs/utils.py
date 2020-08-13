'''
    代码链接：https://github.com/tzutalin/labelImg/tree/master/libs
'''

from math import sqrt
import hashlib
import os
import re
import sys
import cv2
import tarfile
import shutil
import numpy as np


from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from define import *
from libs.ustr import ustr


def newIcon(icon):
    return QIcon(':/' + icon)


def newButton(text, icon=None, slot=None):
    b = QPushButton(text)
    if icon is not None:
        b.setIcon(newIcon(icon))
    if slot is not None:
        b.clicked.connect(slot)
    return b


def newAction(parent, text, slot=None, shortcut=None, icon=None,
              tip=None, checkable=False, enabled=True):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QAction(text, parent)
    if icon is not None:
        a.setIcon(newIcon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    return a


def addActions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)


def labelValidator():
    return QRegExpValidator(QRegExp(r'^[^ \t].+'), None)


class struct(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())


def fmtShortcut(text):
    mod, key = text.split('+', 1)
    return '<b>%s</b>+<b>%s</b>' % (mod, key)


def generateColorByText(text):
    s = ustr(text)
    hashCode = int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16)
    r = int((hashCode / 255) % 255)
    g = int((hashCode / 65025)  % 255)
    b = int((hashCode / 16581375)  % 255)
    return QColor(r, g, b, 100)

def have_qstring():
    '''p3/qt5 get rid of QString wrapper as py3 has native unicode str type'''
    return not (sys.version_info.major >= 3 or QT_VERSION_STR.startswith('5.'))

def util_qt_strlistclass():
    return QStringList if have_qstring() else list

def natural_sort(list, key=lambda s:s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)


def GetFileList(dir, treeItem, level):
    if treeItem is None:
        print("GetFileList failed, treeItem is None")
        # self.__logger.error("GetFileList failed, treeItem is None")
        return

    if dir is None or dir == "":
        print("GetFileList failed, dir is {}".format(dir))
        # self.__logger.error("GetFileList failed, dir is {}".format(dir))
        return

    # 获取文件名
    child = QTreeWidgetItem()
    filePath = dir
    _, fileName = os.path.split(filePath)
    # child.setText(0, fileName)
    if level > 1:
        # 过滤某些特定文件
        if fileName in ["project.json", "task.json~", "project.json~"]:
            return

        # print("file name {}".format(fileName))
        # 创建树的节点，根据后缀名类型的不同来设置不同的icon
        extension = os.path.splitext(fileName)[1]
        if extension in [".jpg", ".png", ".bmp"]:
            print("dir {} file name is {}".format(dir, fileName))
            child.setText(0, fileName)
            child.setText(2, ITEM_TYPE_IMAGE)
            child.setText(3, dir)

            icon = QIcon()
            icon.addPixmap(QPixmap(":/menu/image.jpg"), QIcon.Normal, QIcon.Off)
            child.setIcon(0, icon)
            treeItem.addChild(child)

        elif extension in ["", ".0", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9"]:
            print("dir {} file name is {}".format(dir, fileName))
            child.setText(0, fileName)
            child.setText(2, ITEM_TYPE_IMAGE_FLODER)
            child.setText(3, dir)

            icon = QIcon()
            icon.addPixmap(QPixmap(":/menu/floder.jpg"), QIcon.Normal, QIcon.Off)
            child.setIcon(0, icon)
            treeItem.addChild(child)

        elif extension in [".json"]:
            return

    # 若dir为目录，则递归
    if os.path.isdir(dir):
        child.setText(0, fileName)
        child.setText(2, ITEM_TYPE_IMAGE_FLODER)
        child.setText(3, dir)
        # treeItem.addChild(child)

        for s in os.listdir(dir):
            newDir=os.path.join(dir, s)
            if level > 1:
                GetFileList(newDir, child, level + 1)
            else:
                GetFileList(newDir, treeItem, level + 1)


def CreateTreeItem(key, value=None, type=None, edit=False):
    child = QTreeWidgetItem()
    child.setText(0, str(key))

    if value is not None:
        child.setText(1, str(value))

    if type is not None:
        child.setText(2, type)
    if edit is True:
        child.setFlags(child.flags() | Qt.ItemIsEditable)

    return child


def ClearTreeItem( item):
    print("count is {}".format(item.childCount()))
    for itemIndex in range(item.childCount()):
        try:
            print("index {} take child {}".format(itemIndex, item.child(0).text(0)))
            item.takeChild(0)
        except Exception as error:
            raise ("error is {}".format(error))


def MakeTargz(outputFile, sourceFile):
    if None in [outputFile, sourceFile]:
        raise ("failed: input file or output file is None")
    if not os.path.exists(sourceFile):
        raise ("failed: source file {} is not exists".format(sourceFile))

    with tarfile.open(outputFile, "w:gz") as tar:
        tar.add(sourceFile, arcname=os.path.basename(sourceFile))
        return True


def GetfilesCount(dirName, formatList=None):
    if formatList is None:
        formatList = [".png", ".bmp", ".jpg"]

    file_count = 0
    for dirPath, dirNames, fileNames in os.walk(dirName):
        for file in fileNames:
            if os.path.splitext(file)[1] in formatList:
                file_count = file_count + 1

    return file_count


def DelFiles(objDir):
    for root, dirs, files in os.walk(objDir):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            # os.rmdir(folder): folder must be empty
            shutil.rmtree(os.path.join(root, name))


def NormaImage(srcPath, dstPath):
    if os.path.isfile(srcPath):
        extension = os.path.splitext(srcPath)[1]
        if extension not in [".jpg", ".png", ".bmp", ".jpeg"]:
            raise Exception("{} is not image".format(srcPath))

        image = cv2.imdecode(np.fromfile(srcPath, dtype=np.uint8), cv2.IMREAD_COLOR)
        width = image.shape[1]
        height = image.shape[0]
        
        scaleW = 1.0
        scaleH = 1.0
        if width > height:
            scaleW = width / 1280
            scaleH = height / 720
        else:
            scaleW = width / 720
            scaleH = height / 1280

        if scaleW != scaleH:
            raise Exception("image {} width/height not equal to 16:9 or 9:16, current width/height: {}/{}".format(
                srcPath, width, height))

        elif scaleW != 1:
            image = cv2.resize(image, (int(width/scaleW), int(height/scaleH)))
            cv2.imwrite(dstPath, image)
            # overwrite srcPath
            cv2.imwrite(srcPath, image)

        else:
            cv2.imwrite(dstPath, image)


def NormFolderImage(path):
    for dirPath, _, files in os.walk(path):
        for file in files:
            try:
                path = os.path.join(dirPath, file)
                NormaImage(path, path)
            except Exception as error:
                print("error is {}".format(error))
                continue




