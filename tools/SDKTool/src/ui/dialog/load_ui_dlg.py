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

from ..common_widget.label_qline_edit import LabelQLineEdit
from ..utils import create_common_button_box


class LoadUIDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoadUIDlg, self).__init__(parent)
        self.setWindowTitle("load ui config")
        layout = QtWidgets.QVBoxLayout()

        self.ui_config_layout = QtWidgets.QHBoxLayout()
        self.ui_config_label = QtWidgets.QLabel(self)
        self.ui_config_label.setObjectName("ui config")
        self.ui_config_label.setText("ui config(.json)")
        self.ui_config_layout.addWidget(self.ui_config_label)
        self.ui_config_edit = LabelQLineEdit()
        self.ui_config_edit.setPlaceholderText("...")
        self.ui_config_layout.addWidget(self.ui_config_edit)
        layout.addLayout(self.ui_config_layout)
        bb = create_common_button_box(self, self.accept, self.reject)
        layout.addWidget(bb)
        self.setLayout(layout)

    def pop_up(self):
        self.move(QCursor.pos())
        self.exec_()
