# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import time

from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker


class Communicate(QObject):
    signal = pyqtSignal(str)


# 定时器，通过继承QThread类来实现
class ToolTimer(QThread):

    def __init__(self, frequent=1):
        QThread.__init__(self)
        self.stopped = True
        self.frequent = frequent
        self.time_signal = Communicate()
        self.mutex = QMutex()

    def run(self):
        '''重写QThread类的run函数，若线程启动，则会被执行'''
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            if self.stopped:
                return
            self.time_signal.signal.emit("1")

            time.sleep(1 / self.frequent)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, fps):
        self.frequent = fps

    def get_fps(self):
        return self.frequent
