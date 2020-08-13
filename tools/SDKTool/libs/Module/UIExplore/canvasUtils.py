# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import traceback


from libs.shape import *
from libs.JsonToRefineDetTxt import *
from libs.utils import *
from libs.Module.UIExplore.define import *


def PaintImage(imgPath, canvas, zoomWidget, ui):
    canvas.resetState()
    if imgPath == "" or imgPath is None:
        raise Exception('wrong imgPath: {}'.format(imgPath))
    try:
        if not os.path.exists(imgPath):
            raise Exception("there is no file {}".format(imgPath))

        frame = QImage(imgPath)
        if canvas.uiGraph is not None:
            scaleW, scaleH = canvas.uiGraph.GetWindowScale()
            frame = frame.scaled(frame.width() * scaleW, frame.height() * scaleH)
        # self.image = frame
        pix = QPixmap.fromImage(frame)
        canvas.loadPixmap(pix)
        canvas.setEnabled(True)
        AdjustScale(canvas, zoomWidget, ui)
        paintCanvas(canvas, zoomWidget)
    except Exception as e:
        raise Exception('read image failed, imgPath: {}, traceback {}'.format(imgPath, traceback.format_exc()))


# canvas, zoomWidget
def AdjustScale(canvas, zoomWidget, ui):
    value = scaleFitWindow(canvas, ui)  # 相当于执行self.scaleFitWindow()
    if canvas.uiGraph:
        (scaleX, scaleY) = canvas.uiGraph.GetWindowScale()
        value = value * max(scaleX, scaleY)
    zoomWidget.setValue(int(100 * value))


 # canvas,
def LoadLabelJson(labelImageName, sceneItem, labelsItem, canvas):
    # 清除画布的一些数据
    canvas.shapeItem.clear()
    canvas.itemShape.clear()

    # 读取json文件
    labelJsonPath = labelImageName[:labelImageName.rfind('.')] + ".json"
    if os.path.exists(labelJsonPath) is False:
        return

    try:
        with open(labelJsonPath, 'r') as f:
            labelJsonDict = json.load(f)
    except Exception as e:
        raise (e)

    sceneName = labelJsonDict["scene"]
    # self.__ui.treeWidget.topLevelItem(1).setText(1, sceneName)
    sceneItem.setText(1, sceneName)

    # 对每个label，读取其内容并展示在画布上
    for labelShape in labelJsonDict["labels"]:
        labelText = labelShape["label"]
        # labelName = labelShape["name"]
        if "clickNum" in labelShape.keys():
            labelClickNum = int(labelShape["clickNum"])
        else:
            labelClickNum = 0
        canvas.labelDialog.addLabelHistory(labelText)
        treeLabelItem = None
        labelFlag = False
        # labelTreeItem = labelsItem.topLevelItem(2)
        labelTreeItem = labelsItem
        for itemIndex in range(labelTreeItem.childCount()):
            treeItem = labelTreeItem.child(itemIndex)
            if treeItem.text(0) == labelText:
                labelFlag = True
                treeLabelItem = treeItem
                break

        if labelFlag is False:
            treeLabelItem = CreateTreeItem(key=labelText)
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
            raise Exception("{} file is wrong".format(labelJsonPath))

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
        canvas.shapes.append(shape)
        canvas.shapeItem[shape] = treeLabelItem
        if labelText not in canvas.itemShape.keys():
            canvas.itemShape[labelText] = list()
        canvas.itemShape[labelText].append(shape)


    # canvas, zoomWidget
def paintCanvas(canvas, zoomWidget):
    # assert not self.image.isNull(), "cannot paint null image"
    canvas.scale = 0.01 * zoomWidget.value()
    canvas.adjustSize()
    canvas.update()


def scaleFitWindow(canvas, ui):
    # e = 2.0  # So that no scrollbars are generated.
    e = 0.0
    w1 = ui.scroll.width() - e
    h1 = ui.scroll.height() - e
    a1 = w1 / h1

    # Calculate a new scale value based on the pixmap's aspect ratio.
    if canvas.pixmap is not None:
        w2 = canvas.pixmap.width() - 0.0
        h2 = canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2
    else:
        return 1


def LoadLabelImage(canvas, zoomWidget, ui, fileName):
    if not os.path.exists(fileName):
        raise Exception("image {} is not exist".format(fileName))

    # print("label image index is {}, file name is {}".format(labelImageIndex, fileName))
    PaintImage(fileName, canvas, zoomWidget, ui)
    labelItem = GetLabelImageItem(ui)

    if labelItem is None:
        return

    for index in range(labelItem.childCount()):
        labelItem.takeChild(0)

    fileNameItem = CreateTreeItem(key='fileName', value=fileName)
    fileNameItem.setText(1, os.path.basename(fileName))
    fileNameItem.setText(2, fileName)
    labelItem.addChild(fileNameItem)

    sceneItem = CreateTreeItem(key='scene', edit=True)
    labelItem.addChild(sceneItem)

    labelsItem = CreateTreeItem(key='labels')
    labelItem.addChild(labelsItem)
    labelItem.setExpanded(True)

    LoadLabelJson(fileName, sceneItem, labelsItem, canvas)
    canvas.setLabel()
    canvas.labelFlag = True


def GetLabelImageItem(ui):
    labelImageItem = None
    for itemIdx in range(ui.treeWidget.topLevelItemCount()):
        childItem = ui.treeWidget.topLevelItem(itemIdx)
        if childItem.text(0) == UI_USR_LABEL_NAME:
            labelImageItem = childItem
    try:
        for itemIdx in range(labelImageItem.childCount()):
            item = labelImageItem.child(itemIdx)
            if item.text(0) == USR_LABEL_ITEM_NAME:
                return item

    except Exception as e:
        raise Exception("find item {} failed".format(USR_LABEL_ITEM_NAME))