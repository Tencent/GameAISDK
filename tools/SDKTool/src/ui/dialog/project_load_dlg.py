# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os

from qtpy import QtCore
from qtpy import QtWidgets
from qtpy import QtGui
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal

from ..common_widget.label_qline_edit import LabelQLineEdit
from ..dialog.tip_dialog import show_warning_tips


class ProjectLoadDlg(QtWidgets.QDialog):
    # directory
    finish_new_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProjectLoadDlg, self).__init__(parent)
        self.setWindowTitle("load project")
        layout = QtWidgets.QVBoxLayout()

        self.dir_layout = QtWidgets.QHBoxLayout()
        self.label_dir = QtWidgets.QLabel(self)
        self.label_dir.setObjectName("project dir")
        self.label_dir.setText("directory")
        self.dir_layout.addWidget(self.label_dir)
        self.edit_dir = LabelQLineEdit(mode=QtWidgets.QFileDialog.Directory)
        self.edit_dir.setPlaceholderText("...")
        self.dir_layout.addWidget(self.edit_dir)
        layout.addLayout(self.dir_layout)

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

    def pop_up(self):
        self.move(QCursor.pos())
        self.exec_()

    def check_valid(self):
        directory = self.edit_dir.text()
        if len(directory) == 0:
            show_warning_tips("please input directory")
            return
        if os.path.isdir(directory):
            show_warning_tips("directory must be a folder")
            return

        self.finish_new_signal.emit(directory)
        self.accept()
