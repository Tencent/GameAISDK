# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QProgressDialog


class ProgressBarDialog(QWidget):
    def __init__(self, title='', label='', minValue=0, maxValue=100, parent=None):
        super(ProgressBarDialog, self).__init__(parent)
        self.process_bar = QProgressDialog(self)
        self.set_bar_window_title(title)
        self.set_label_text(label)
        self.set_min_value(minValue)
        self.set_max_value(maxValue)
        self.process_bar.setWindowModality(Qt.WindowModal)
        self.setGeometry(800, 300, 580, 570)
        self.process_bar.canceled.connect(self.close_bar)

    def set_bar_window_title(self, text):
        self.process_bar.setWindowTitle(text)
        self.setWindowTitle(text)

    def set_label_text(self, text):
        self.process_bar.setLabelText(text)

    def set_min_value(self, minValue):
        self.process_bar.setMinimum(minValue)

    def set_max_value(self, maxvalue):
        self.process_bar.setMaximum(maxvalue)

    def set_value(self, value):
        self.process_bar.setValue(value)

    def close_bar(self):
        self.process_bar.close()

    def reset_bar(self):
        self.process_bar = None

    def show(self):
        self.process_bar.show()

    def is_valid(self):
        return bool(self.process_bar)
