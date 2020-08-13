'''
    画布，labelimg中的代码
    代码链接：https://github.com/tzutalin/labelImg/tree/master/libs
'''
import os
import cv2
import numpy as np

import logging
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

#from PyQt4.QtOpenGL import *
from libs.shape import Shape
from libs.utils import distance
from libs.labelDialog import *
from libs.Graph import UIGraph, UIGRAPH
from libs.ProgressBarDialog import ProgressBarDialog

# from libs.polyrnn.src.polyrnn import *

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor

# class Canvas(QGLWidget):


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)

    CREATE, EDIT, LABEL = list(range(3))
    # RECT, LINE, POINT = list(range(3))

    epsilon = 11.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.CREATE                    # 画布当前的模式，create表示画图形，edit表示修改图形
        self.shapes = []
        self.current = None
        self.mouseMoveFlag = False
        self.nextModel = None
        self.currentModel = list()                 # list类型，表示当前需要执行的画图形的任务，比如如果其内容为[rect, rect, line, point]，
                                                   # 那说明接下来需要画四个图形，分别是框，框，线，点。
        self.pointGraphIndex = 1
        self.graphPrevPointIndex = -1
        self.selectedShape = None  # save the selected shape here
        self.selectedShapeCopy = None
        self.drawingLineColor = QColor(0, 0, 255)
        self.drawingRectColor = QColor(0, 0, 255)
        self.line = Shape(line_color=self.drawingLineColor)
        self.prevPoint = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.pixmap = QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.hVertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.verified = False
        self.drawSquare = False
        self.rectTreeItem = list()                  # list类型，当前画图的图形（rect）与QTreeItem的对应，以便拖拽的时候实时更新item中的数据。
        self.lineTreeItem = list()                  # list类型，当前画图的图形（line）与QTreeItem的对应，以便拖拽的时候实时更新item中的数据。
        self.pointTreeItem = list()                 # list类型，当前画图的图形（point）与QTreeItem的对应，以便拖拽的时候实时更新item中的数据。
        self.itemRect = dict()                      # rect类型的字典，{"x": int, "y", int, "w": int, "h": int}
        self.itemLine = dict()                      # line类型的字典，{"actionX1": int, "actionY1", int, "actionX2": int, "actionY2": int}
        self.itemPoint = dict()                     # point类型的字典，{"x": int, "y", int}
        self.shapeTree = dict()                     # UI标签功能用到的成员，是一个字典，key为shape类型变量，value为item
                                                    # 表示该标签（shape）对应的是树结构中的某一个类型（类型在树结构中以item形式呈现）
        self.polygonLineItem = None
        self.btnPressPos = QPoint()
        self.mouseFlag = False
        self.shapesNum = 0

        self.treeIcon = QIcon()
        self.treeIcon.addPixmap(QPixmap(":/menu/treeIcon.png"), QIcon.Normal, QIcon.Off)

        self.__logger = logging.getLogger('sdktool')
        self.segmentLabels = dict()
        self.segmentPos = dict()
        self.segmentCurrentShape = None
        self.currentSegmentImg = None
        self.currentSegmentDict = dict()
        self.segmentWidth = None
        self.segmentHeight = None
        self.pixLevelFlag = False
        self.preSegShapeNum = 0
        self.shapeItem = dict()
        self.itemShape = dict()
        self.labelDialog = LabelDialog(parent=self)
        self.labelNameDialog = LabelDialog(parent=self)
        self.treeWidget = None
        self.labelFlag = False
        self.selectShapeIndex = -1
        self.ui = None
        self.cursorWidth = 10
        # self.polyRNN = PolyRNNModel()
        self.labelImage = None
        self.rightMenu = QMenu(self)

        # 删除shape的动作，在UI标签中用到
        self.actionDeleteShape = QAction(self)
        self.actionDeleteShape.setText("删除")
        self.actionDeleteShape.triggered.connect(self.deleteShape)

        # 删除点的动作，在地图路径和图结构的地图路径中用到
        self.actionDeletePoint = QAction(self)
        self.actionDeletePoint.setText("删除")
        self.actionDeletePoint.triggered.connect(self.deletePoint)
        self.uiGraph = None
        self.processBar = None

    def ClearCurrModel(self):
        self.currentModel.clear()

    def ClearRectTree(self):
        self.rectTreeItem.clear()

    def addUIGraph(self, uiGraph):
        self.uiGraph = uiGraph
    '''
        self.actionDeletePoint动作的槽函数，删除路径中的点
    '''
    def deletePoint(self):
        shape = self.shapes[0]
        shape.points.pop(self.hVertex)
        if self.hVertex in shape.pointLinePath.keys():
            del shape.pointLinePath[self.hVertex]

        for key in sorted(shape.pointLinePath.keys()):
            valueList = shape.pointLinePath[key]
            if self.hVertex in valueList:
                valueList.remove(self.hVertex)

            if key > self.hVertex:
                del shape.pointLinePath[key]
                shape.pointLinePath[key - 1] = valueList

            for index in range(len(valueList)):
                if valueList[index] > self.hVertex:
                    valueList[index] -= 1

        self.update()

    '''
        self.actionDeleteShape动作的槽函数，在UI标签中用到
        删除shape（标签）时，self.shapeItem中删除对应的项
    '''
    def deleteShape(self):
        if self.selectedShape in self.shapeItem.keys():
            labelText = self.shapeItem[self.selectedShape].text(0)
            self.shapeItem.pop(self.selectedShape)
            self.itemShape[labelText].remove(self.selectedShape)
            if len(self.itemShape[labelText]) == 0:
                labelItem = self.treeWidget.topLevelItem(2)
                for itemIndex in range(labelItem.childCount()):
                    treeItem = labelItem.child(itemIndex)
                    if treeItem.text(0) == labelText:
                        labelItem.takeChild(itemIndex)
                        break
        self.shapes.remove(self.selectedShape)

    def setLabelImage(self, image):
        self.labelImage = image

    def setUI(self, ui):
        self.ui = ui

    def setTreeWidget(self, treeWidget):
        self.treeWidget = treeWidget

        # initRes, strError = self.polyRNN.init(useGGNN=False)
        # if initRes is False:
        #     self.__logger.error(strError)
        #     self.__logger.error("init polygon++ model failed")

    def setSegmentParams(self, segmentLabels, segmentPos):
        self.segmentLabels = segmentLabels
        self.segmentPos = segmentPos

    def setSegmentImg(self, width, height):
        self.segmentWidth = width
        self.segmentHeight = height
        self.labelFlag = True
        self.currentSegmentImg = np.zeros([height, width, 3], dtype="uint8")

    def setDrawingColor(self, qColor):
        self.drawingLineColor = qColor
        self.drawingRectColor = qColor
        
    def setUIWorker(self, uiWorker):
        self.uiWorker = uiWorker

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        if UIGRAPH in self.currentModel:
            self.mode = None
            return False
        else:
            return self.mode == self.CREATE

    def segment(self):
        return self.mode == self.LABEL

    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShape()
        self.prevPoint = QPointF()
        self.repaint()

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    def selectedVertex(self):
        return self.hVertex is not None

    def setPolygonLineItem(self, treeItem):
        self.polygonLineItem = treeItem

    '''
        向self.rectTreeItem添加一个rect的QTreeItem，当下次画图时，会对应修改该item的值
    '''
    def setRectTreeItem(self, treeItem):
        self.rectTreeItem.append(treeItem)
        # filter "threshold"
        for itemIndex in range(treeItem.childCount() - 1):
            itemChild = treeItem.child(itemIndex)
            self.itemRect[itemChild.text(0)] = int(itemChild.text(1))

        # templateThreshold type is float
        itemChild = treeItem.child(treeItem.childCount() - 1)
        self.itemRect[itemChild.text(0)] = float(itemChild.text(1))

    '''
        向self.lineTreeItem添加一个line的QTreeItem，当下次画图时，会对应修改该item的值
    '''
    def setLineTreeItem(self, treeItem):
        self.lineTreeItem.append(treeItem)
        for itemIndex in range(treeItem.childCount()):
            itemChild = treeItem.child(itemIndex)
            
            # "actionX1"(0), "actionY1"(1),"actionX2"(7), "actionY2"(8)
            if itemIndex % 7 < 2:
                self.itemLine[itemChild.text(0)] = int(itemChild.text(1))
            else:
                self.itemLine[itemChild.text(0)] = itemChild.text(1)


    '''
        向self.pointTreeItem添加一个point的QTreeItem，当下次画图时，会对应修改该item的值
    '''
    def setPointTreeItem(self, treeItem):
        self.pointTreeItem.append(treeItem)
        for itemIndex in range(treeItem.childCount()):
            itemChild = treeItem.child(itemIndex)
            if itemIndex < 2:
                self.itemPoint[itemChild.text(0)] = int(itemChild.text(1))
            else:
                self.itemPoint[itemChild.text(0)] = itemChild.text(1)



    '''
        self.itemRect保存的是事实的画布上框的坐标，将self.itemRect中的坐标写到对应的rect类型的QTreeItem中
    '''
    def setItemRect(self, itemTree=None):
        if itemTree is None:
            itemTree = self.rectTreeItem[0]
            
        for itemIndex in range(itemTree.childCount()):
            itemChild = itemTree.child(itemIndex)
            itemChild.setText(1, str(self.itemRect.get(itemChild.text(0))))

            # print("{} set text {}".format(itemChild.text(0), self.itemRect.get(itemChild.text(0))))
        self.update()
    '''
        self.lineTreeItem保存的是事实的画布上线的起始点和结束点的坐标，将self.lineTreeItem中的坐标写到对应的line类型的QTreeItem中
    '''
    def setItemLine(self, itemTree=None):
        if itemTree is None:
            itemTree = self.lineTreeItem[0]
            
        for itemIndex in range(itemTree.childCount()):
            itemChild = itemTree.child(itemIndex)
            itemChild.setText(1, str(self.itemLine[itemChild.text(0)]))

        self.update()

    '''
        self.pointTreeItem保存的是事实的画布上点的坐标，将self.pointTreeItem中的坐标写到对应的rect类型的QTreeItem中
    '''
    def setItemPoint(self, itemTree=None):
        if itemTree is None:
            itemTree = self.pointTreeItem[0]
            
        for itemIndex in range(itemTree.childCount()):
            itemChild = itemTree.child(itemIndex)
            itemChild.setText(1, str(self.itemPoint[itemChild.text(0)]))

    def getRectanglePix(self, centerx=None, centery=None, radius=5):
        pixList = list()
        xbegin = max(0, centerx - radius)
        xend = min(self.segmentWidth, centerx + radius)
        ybegin = max(0, centery - radius)
        yend = min(self.segmentHeight, centery + radius)

        for x in range(xbegin, xend):
            for y in range(ybegin, yend):
                pixList.append([x, y])

        return pixList

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        if self.mouseFlag is False:
            return
        self.mouseMoveFlag = True
        pos = self.transformPos(ev.pos())

        # Update coordinates in status bar if image is opened
        if self.pixmap.isNull() is not True:
            self.uiWorker.ui.labelCoordinates.setText(
                'X: %d; Y: %d' % (pos.x(), pos.y()))

        posx = int(pos.x())
        posy = int(pos.y())

        # segment label
        if self.segment():
            self.overrideCursor(CURSOR_DRAW)
            if self.current:
                color = self.drawingLineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)

                if self.drawSquare:
                    initPos = self.current[0]
                    minX = initPos.x()
                    minY = initPos.y()
                    min_size = min(abs(pos.x() - minX), abs(pos.y() - minY))
                    directionX = -1 if pos.x() - minX < 0 else 1
                    directionY = -1 if pos.y() - minY < 0 else 1
                    self.line[1] = QPointF(minX + directionX * min_size, minY + directionY * min_size)
                else:
                    self.line[1] = pos

                self.line.line_color = color
                self.prevPoint = QPointF()
                self.current.highlightClear()
            else:
                self.prevPoint = pos
            self.repaint()
            return

        # Polygon drawing.
        if self.drawing():
            self.overrideCursor(CURSOR_DRAW)
            if len(self.currentModel) > 0:
                if self.currentModel[0] == Shape.GRAPH:
                    return

            if self.current:
                color = self.drawingLineColor
                if self.outOfPixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Project the point to the pixmap's edges.
                    pos = self.intersectionPoint(self.current[-1], pos)
                elif len(self.current) > 1 and self.closeEnough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.overrideCursor(CURSOR_POINT)
                    self.current.highlightVertex(0, Shape.NEAR_VERTEX)

                if self.drawSquare:
                    initPos = self.current[0]
                    minX = initPos.x()
                    minY = initPos.y()
                    min_size = min(abs(pos.x() - minX), abs(pos.y() - minY))
                    directionX = -1 if pos.x() - minX < 0 else 1
                    directionY = -1 if pos.y() - minY < 0 else 1
                    self.line[1] = QPointF(minX + directionX * min_size, minY + directionY * min_size)
                else:
                    self.line[1] = pos
                
                # print(len(self.shapes))
                if self.currentModel[0] == Shape.RECT:
                    # if (len(self.shapes) > 0):
                    #     print(self.shapes[0].points)
                    if int(pos.x()) < int(self.btnPressPos.x()):
                        if int(pos.y()) < int(self.btnPressPos.y()):
                            self.itemRect["x"] = int(pos.x())
                            self.itemRect["y"] = int(pos.y())
                            self.itemRect["w"] = int(self.btnPressPos.x() - pos.x())
                            self.itemRect["h"] = int(self.btnPressPos.y() - pos.y())
                        else:
                            self.itemRect["x"] = int(pos.x())
                            self.itemRect["y"] = int(self.btnPressPos.y())
                            self.itemRect["w"] = int(self.btnPressPos.x() - pos.x())
                            self.itemRect["h"] = int(pos.y() - self.btnPressPos.y())
                    else:
                        if int(pos.y()) < int(self.btnPressPos.y()):
                            self.itemRect["x"] = int(self.btnPressPos.x())
                            self.itemRect["y"] = int(pos.y())
                            self.itemRect["w"] = int(pos.x() - self.btnPressPos.x())
                            self.itemRect["h"] = int(self.btnPressPos.y() - pos.y())
                        else:
                            self.itemRect["x"] = int(self.btnPressPos.x())
                            self.itemRect["y"] = int(self.btnPressPos.y())
                            self.itemRect["w"] = int(pos.x() - self.btnPressPos.x())
                            self.itemRect["h"] = int(pos.y() - self.btnPressPos.y())
                    self.setItemRect()

                elif self.currentModel[0] == Shape.LINE:
                    self.itemLine["actionX1"] = int(self.btnPressPos.x())
                    self.itemLine["actionY1"] = int(self.btnPressPos.y())
                    self.itemLine["actionX2"] = int(pos.x())
                    self.itemLine["actionY2"] = int(pos.y())
                    self.setItemLine()
                
                self.line.line_color = color
                self.prevPoint = QPointF()
                self.current.highlightClear()
            else:
                self.prevPoint = pos
            self.repaint()
            return

        # Polygon copy moving.
        if Qt.RightButton & ev.buttons():
            if self.selectedShapeCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShapeCopy, pos)
                self.repaint()
            elif self.selectedShape:
                self.selectedShapeCopy = self.selectedShape.copy()
                self.repaint()
            return

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.shapeMoved.emit()
                self.repaint()
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.shapeMoved.emit()
                self.repaint()

            self.pointGraphIndex = 1
            if self.labelFlag is True:
                return

            selectShape = self.hShape
            
            if selectShape is None:
                return
            
            if selectShape.shapeName == Shape.RECT:
                point1 = selectShape.points[0]
                point2 = selectShape.points[1]
                point3 = selectShape.points[2]
                point4 = selectShape.points[3]
    
                beginPointX = min(point1.x(), point2.x(), point3.x(), point4.x())
                beginPointY = min(point1.y(), point2.y(), point3.y(), point4.y())
                endPointX = max(point1.x(), point2.x(), point3.x(), point4.x())
                endPointY = max(point1.y(), point2.y(), point3.y(), point4.y())
    
                self.itemRect["x"] = int(beginPointX)
                self.itemRect["y"] = int(beginPointY)
                self.itemRect["w"] = int(endPointX - beginPointX)
                self.itemRect["h"] = int(endPointY - beginPointY)

                if selectShape in self.shapeTree.keys():
                    self.setItemRect(self.shapeTree[selectShape])
            elif selectShape.shapeName == Shape.LINE:
                point1 = selectShape.points[0]
                point2 = selectShape.points[1]
                
                self.itemLine["actionX1"] = int(point1.x())
                self.itemLine["actionY1"] = int(point1.y())
                self.itemLine["actionX2"] = int(point2.x())
                self.itemLine["actionY2"] = int(point2.y())

                if selectShape in self.shapeTree.keys():
                    self.setItemLine(self.shapeTree[selectShape])
            elif selectShape.shapeName == Shape.POINT:
                point = selectShape.points[0]
                self.itemPoint["actionX"] = int(point.x())
                self.itemPoint["actionY"] = int(point.y())

                if selectShape in self.shapeTree.keys():
                    self.setItemPoint(self.shapeTree[selectShape])
            elif selectShape.shapeName == Shape.POLYGONLINE:
                for index, point in enumerate(selectShape.points):
                    pointItem = self.polygonLineItem.child(index)
                    pointItem.child(0).setText(1, str(int(point.x())))
                    pointItem.child(1).setText(1, str(int(point.y())))
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,z
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon / self.scale)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = index, shape
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos):
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex, self.hShape = None, shape
                self.setToolTip(
                    "Click & drag to move shape '%s'" % shape.label)
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape = None, None
            self.overrideCursor(CURSOR_DEFAULT)

        if self.uiGraph is not None:
            # first: if there is a edge nearby, highLight it and unhighLight node image
            edge = self.uiGraph.NearestEdge(pos.x(), pos.y(), self.epsilon / self.scale)
            if edge is not None:
                self.uiGraph.SetHighLightEdge(edge)
                self.uiGraph.ClearHighLightNode()
            else:
                self.uiGraph.ClearHighLightEdge()
                # second: find UI Image
                node = self.uiGraph.NearestNode(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
                if node is not None:
                    self.uiGraph.SetHighLightNode(node)
                else:
                    self.uiGraph.ClearHighLightNode()

            self.update()

    def mouseDoubleClickEvent(self, ev):
        pos = self.transformPos(ev.pos())

        if self.uiGraph is not None:
            # first: if there is a  edge nearby, highLight it and show the node images
            edge = self.uiGraph.NearestEdge(pos.x(), pos.y(), self.epsilon / self.scale)
            if edge is not None:
                self.uiGraph.SetSelectEdge(edge)
                self.uiGraph.SetHighLightEdge(edge)
            else:
                # second: if there is a node nearby, highLight it and show the node image
                node = self.uiGraph.NearestNode(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
                if node is not None:
                    self.uiGraph.SetSelectNode(node)
                    self.uiGraph.SetHighLightNode(node)
                    self.uiGraph.SetShowNodeImage(True)
                else:
                    self.uiGraph.ClearSelectNode()
                    self.uiGraph.ClearHighLightNode()
                    self.uiGraph.ClearSelectEdge()
                    self.uiGraph.ClearHighLightEdge()

            self.repaint()

        if self.mouseFlag is False:
            return

        if self.labelFlag is False:
            return

        selectedFlag = False
        for shape in self.shapes:
            if shape.selected == True:
                selectedFlag = True
                break

        if selectedFlag is False:
            return

        labelText = self.labelDialog.popUp()
        if labelText is None or labelText == "":
            return

        labelName = self.labelNameDialog.popUp()
        if labelName is None or labelName == "":
            return

        treeLabelItem = None
        labelFlag = False
        for itemIndex in range(self.treeWidget.topLevelItemCount()):
            treeItem = self.treeWidget.topLevelItem(itemIndex)
            if treeItem.text(0) == labelText:
                labelFlag = True
                treeLabelItem = treeItem
                break

        if labelFlag is False:
            treeLabelItem = QTreeWidgetItem()
            treeLabelItem.setText(0, labelText)
            self.treeWidget.addTopLevelItem(treeLabelItem)

        for shape in self.shapes:
            if shape.selected == True:
                self.shapeItem[shape] = treeLabelItem
                if labelText not in self.itemShape.keys():
                    self.itemShape[labelText] = list()
                self.itemShape[labelText].append(shape)

        for shape in self.shapes:
            shape.selected = False

    def mousePressEvent(self, ev):
        for shape in self.shapes:
            shape.selected = False

        if self.mouseFlag is False:
            return
        self.mouseMoveFlag = True
        pos = self.transformPos(ev.pos())

        if self.segment():
            self.handleDrawing(pos)
            return

        if ev.button() == Qt.LeftButton:
            if self.drawing():
                self.shapesNum = len(self.shapes)

                if len(self.currentModel) == 0:
                    return

                if self.currentModel[0] in [Shape.POINT, Shape.POLYGONLINE]:
                    return
                elif self.currentModel[0] == Shape.GRAPH:
                    self.shapes[0].addPoint(QPoint(pos.x(), pos.y()))

                elif self.currentModel[0] == Shape.POLYGON:
                    self.segmentBeginPoint = pos
                self.handleDrawing(pos)
                self.btnPressPos = pos
            else:
                self.selectShapePoint(pos)
                if self.uiGraph is not None:
                    # first select edge
                    edge = self.uiGraph.NearestEdge(pos.x(), pos.y(), self.epsilon / self.scale)
                    if edge is None:
                        # if there is no edge nearby, may be this is a new node
                        node = self.uiGraph.NearestNode(pos.x(), pos.y(), 3 * self.epsilon / self.scale)
                        self.uiGraph.SetSelectNode(node)
                        self.uiGraph.SetShowNodeImage(False)

                    # clear previous selected edge
                    self.uiGraph.ClearSelectEdge()

                if len(self.currentModel) > 0 and self.currentModel[0] == Shape.GRAPH:

                    if self.selectedVertex():
                        if self.pointGraphIndex == 1:
                            self.graphPrevPointIndex = self.hVertex
                            self.pointGraphIndex = 2
                        else:
                            graphShape = self.shapes[0]
                            if self.graphPrevPointIndex not in graphShape.pointLinePath.keys():
                                graphShape.pointLinePath[self.graphPrevPointIndex] = list()
                            graphShape.pointLinePath[self.graphPrevPointIndex].append(self.hVertex)
                            self.pointGraphIndex = 1

                if self.selectedShape is not None and self.labelFlag is True:
                    if self.selectShapeIndex >= 0 and self.selectShapeIndex < len(self.shapes):
                        if self.shapes[self.selectShapeIndex] in self.shapeItem.keys():
                            treeLabelItem = self.shapeItem[self.shapes[self.selectShapeIndex]]
                            self.treeWidget.setCurrentItem(treeLabelItem)
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == Qt.RightButton and self.editing():
            self.selectShapePoint(pos)
            if self.labelFlag is True:
                if self.selectedShape is not None:
                    self.rightMenu.addAction(self.actionDeleteShape)
                    self.rightMenu.exec_(QCursor.pos())

            self.prevPoint = pos
            self.repaint()

    def mouseReleaseEvent(self, ev):
        if self.mouseFlag is False:
            return
        self.mouseMoveFlag = True

        if self.segment():
            prevShapeNum = len(self.shapes)
            # print(self.currentSegmentDict)
            pos = self.transformPos(ev.pos())
            self.handleDrawing(pos)

            if len(self.shapes) == prevShapeNum:
                return

            labelText = self.labelDialog.popUp()
            if labelText is None or labelText == "":
                return

            # labelName = self.labelNameDialog.popUp()
            # if labelName is None or labelText == "":
            #     return

            print("label Text {}".format(labelText))

            treeLabelItem = None
            labelFlag = False
            labelTreeItem = self.treeWidget.topLevelItem(2)
            for itemIndex in range(labelTreeItem.childCount()):
                treeItem = labelTreeItem.child(itemIndex)
                if treeItem.text(0) == labelText:
                    labelFlag = True
                    treeLabelItem = treeItem
                    break

            if labelFlag is False:
                treeLabelItem = self.CreateTreeItem(key=labelText)
                labelTreeItem.addChild(treeLabelItem)

            shape = self.shapes[-1]
            
            # shape.setLabel(labelName)
            shape.setLabel(labelText)

            self.shapeItem[shape] = treeLabelItem
            if labelText not in self.itemShape.keys():
                self.itemShape[labelText] = list()
            self.itemShape[labelText].append(shape)

            for shape in self.shapes:
                shape.selected = False
            # for point in newContour:
            #     img = cv2.circle(self.currentSegmentImg, (point[0], point[1]), 3, (0, 0, 255))
            # cv2.imshow('res', img)
            # cv2.waitKey(0)
            return

        if ev.button() == Qt.RightButton:
            if self.selectedVertex():
                self.rightMenu.addAction(self.actionDeletePoint)
                self.rightMenu.exec_(QCursor.pos())
                return

            menu = self.menus[bool(self.selectedShapeCopy)]
            self.restoreCursor()
            if not menu.exec_(self.mapToGlobal(ev.pos()))\
               and self.selectedShapeCopy:
                # Cancel the move by deleting the shadow copy.
                self.selectedShapeCopy = None
                self.repaint()
        elif ev.button() == Qt.LeftButton and self.selectedShape:
            if self.selectedVertex():
                self.overrideCursor(CURSOR_POINT)
            else:
                self.overrideCursor(CURSOR_GRAB)
        elif ev.button() == Qt.LeftButton:
            pos = self.transformPos(ev.pos())
            if self.drawing() and len(self.currentModel) > 0:
                if self.currentModel[0] == Shape.POLYGON:
                    self.segmentEndPoint = pos
                    # self.CreateSegmentEdge()
                    self.finalise()

                elif self.currentModel[0] == Shape.LINE:
                    self.handleDrawingLine(pos)
                    if len(self.lineTreeItem) > 0 and len(self.shapes) > 0:
                        self.shapeTree[self.shapes[-1]] = self.lineTreeItem[0]
                elif self.currentModel[0] == Shape.RECT:
                    self.handleDrawing(pos)
                    if len(self.rectTreeItem) > 0 and len(self.shapes) > 0:
                        self.shapeTree[self.shapes[-1]] = self.rectTreeItem[0]
                elif self.currentModel[0] == Shape.POLYGONLINE:
                    if len(self.shapes) == 0:
                        shape = Shape(name=Shape.POLYGONLINE)
                        self.shapes.append(shape)
                    self.shapes[0].addPoint(QPoint(pos.x(), pos.y()))
                    childPointItem = self.CreateTreeItem(key='point')
                    childPointItem.addChild(self.CreateTreeItem(key='x', value=int(pos.x()), edit=True))
                    childPointItem.addChild(self.CreateTreeItem(key='y', value=int(pos.y()), edit=True))
                    self.polygonLineItem.addChild(childPointItem)
                    self.repaint()
                elif self.currentModel[0] == Shape.POINT:
                    self.itemPoint["actionX"] = int(pos.x())
                    self.itemPoint["actionY"] = int(pos.y())
                    self.setItemPoint()
                    shape = Shape(name=Shape.POINT)
                    shape.addPoint(QPoint(pos.x(), pos.y()))
                    self.shapes.append(shape)
                    self.shapeTree[self.shapes[-1]] = self.pointTreeItem[0]
                    self.repaint()
                elif self.currentModel[0] == Shape.GRAPH:
                    pass
            
            if len(self.currentModel) > 0 and len(self.shapes) - self.shapesNum == 1:
                if self.currentModel[0] == Shape.LINE:
                    self.lineTreeItem.pop(0)
                elif self.currentModel[0] == Shape.RECT:
                    self.rectTreeItem.pop(0)
                elif self.currentModel[0] in [Shape.POLYGONLINE, Shape.POLYGON, Shape.GRAPH]:
                    pass
                else:
                    self.pointTreeItem.pop(0)

                if self.currentModel[0] not in [Shape.POLYGONLINE, Shape.GRAPH]:
                    self.currentModel.pop(0)

            elif UIGraph in self.currentModel:
                self.mode = None

            if len(self.currentModel) == 0:
                self.mode = self.EDIT

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

    def format_shape(self, s):
        return dict(label=s.label,
                    line_color=s.line_color.getRgb(),
                    fill_color=s.fill_color.getRgb(),
                    points=[(p.x(), p.y()) for p in s.points],
                    # add chris
                    difficult=s.difficult)

    def endMove(self, copy=False):
        assert self.selectedShape and self.selectedShapeCopy
        shape = self.selectedShapeCopy
        #del shape.fill_color
        #del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            self.selectedShape.points = [p for p in shape.points]
        self.selectedShapeCopy = None

    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()
            
    def handleDrawingLine(self, pos):
        if self.current and self.current.reachMaxPoints() is False:
            targetPos = self.line[1]
            self.current.addPoint(targetPos)
            self.finalise()
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()
            
    def handleDrawingPoint(self, pos):
        if self.current and self.current.reachMaxPoints() is False:
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()
            self.current.addPoint(QPointF(maxX, minY))
            self.current.addPoint(targetPos)
            self.current.addPoint(QPointF(minX, maxY))
            self.finalise()
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    def handleDrawing(self, pos):
        if self.current and self.current.reachMaxPoints() is False:
            initPos = self.current[0]
            minX = initPos.x()
            minY = initPos.y()
            targetPos = self.line[1]
            maxX = targetPos.x()
            maxY = targetPos.y()
            self.current.addPoint(QPointF(maxX, minY))
            self.current.addPoint(targetPos)
            self.current.addPoint(QPointF(minX, maxY))
            self.finalise()
        elif not self.outOfPixmap(pos):
            self.current = Shape()
            self.current.addPoint(pos)
            self.line.points = [pos, pos]
            self.setHiding()
            self.drawingPolygon.emit(True)
            self.update()

    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def selectShape(self, shape):
        self.deSelectShape()
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)
        self.update()

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape()
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            self.selectShape(shape)
            return

        index = len(self.shapes) - 1
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point):
                self.selectShape(shape)
                self.selectShapeIndex = index
                self.calculateOffsets(shape, point)
                return
            index -= 1

    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def snapPointToCanvas(self, x, y):
        """
        Moves a point x,y to within the boundaries of the canvas.
        :return: (x,y,snapped) where snapped is True if x or y were changed, False if not.
        """
        if x < 0 or x > self.pixmap.width() or y < 0 or y > self.pixmap.height():
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.pixmap.width())
            y = min(y, self.pixmap.height())
            return x, y, True

        return x, y, False
    
    def boundedMoveVertexLine(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)
    
        if self.drawSquare:
            opposite_point_index = (index + 2) % 4
            opposite_point = shape[opposite_point_index]
        
            min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
            directionX = -1 if pos.x() - opposite_point.x() < 0 else 1
            directionY = -1 if pos.y() - opposite_point.y() < 0 else 1
            shiftPos = QPointF(opposite_point.x() + directionX * min_size - point.x(),
                               opposite_point.y() + directionY * min_size - point.y())
        else:
            shiftPos = pos - point
    
        shape.moveVertexBy(index, shiftPos)

    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        if self.outOfPixmap(pos):
            pos = self.intersectionPoint(point, pos)

        if self.drawSquare:
            opposite_point_index = (index + 2) % 4
            opposite_point = shape[opposite_point_index]

            min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
            directionX = -1 if pos.x() - opposite_point.x() < 0 else 1
            directionY = -1 if pos.y() - opposite_point.y() < 0 else 1
            shiftPos = QPointF(opposite_point.x() + directionX * min_size - point.x(),
                               opposite_point.y() + directionY * min_size - point.y())
        else:
            shiftPos = pos - point

        shape.moveVertexBy(index, shiftPos)
        
        if shape.shapeName == shape.RECT:
            lindex = (index + 1) % 4
            rindex = (index + 3) % 4
            lshift = None
            rshift = None
            if index % 2 == 0:
                rshift = QPointF(shiftPos.x(), 0)
                lshift = QPointF(0, shiftPos.y())
            else:
                lshift = QPointF(shiftPos.x(), 0)
                rshift = QPointF(0, shiftPos.y())
            shape.moveVertexBy(rindex, rshift)
            shape.moveVertexBy(lindex, lshift)

    def boundedMoveShape(self, shape, pos):
        if self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        #self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    def deSelectShape(self):
        if self.selectedShape:
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False)
            self.selectionChanged.emit(False)
            self.update()

    def deleteSelected(self):
        if self.selectedShape:
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.selectedShape = None
            self.update()
            return shape

    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShape()
            self.shapes.append(shape)
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            return shape

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    def paintEvent(self, event):
        if self.processBar is not None and self.processBar.IsValid():
            self.processBar.Show()

        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.Paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            leftTop = self.line[0]
            rightBottom = self.line[1]
            rectWidth = rightBottom.x() - leftTop.x()
            rectHeight = rightBottom.y() - leftTop.y()
            p.setPen(self.drawingRectColor)
            brush = QBrush(Qt.BDiagPattern)
            p.setBrush(brush)
            p.drawRect(leftTop.x(), leftTop.y(), rectWidth, rectHeight)

        if self.drawing() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
            if len(self.currentModel) > 0 and self.currentModel[0] != Shape.GRAPH:
                p.setPen(QColor(0, 0, 0))
                p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
                p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())

        if self.segment() and not self.prevPoint.isNull() and not self.outOfPixmap(self.prevPoint):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(self.prevPoint.x(), 0, self.prevPoint.x(), self.pixmap.height())
            p.drawLine(0, self.prevPoint.y(), self.pixmap.width(), self.prevPoint.y())

        # self.setAutoFillBackground(True)
        # if self.verified:
        #     pal = self.palette()
        #     pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
        #     self.setPalette(pal)
        # else:
        #     pal = self.palette()
        #     pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
        #     self.setPalette(pal)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(255, 255, 255))
        self.setPalette(pal)

        if self.uiGraph is not None:
            self.uiGraph.Paint(p)

        p.end()

    def CreateProcessbar(self, title, label, minValue, maxValue):
        # print("create.......")
        self.processBar = ProgressBarDialog(title=title, label=label,
                                            minValue=minValue, maxValue=maxValue)

    def SetBarCurValue(self, value):
        self.processBar.SetValue(value)

    def CloseBar(self):
        self.processBar.CloseBar()
        self.processBar.ResetBar()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return

        self.current.close()
        if len(self.currentModel) > 0:
            self.current.setShapName(self.currentModel[0])
        self.shapes.append(self.current)
        self.current = None
        self.setHiding(False)
        self.newShape.emit()
        self.update()

    def closeEnough(self, p1, p2):
        #d = distance(p1 - p2)
        #m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width(), 0),
                  (size.width(), size.height()),
                  (0, size.height())]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QPointF(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QPointF(min(max(0, x2), max(x3, x4)), y3)

        # Ensure the labels are within the bounds of the image. If not, fix them.
        x, y, _ = self.snapPointToCanvas(x, y)

        return QPointF(x, y)

    def intersectingEdges(self, x1y1, x2y2, points):
        """For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen."""
        x1, y1 = x1y1
        x2, y2 = x2y2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QPointF((x3 + x4) / 2, (y3 + y4) / 2)
                d = distance(m - QPointF(x2, y2))
                yield d, i, (x, y)

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()
        if self.segment():
            if v_delta > 0:
                self.cursorWidth += 2
                if self.cursorWidth > 30:
                    self.cursorWidth = 30
            else:
                self.cursorWidth -= 2
                if self.cursorWidth < 5:
                    self.cursorWidth = 5

            self.repaint()
            return
        elif self.editing():
            if v_delta > 0:
                self.scale += 0.05

                self.adjustSize()
                self.update()
            else:
                self.scale -= 0.05
                self.adjustSize()
                self.update()
            return

        if self.uiGraph is not None:
            if v_delta > 0:
                self.scale += 0.05
                print("canvas scale .... {}".format(self.scale))
                self.adjustSize()
                self.update()
            else:
                self.scale -= 0.05
                self.adjustSize()
                self.update()
            return

        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if Qt.ControlModifier == int(mods) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape:
            print('ESC press, labelFlag {}, self.mode {}'.format(self.labelFlag, self.mode))

            if self.labelFlag is True:
                if self.mode == self.EDIT:
                    self.mode = self.LABEL
                elif self.mode == self.LABEL:
                    self.mode = self.EDIT
            else:
                # if len(self.currentModel) > 0 and self.currentModel[0] == Shape.GRAPH:
                if len(self.currentModel) > 0:
                    if self.mode == self.CREATE:
                        self.mode = self.EDIT
                    elif self.mode == self.EDIT:
                        self.mode = self.CREATE

            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Return and self.canCloseShape():
            self.finalise()
        elif key == Qt.Key_Left and self.selectedShape:
            self.moveOnePixel('Left')
        elif key == Qt.Key_Right and self.selectedShape:
            self.moveOnePixel('Right')
        elif key == Qt.Key_Up and self.selectedShape:
            self.moveOnePixel('Up')
        elif key == Qt.Key_Down and self.selectedShape:
            self.moveOnePixel('Down')
        elif key == Qt.Key_Shift:
            self.pixLevelFlag = True
        elif key == Qt.Key_Z:
            if self.labelFlag is True:
                if self.ui.actionSwitch.isChecked():
                    self.ui.actionSwitch.setChecked(False)
                    self.setLabel()
                else:
                    self.ui.actionSwitch.setChecked(True)
                    self.setEditing()

    def keyReleaseEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Shift:
            self.pixLevelFlag = False

    def moveOnePixel(self, direction):
        # print(self.selectedShape.points)
        if direction == 'Left' and not self.moveOutOfBound(QPointF(-1.0, 0)):
            # print("move Left one pixel")
            self.selectedShape.points[0] += QPointF(-1.0, 0)
            self.selectedShape.points[1] += QPointF(-1.0, 0)
            self.selectedShape.points[2] += QPointF(-1.0, 0)
            self.selectedShape.points[3] += QPointF(-1.0, 0)
        elif direction == 'Right' and not self.moveOutOfBound(QPointF(1.0, 0)):
            # print("move Right one pixel")
            self.selectedShape.points[0] += QPointF(1.0, 0)
            self.selectedShape.points[1] += QPointF(1.0, 0)
            self.selectedShape.points[2] += QPointF(1.0, 0)
            self.selectedShape.points[3] += QPointF(1.0, 0)
        elif direction == 'Up' and not self.moveOutOfBound(QPointF(0, -1.0)):
            # print("move Up one pixel")
            self.selectedShape.points[0] += QPointF(0, -1.0)
            self.selectedShape.points[1] += QPointF(0, -1.0)
            self.selectedShape.points[2] += QPointF(0, -1.0)
            self.selectedShape.points[3] += QPointF(0, -1.0)
        elif direction == 'Down' and not self.moveOutOfBound(QPointF(0, 1.0)):
            # print("move Down one pixel")
            self.selectedShape.points[0] += QPointF(0, 1.0)
            self.selectedShape.points[1] += QPointF(0, 1.0)
            self.selectedShape.points[2] += QPointF(0, 1.0)
            self.selectedShape.points[3] += QPointF(0, 1.0)
        self.shapeMoved.emit()
        self.repaint()

    def moveOutOfBound(self, step):
        points = [p1+p2 for p1, p2 in zip(self.selectedShape.points, [step]*4)]
        return True in map(self.outOfPixmap, points)

    def setLastLabel(self, text, line_color  = None, fill_color = None):
        assert text
        self.shapes[-1].label = text
        if line_color:
            self.shapes[-1].line_color = line_color

        if fill_color:
            self.shapes[-1].fill_color = fill_color

        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def resetAllLines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.mouseFlag = True
        self.repaint()

    def loadShapes(self, shapes):
        self.shapes = shapes
        self.current = None
        self.repaint()

    def AddShape(self, shape):
        self.shapes.append(shape)
        self.current = None
        self.repaint()

    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.mode = self.CREATE
        self.mouseFlag = False
        self.selectedShape = None
        self.currentModel.clear()
        self.rectTreeItem.clear()
        self.lineTreeItem.clear()
        self.pointTreeItem.clear()
        self.update()

    def setDrawingShapeToSquare(self, status):
        self.drawSquare = status

    def setLabel(self):
        self.mode = self.LABEL