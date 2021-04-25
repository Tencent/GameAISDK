# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import QtGui
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal

from .tip_dialog import show_warning_tips


class ProjectNewDlg(QtWidgets.QDialog):
    # name
    finish_new_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProjectNewDlg, self).__init__(parent)
        self.setWindowTitle("new project")
        layout = QtWidgets.QVBoxLayout()

        self.name_layout = QtWidgets.QHBoxLayout()
        self.label_name = QtWidgets.QLabel(self)
        self.label_name.setObjectName("video_label")
        self.label_name.setText("name")

        self.name_layout.addWidget(self.label_name)
        self.edit_name = QtWidgets.QLineEdit()
        self.edit_name.setPlaceholderText("project name")
        self.edit_name.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.name_layout.addWidget(self.edit_name)
        layout.addLayout(self.name_layout)

        bb = QtWidgets.QDialogButtonBox(
                     QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
                     QtCore.Qt.Horizontal,
                     self,
                 )
        bb.button(bb.Ok).setIcon(QtGui.QIcon(":/menu/done.png"))
        bb.button(bb.Cancel).setIcon(QtGui.QIcon(":/menu/undo.png"))
        bb.accepted.connect(self.check_valid)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self.setLayout(layout)
        self.edit_name.setCursorPosition(2)

    def pop_up(self):
        self.move(QCursor.pos())
        self.exec_()

    def check_valid(self):
        name = self.edit_name.text()

        if len(name) == 0:
            show_warning_tips("please input name")
            return

        self.finish_new_signal.emit(name)
        self.accept()
