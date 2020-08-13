# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ProgressBarDialog(QWidget):
    def __init__(self, title='', label='', minValue=0, maxValue=100, parent=None):
        super(ProgressBarDialog, self).__init__(parent)
        self.processBar = QProgressDialog(self)
        self.SetBarWindowTitle(title)
        self.SetLabelText(label)
        self.SetMinValue(minValue)
        self.SetMaxValue(maxValue)
        self.processBar.setWindowModality(Qt.WindowModal)
        self.setGeometry(800, 300, 580, 570)
        self.processBar.canceled.connect(lambda: print("被取消"))

    def SetBarWindowTitle(self, text):
        self.processBar.setWindowTitle(text)
        self.setWindowTitle(text)

    def SetLabelText(self, text):
        self.processBar.setLabelText(text)

    def SetMinValue(self, minValue):
        self.processBar.setMinimum(minValue)

    def SetMaxValue(self, maxvalue):
        self.processBar.setMaximum(maxvalue)

    def SetValue(self, value):
        self.processBar.setValue(value)

    def CloseBar(self):
        self.processBar.close()

    def ResetBar(self):
        self.processBar = None

    def Show(self):
        self.processBar.show()

    def IsValid(self):
        if self.processBar is not None:
            return True
        else:
            return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fileIndex = '3'  # 当前正在处理第几个文件
    filenum = '10'  # 文件总数，在label中显示
    progress = ProgressBarDialog(fileIndex, filenum, 0)
    progress.popUp()
    progress.show()
    app.exec_()
