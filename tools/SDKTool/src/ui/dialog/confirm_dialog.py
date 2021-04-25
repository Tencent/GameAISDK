# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtGui import QCursor, Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QSlider, QLabel, QVBoxLayout

from src.ui.utils import new_icon

BB = QDialogButtonBox


# 继承于QSlider类，实现自己的进度条控件
class CustomSlider(QSlider):
    costom_slider_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(CustomSlider, self).__init__(parent)

    def mousePressEvent(self, QMouseEvent):
        """ MousePressEvent
        重写mousePressEvent函数，实现点击进度条上任意位置，都能跳到指定进度
        :param QMouseEvent:
        :return:
        """
        super(CustomSlider, self).mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos().x() / self.width()
        self.setValue(pos * (self.maximum() - self.minimum() + self.minimum()))
        self.costom_slider_clicked.emit()


class ConfirmDialog(QDialog):

    def __init__(self, text="", parent=None):
        super(ConfirmDialog, self).__init__(parent)

        self.setWindowTitle("请确认")
        self.label = QLabel()
        self.label.setText(text)
        self.confirmFlag = False

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(new_icon('done'))
        bb.button(BB.Cancel).setIcon(new_icon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        self.setLayout(layout)

    def validate(self):
        self.confirmFlag = True
        self.accept()

    def pop_up(self, move=True):
        if move:
            self.move(QCursor.pos())
        return self.confirmFlag if self.exec() else None

    def get_button_box(self):
        return self.buttonBox
