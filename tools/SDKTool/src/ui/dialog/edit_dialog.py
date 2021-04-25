# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, pyqtSignal

from .tip_dialog import show_warning_tips

BB = QDialogButtonBox

logger = logging.getLogger("sdktool")


class EditDialog(QDialog):
    finish_signal = pyqtSignal(str)

    def __init__(self, label_text='', default_edit='project name', title='', parent=None):
        super(EditDialog, self).__init__(parent)

        layout = QVBoxLayout()

        self.setWindowTitle(title)
        layout_label = QHBoxLayout()
        label = QLabel()
        label.setText(label_text)
        layout_label.addWidget(label)

        # layout.addWidget(label)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(default_edit)
        self.edit.setFocusPolicy(Qt.StrongFocus)
        layout_label.addWidget(self.edit)

        layout.addLayout(layout_label)

        bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self.__valid = True
        self.setLayout(layout)

    def pop_up(self, move=True):
        if move:
            self.move(QCursor.pos())
        return True if self.exec() else None

    def validate(self):
        text = self.edit.text()
        if len(text) != 0:
            logger.info("emit %s", text)
            self.finish_signal.emit(text)
            logger.debug("accept..............")
            if self.__valid:
                self.accept()
            logger.debug("accept over..............")
        else:
            logger.info("text %s", text)
            show_warning_tips("please input name")

    def set_valid(self, flag):
        self.__valid = flag
