# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from .ui_canvas import canvas
from PyQt5.QtCore import QObject, pyqtSignal


class Communicate(QObject):
    signal = pyqtSignal(str)


class CanvasSignal(object):
    canvas_update_signal = Communicate()

    def __init__(self):
        self.canvas_update_signal.signal[str].connect(canvas.show_img)

    def canvas_show_img(self, img_name):
        self.canvas_update_signal.signal[str].emit(img_name)

    @staticmethod
    def reset_state():
        canvas.reset_state()


canvas_signal_inst = CanvasSignal()
