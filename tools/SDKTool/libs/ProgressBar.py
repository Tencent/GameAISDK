# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ProgressBar(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)

        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('ProgressBar')
        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)

        self.button = QPushButton('Start', self)
        self.button.setFocusPolicy(Qt.NoFocus)
        self.button.move(40, 80)

        self.button.clicked.connect(self.onStart)
        self.timer = QBasicTimer()
        self.step = 0

    def timerEvent(self, event):
        if self.step >= 100:
            self.timer.stop()
            return
        self.step = self.step + 1
        self.pbar.setValue(self.step)

    def onStart(self):
        if self.timer.isActive():
            self.timer.stop()
            self.button.setText('Start')
        else:
            self.timer.start(100, self)
            self.button.setText('Stop')