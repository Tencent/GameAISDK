'''
    自定义的弹框，以及进度条，labelimg中的代码
    代码链接：https://github.com/tzutalin/labelImg/tree/master/libs
'''

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import newIcon, labelValidator

BB = QDialogButtonBox

# 继承于QSlider类，实现自己的进度条控件
class CustomSlider(QSlider):
    costomSliderClicked = pyqtSignal()

    def __init__(self, parent=None):
        super(CustomSlider, self).__init__(parent)

    def mousePressEvent(self, QMouseEvent):
        '''重写mousePressEvent函数，实现点击进度条上任意位置，都能跳到指定进度'''
        super(CustomSlider, self).mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos().x() / self.width()
        self.setValue(pos * (self.maximum() - self.minimum() + self.minimum()))
        self.costomSliderClicked.emit()


class confirmDialog(QDialog):

    def __init__(self, text="", parent=None):
        super(confirmDialog, self).__init__(parent)

        self.setWindowTitle("请确认")
        self.label = QLabel()
        self.label.setText(text)
        self.confirmFlag = False

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.buttonBox = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(newIcon('done'))
        bb.button(BB.Cancel).setIcon(newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        self.setLayout(layout)

    def validate(self):
        self.confirmFlag = True
        self.accept()

    def popUp(self, move=True):
        if move:
            self.move(QCursor.pos())
        return self.confirmFlag if self.exec() else None

    def GetButtonBox(self):
        return self.buttonBox
