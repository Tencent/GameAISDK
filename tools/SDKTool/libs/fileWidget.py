# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class fileDialog(QWidget):

    def __init__(self, parent=None):
        super(fileDialog, self).__init__(parent)
        layout = QVBoxLayout()
        self.resize(800, 1000)

        self.content = QTextEdit()
        layout.addWidget(self.content)
        self.setWindowTitle("文件查看")

        self.setLayout(layout)

    def loadFile(self):
        fname, _ = QFileDialog.getOpenFileName(self, '选择图片', 'c:\\', 'Image files(*.jpg *.gif *.png)')
        self.label.setPixmap(QPixmap(fname))

    def show_text(self, filePath):
        f = open(filePath, 'r')
        with f:
            data = f.read()
            self.content.setText(data)
        
        self.show()
            
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    fileload =  fileDialog()
    fileload.show()
    sys.exit(app.exec_())