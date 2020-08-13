'''
    自定义的弹框，labelimg中的代码
    代码链接：https://github.com/tzutalin/labelImg/tree/master/libs
'''

try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

# QT5 = QT_VERSION[0] == '5'  # NOQA

from labelme.logger import logger
import labelme.utils

AI_PLUGIN_TMPT_LIST = [
    "Action",
    "FPS",
    "Imitation",
    "MMO",
    "MOBA",
    "PBE",
    "PUBG"
]

# TODO(unknown):
# - Calculate optimal position so as not to go out of screen area.


class LabelQLineEdit(QLineEdit):

    def setListWidget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [Qt.Key_Up, Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)


class AIPluginDialog(QDialog):

    def __init__(self, text="GameName", parent=None):
        super(AIPluginDialog, self).__init__(parent)
        self.setWindowTitle("Plugin")
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(labelme.utils.labelValidator())
        self.edit.editingFinished.connect(self.postProcess)
        layout = QVBoxLayout()
        layout.addWidget(self.edit)

        self.tmptCombox = QComboBox()
        self.tmptCombox.addItems(AI_PLUGIN_TMPT_LIST)
        layout.addWidget(self.tmptCombox)

        # buttons
        self.buttonBox = bb = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(labelme.utils.newIcon('done'))
        bb.button(bb.Cancel).setIcon(labelme.utils.newIcon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self.setLayout(layout)

    def validate(self):
        text = self.edit.text()

        def _CheckContainChinese(check_str):
            for ch in check_str.encode('utf-8').decode('utf-8'):
                if u'\u4e00' <= ch <= u'\u9fff':
                    return True
            return False
        if _CheckContainChinese(text):
            return

        if text ==  '':
            return

        self.confirmFlag = True
        self.accept()

    def postProcess(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def popUp(self, move=True):
        if move:
            self.move(QCursor.pos())
        return self.confirmFlag if self.exec() else None

    def getGameName(self):
        return self.edit.text()

    def getTemplateName(self):
        return self.tmptCombox.currentText()
