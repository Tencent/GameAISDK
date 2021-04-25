# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import logging

from qtpy import QT_VERSION
from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

QT5 = QT_VERSION[0] == '5'  # NOQA
logger = logging.getLogger("sdktool")


def new_icon(icon_name):
    icons_dir = os.path.join(os.environ['AI_SDK_TOOL_PATH'], 'Resource')
    return QtGui.QIcon(os.path.join(':/', icons_dir, '%s.png' % icon_name))


class LabelQLineEdit(QtWidgets.QLineEdit):
    def __init__(self):
        self.list_widget = None
        super(LabelQLineEdit, self).__init__()

    def set_list_widget(self, list_widget):
        self.list_widget = list_widget

    def keyPressEvent(self, e):
        if e.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            self.list_widget.keyPressEvent(e)
        else:
            super(LabelQLineEdit, self).keyPressEvent(e)


class LabelTextDialog(QtWidgets.QDialog):

    def __init__(self, text="Enter object label", parent=None, labels=None,
                 sort_labels=True, show_text_field=True,
                 completion='startswith', fit_to_content=None):
        if fit_to_content is None:
            fit_to_content = {'row': False, 'column': True}
        self._fit_to_content = fit_to_content

        super(LabelTextDialog, self).__init__(parent)
        self.edit = LabelQLineEdit()
        self.edit.setPlaceholderText(text)
        self.edit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(r'^[^ \t].+'), None))

        self.edit.editingFinished.connect(self.post_process)
        layout = QtWidgets.QVBoxLayout()
        if show_text_field:
            layout.addWidget(self.edit)
        # buttons
        self.buttonBox = bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self,
        )
        bb.button(bb.Ok).setIcon(new_icon('done'))
        bb.button(bb.Cancel).setIcon(new_icon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        # label_list
        self.labelList = QtWidgets.QListWidget()
        if self._fit_to_content['row']:
            self.labelList.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        if self._fit_to_content['column']:
            self.labelList.setVerticalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
        self._sort_labels = sort_labels
        if labels:
            self.labelList.addItems(labels)
        if self._sort_labels:
            self.labelList.sortItems()
        else:
            self.labelList.setDragDropMode(
                QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.currentItemChanged.connect(self.label_selected)
        self.edit.set_list_widget(self.labelList)
        layout.addWidget(self.labelList)
        self.setLayout(layout)
        # completion
        completer = QtWidgets.QCompleter()
        if not QT5 and completion != 'startswith':
            logger.warn(
                "completion other than 'startswith' is only "
                "supported with Qt5. Using 'startswith'"
            )
            completion = 'startswith'
        if completion == 'startswith':
            completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
            # Default settings.
            # completer.setFilterMode(QtCore.Qt.MatchStartsWith)
        elif completion == 'contains':
            completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            completer.setFilterMode(QtCore.Qt.MatchContains)
        else:
            raise ValueError('Unsupported completion: {}'.format(completion))
        completer.setModel(self.labelList.model())
        self.edit.setCompleter(completer)

    def add_label_history(self, label):
        if self.labelList.findItems(label, QtCore.Qt.MatchExactly):
            return
        self.labelList.addItem(label)
        if self._sort_labels:
            self.labelList.sortItems()

    def label_selected(self, item):
        self.edit.setText(item.text())

    def validate(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        if text:
            self.add_label_history(text)
            self.accept()

    def post_process(self):
        text = self.edit.text()
        if hasattr(text, 'strip'):
            text = text.strip()
        else:
            text = text.trimmed()
        self.edit.setText(text)

    def pop_up(self, text=None, move=True):
        if self._fit_to_content['row']:
            self.labelList.setMinimumHeight(
                self.labelList.sizeHintForRow(0) * self.labelList.count() + 2
            )
        if self._fit_to_content['column']:
            self.labelList.setMinimumWidth(
                self.labelList.sizeHintForColumn(0) + 2
            )
        # if text is None, the previous label in self.edit is kept
        if text is None:
            text = self.edit.text()
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        items = self.labelList.findItems(text, QtCore.Qt.MatchFixedString)
        if items:
            if len(items) != 1:
                logger.warning("Label list has duplicate '{}'".format(text))
            self.labelList.setCurrentItem(items[0])
            row = self.labelList.row(items[0])
            self.edit.completer().setCurrentRow(row)
        self.edit.setFocus(QtCore.Qt.PopupFocusReason)
        if move:
            self.move(QtGui.QCursor.pos())
        return self.edit.text() if self.exec_() else None
