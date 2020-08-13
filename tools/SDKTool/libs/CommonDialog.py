# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtWidgets import *


class CommonDialog(QDialog):
    def __init__(self, title="", text="", parent=None):
        super(CommonDialog, self).__init__(parent)
        self.setWindowTitle(title)
        self.resize(350, 100)

        self.__label = QLabel(text)
        layout = QVBoxLayout()
        layout.addWidget(self.__label)
        BB = QDialogButtonBox(self)
        BB.setStandardButtons(QDialogButtonBox.Ok)
        # self.buttonBox = bb = BB(BB.Ok, Qt.Horizontal, self)
        BB.setObjectName("bb")
        BB.accepted.connect(self.accept)
        BB.rejected.connect(self.reject)
        # BB.button(BB.Ok)
        # BB.accepted.connect(self.accept)
        layout.addWidget(BB)

        self.setLayout(layout)

    def popUp(self):
        self.exec()
