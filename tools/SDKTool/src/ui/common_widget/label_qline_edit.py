# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from qtpy import QtWidgets
from PyQt5.QtCore import pyqtSignal


class LabelQLineEdit(QtWidgets.QLineEdit):
    # (before, after)
    text_modified = pyqtSignal(str, str)

    def __init__(self, content='...', parent=None, mode=None):
        super(LabelQLineEdit, self).__init__(parent)
        self.editingFinished.connect(self._handle_editing_finished)
        self.textChanged.connect(self._handle_text_changed)
        self.__before = content
        self.__mode = mode
        self.__logger = logging.getLogger('sdktool')

    def _handle_text_changed(self):
        before, after = self.__before, self.text()
        if before != after:
            self.__before = after
            self.text_modified.emit(before, after)

    def _handle_editing_finished(self):
        pass

    def mousePressEvent(self, e):
        self.__logger.info("mousePressEvent %s", e)
        dlg = QtWidgets.QFileDialog()
        if self.__mode is not None:
            dlg.setFileMode(QtWidgets.QFileDialog.Directory)

        if dlg.exec():
            text = dlg.selectedFiles()[0]
            self.setText(text)
