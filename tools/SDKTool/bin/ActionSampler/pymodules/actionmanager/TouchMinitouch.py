# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)

from .MinitouchStream import MinitouchStream
from screen.RotationWatcher import RotationWatcher

class TouchMinitouch(MinitouchStream, RotationWatcher):
    def __init__(self, device):
        super(self.__class__, self).__init__(device)
        self.OpenMinitouchStream()
        # self.open_rotation_watcher(on_rotation_change=lambda v: self.ChangeRotation(v))

import time
from adbkit.ADBClient import ADBClient

if __name__ == '__main__':
    adb = ADBClient()
    dev = adb.device()
    testTouch = TouchMinitouch(dev)
    count = 100
    while count > 0:
        testTouch.Click(200, 200)
        # testTouch.Move(500, 0)
        # testTouch.Up()
        time.sleep(1)
        count -= 1
