# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QDialogButtonBox
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, pyqtSignal

BB = QDialogButtonBox

logger = logging.getLogger("sdktool")


class LabelDialog(QDialog):
    finish_signal = pyqtSignal()

    def __init__(self, text="", title='', parent=None):
        super(LabelDialog, self).__init__(parent)

        layout = QVBoxLayout()

        self.setWindowTitle(title)
        # layout_label = QHBoxLayout()
        label = QLabel()
        label.setText(text)
        # layout_label.addWidget(label)
        layout.addWidget(label)

        bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)

        bb.accepted.connect(self.valid)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        self.setLayout(layout)

    def pop_up(self, move=True):
        if move:
            self.move(QCursor.pos())
        return True if self.exec() else None

    def valid(self):
        logger.debug("emit valid....")
        self.finish_signal.emit()
        self.accept()
