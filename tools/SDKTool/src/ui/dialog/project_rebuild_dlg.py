# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets
from PyQt5.QtGui import QCursor

from src.ui.common_widget.label_qline_edit import LabelQLineEdit
from ..utils import create_common_button_box


class ProjectRebuildDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ProjectRebuildDlg, self).__init__(parent)
        self.setWindowTitle("rebuild project")
        layout = QtWidgets.QVBoxLayout()

        self.data_dir_layout = QtWidgets.QHBoxLayout()
        self.data_dir_label = QtWidgets.QLabel(self)
        self.data_dir_label.setObjectName("video_label")
        self.data_dir_label.setText("data dir")
        self.data_dir_layout.addWidget(self.data_dir_label)
        self.data_dir_edit = LabelQLineEdit(mode=QtWidgets.QFileDialog.Directory)
        self.data_dir_edit.setPlaceholderText("....")
        self.data_dir_layout.addWidget(self.data_dir_edit)
        layout.addLayout(self.data_dir_layout)

        self.ui_config_layout = QtWidgets.QHBoxLayout()
        self.ui_config_label = QtWidgets.QLabel(self)
        self.ui_config_label.setObjectName("ui config")
        self.ui_config_label.setText("ui config(.json)")
        self.ui_config_layout.addWidget(self.ui_config_label)
        self.ui_config_edit = LabelQLineEdit()
        self.ui_config_edit.setPlaceholderText("...")
        self.ui_config_layout.addWidget(self.ui_config_edit)
        layout.addLayout(self.ui_config_layout)

        self.task_config_layout = QtWidgets.QHBoxLayout()
        self.task_config_label = QtWidgets.QLabel(self)
        self.task_config_label.setObjectName("task configg")
        self.task_config_label.setText("task config(.json)")
        self.task_config_layout.addWidget(self.task_config_label)
        self.task_config_edit = LabelQLineEdit()
        self.task_config_edit.setPlaceholderText("...")
        self.task_config_layout.addWidget(self.task_config_edit)
        layout.addLayout(self.task_config_layout)

        bb = create_common_button_box(self, self.accept, self.reject)
        layout.addWidget(bb)
        self.setLayout(layout)

    def pop_up(self):
        self.move(QCursor.pos())
        self.exec_()
