# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import json
import math
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


from PyQt5.QtCore import *

from libs.Graph import UIGraph, UIGRAPH
from libs.CommonDialog import *
from libs.Module.UIExplore.canvasUtils import PaintImage


platform = sys.platform


class ExploreResult(object):
    def __init__(self, canvas, zoomWidget, ui):
        self.__logger = logging.getLogger('sdktool')
        self.__zoomWidget = zoomWidget
        self.__canvas = canvas
        self.__ui = ui
        self.__imageList = []
        self.__imageIndex = -1
        self.__exploreRetPath = None
        self.__tableWidget = None

    def SetPath(self, path):
        self.__exploreRetPath = path

    def UIGraph(self):
        fileList = os.listdir(self.__exploreRetPath)
        imgList = [item for item in fileList if item.split('.')[1] in ['jpg']]
        jsonList = [item for item in fileList if '.json' in item]
        if 0 in [len(fileList), len(imgList), len(jsonList)]:
            dialog = CommonDialog("UIGraph", "files count wrong, img count {}, json count{}".format(len(imgList), len(jsonList)))
            dialog.popUp()
            return

        imageLabelDict = dict()
        for item in imgList:
            key = item.split('.')[0]
            jsonfile = "{}.json".format(key)
            if jsonfile in jsonList:
                imageLabelDict[key] = dict()
                imageLabelDict[key]["image"] = item
                imageLabelDict[key]["label"] = jsonfile

        self.__logger.info("images count {},  json count {}, pairs count {}".format(len(imgList),
                                                                                    len(jsonList),
                                                                                len(imageLabelDict.keys())))
        uiGraph = UIGraph()
        # create graph
        for key, value in imageLabelDict.items():
            with open("{0}/{1}".format(self.__exploreRetPath, value.get("label")), 'r') as UILabelFile:
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
            imgPath = self.__exploreRetPath + '/' + str(node)
            uiGraph.AddNodeImage(node, imgPath)

        uiGraph.Process()
        uiGraph.SetTextEdit(self.__ui.textEdit)

        self.__canvas.addUIGraph(uiGraph)
        PaintImage("Resource/White.jpeg", self.__canvas, self.__zoomWidget, self.__ui)
        self.__canvas.currentModel.append(UIGRAPH)
        self.__canvas.update()

    def Coverage(self):
        # clear previous figures
        plt.figure(1)
        jsonFile = self.__exploreRetPath + '/coverage.json'
        if not os.path.exists(jsonFile):
            self.__logger.error("file {} not exists".format(jsonFile))
            return
        try:
            with open(jsonFile) as f:
                value = json.load(f)
        except Exception as e:
            self.__logger.error("load json file {} failed".format(jsonFile))
            return

        buttonValue = value.get("button")
        sceneValue = value.get("scene")
        if None in [buttonValue, sceneValue]:
            self.__logger.error("read button or scene from file {} failed".format(jsonFile))
            return

        plt.cla()
        n_groups = 1
        index = np.arange(n_groups)
        bar_width = 0.3
        ax1 = plt.subplot(1, 2, 2)
        plt.sca(ax1)
        opacity = 0.4
        plt.bar(index,  buttonValue.get("sampleNum"), bar_width, alpha=opacity, color='b', label='游戏按钮')
        plt.text(index, buttonValue.get("sampleNum"), str(buttonValue.get("sampleNum")), ha='center')
        plt.bar(index + bar_width, buttonValue.get("coverNum"), bar_width, alpha=opacity, color='r', label='探索覆盖')
        plt.text(index + bar_width, buttonValue.get("coverNum"), str(buttonValue.get("coverNum")), ha='center')
        yValue = (buttonValue.get("sampleNum"), buttonValue.get("coverNum"))
        ymaxValue = math.ceil(max(yValue) * 1.2)
        plt.ylim(0, ymaxValue)
        if platform == 'win32':
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.xlabel(str('按钮'))
            plt.ylabel(str('按钮数量'))
            plt.title(str('按钮覆盖率'))
            plt.legend()
        else:
            chinesefont = FontProperties(fname='/usr/share/fonts/truetype/arphic/uming.ttc')
            plt.xlabel(str('按钮'), fontproperties=chinesefont)
            plt.ylabel(str('按钮数量'), fontproperties=chinesefont)
            plt.title(str('按钮覆盖率'), fontproperties=chinesefont)
            plt.legend(prop=chinesefont)
        plt.tight_layout()
        ax2 = plt.subplot(1, 2, 1)
        plt.sca(ax2)
        plt.bar(index, sceneValue.get("sampleNum"), bar_width, alpha=opacity, color='g', label='游戏场景')
        plt.text(index, sceneValue.get("sampleNum"), str(sceneValue.get("sampleNum")), ha='center')
        plt.bar(index + bar_width, sceneValue.get("coverNum"), bar_width, alpha=opacity, color='y',
                         label='探索覆盖')
        plt.text(index + bar_width, sceneValue.get("coverNum"), str(sceneValue.get("coverNum")), ha='center')
        yValue1 = (sceneValue.get("sampleNum"), sceneValue.get("coverNum"))
        ymaxValue1 = math.ceil(max(yValue1) * 1.2)
        plt.ylim(0, ymaxValue1)
        if platform == 'win32':
            plt.xlabel(str('场景'))
            plt.ylabel(str('场景数量'))
            plt.title(str('场景覆盖率'))
            plt.legend()
        else:
            chinesefont = FontProperties(fname='/usr/share/fonts/truetype/arphic/uming.ttc')
            plt.xlabel(str('场景'), fontproperties=chinesefont)
            plt.ylabel(str('场景数量'), fontproperties=chinesefont)
            plt.title(str('场景覆盖率'), fontproperties=chinesefont)
            plt.legend(prop=chinesefont)
        plt.tight_layout()
        plt.subplots_adjust(left=0.1, right=0.97, top=0.92, bottom=0.12, wspace=0.31, hspace=0.2)

        name = 'coverage.jpg'
        plt.savefig(name)
        PaintImage(name, self.__canvas, self.__zoomWidget, self.__ui)
        plt.close(1)

    def UICoverage(self):
        jsonFile = self.__exploreRetPath + '/coverage.json'
        if not os.path.exists(jsonFile):
            self.__logger.error("file {} not exists".format(jsonFile))
            return
        try:
            with open(jsonFile) as f:
                value = json.load(f)
        except Exception as e:
            self.__logger.error("load json file {} failed".format(jsonFile))
            return

        coverList = value.get('coverList') or []
        self.__tableWidget = QTableWidget()
        self.__tableWidget.setSortingEnabled(True)
        self.__tableWidget.setRowCount(len(coverList))
        self.__tableWidget.setColumnCount(4)
        self.__tableWidget.setHorizontalHeaderLabels(['图像名', '按钮数', '覆盖数', '覆盖率'])
        self.__tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        index = 0
        for item in coverList:
            fileName = item.get("fileName")
            sampleNum = item.get("sampleNum")

            coverNum = item.get("coverNum")
            coverage = item.get("coverage")
            newItem = QTableWidgetItem(fileName)

            self.__tableWidget.setItem(index, 0, newItem)

            newItem = QTableWidgetItem()
            newItem.setData(Qt.EditRole, int(sampleNum))
            self.__tableWidget.setItem(index, 1, newItem)

            newItem = QTableWidgetItem()
            newItem.setData(Qt.EditRole, int(coverNum))
            self.__tableWidget.setItem(index, 2, newItem)

            newItem = QTableWidgetItem(float(coverage))
            newItem.setData(Qt.EditRole, float(coverage))
            self.__tableWidget.setItem(index, 3, newItem)
            index += 1

        for i in range(self.__ui.horizontalLayout_4.count()):
            item = self.__ui.horizontalLayout_4.itemAt(i)
            item.widget().hide()
        self.__ui.horizontalLayout_4.addWidget(self.__tableWidget)

    def Reset(self):
        for i in range(self.__ui.horizontalLayout_4.count()):
            item = self.__ui.horizontalLayout_4.itemAt(i)
            item.widget().show()

        if self.__tableWidget is not None:
            self.__tableWidget.deleteLater()
            self.__tableWidget = None

