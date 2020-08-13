# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import cv2
import time
from .MinicapStream import MinicapStream
from .RotationWatcher import RotationWatcher

class ScreenMinicap(MinicapStream, RotationWatcher):
    def __init__(self, device=None, isShow=False, serial=None):
        super(self.__class__, self).__init__(device, isShow, serial)

    def Initialize(self, capHeight = 720, capWidth = 1280, minicapPort=None):
        # self.__InstallMinicap()
        self.InitVMSize(capHeight, capWidth)
        self.open_rotation_watcher(on_rotation_change=lambda v: self.OpenMinicapStream(capHeight, capWidth, minicapPort))

        # self.OpenMinicapStream(capHeight, capWidth)
        return True

if __name__ == '__main__':
    import logging.config

    LOG_CFG_FILE = '../cfg/logauto.ini'
    logging.config.fileConfig(LOG_CFG_FILE)

    screen = ScreenMinicap(None)
    screen.Initialize()
    frameCountTimestamp = time.time()

    while True:
        now = time.time()
        difftime = now - frameCountTimestamp
        img = screen.GetScreen()

        if img is not None:
            cv2.imshow('screen', img)
            cv2.waitKey(1)

        if difftime > 1.0:
            print('FPS: {0}'.format(screen.frame_count()))
            screen.clear_frame_count()
            frameCountTimestamp = now
