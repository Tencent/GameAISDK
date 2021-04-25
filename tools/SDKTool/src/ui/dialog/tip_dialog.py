# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QCursor


def show_warning_tips(text, title="警告"):
    """ 显示警告信息对话框

    :param text:
    :param title:
    :return:
    """
    QMessageBox.warning(None, title, text)


def show_critical_tips(text, title="警告"):
    """ 显示错误提示对话框

    :param text:
    :param title:
    :return:
    """
    QMessageBox.critical(None, title, text)


def show_question_tips(text, title="询问"):
    """ 显示询问对话框

    :param text:
    :param title:
    :return: True / False
    """
    reply = QMessageBox.question(None, title, text, QMessageBox.Yes, QMessageBox.No)
    return reply == QMessageBox.Yes


def show_message_tips(text, title="提示"):
    """ 显示警告信息对话框

    :param text:
    :param title:
    :return:
    """
    QMessageBox.information(None, title, text)


class TipDialog(QDialog):

    def __init__(self, text="", parent=None):
        super(TipDialog, self).__init__(parent)

        self.setWindowTitle("tips")
        self.label = QLabel()
        self.label.setText(text)
        self.confirmFlag = False

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        self.setLayout(layout)

    def pop_up(self, move=True):
        if move:
            self.move(QCursor.pos())
        return self.confirmFlag if self.exec() else None
