# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import numpy
import time
import mss
import cv2
import traceback
from pywinauto.win32functions import GetSystemMetrics
from pywinauto.controls.hwndwrapper import win32gui
import logging

from .inputVirtual.hidinputs import *
from ..iPcDeviceAPI import IPcDeviceAPI
from .APIDefine import LOG_DEFAULT

class WindowsDeviceAPI(IPcDeviceAPI):
    def __init__(self, platform):
        IPcDeviceAPI.__init__(self, platform)
        self.width = GetSystemMetrics(0)
        self.height = GetSystemMetrics(1)
        self.__logger = None

    def Initialize(self, long_edge, foregroundwin_only, win_names):
        self.__logger = logging.getLogger(LOG_DEFAULT)
        self.long_edge = long_edge
        self.foregroundwin_only = foregroundwin_only
        self.win_names = win_names
        self.mouse = VirtualMouse()
        self.keyboard = VirtualKeyboard()
        return True

    def DeInitialize(self):
        return True

    def ScreenCap(self, start_x=0, start_y=0, width=None, height=None):
        try:
            bbox, fullwin = self.get_bbox_fullwin()
            if not self.foregroundwin_only:     # -- Full screeen, instead of foregroundwindow
                bbox = fullwin
            if width:
                bbox[2] = width
            if height:
                bbox[3] = height
            with mss.mss() as sct:
                sct_img = numpy.array(sct.grab((bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3])))[:, :, :3]
            if self.long_edge:
                scale_to_longedge = self.long_edge / max(bbox[2], bbox[3])
                sct_img = cv2.resize(sct_img, (0,0), fx=scale_to_longedge, fy=scale_to_longedge) 
            return sct_img
        except Exception as e:
            self.__logger.error('screencap error [{}]'.format(e))
            self.__logger.error(traceback.format_exc())
            raise e

    def InputKeys(self, keys, long_click_time):
        self.keyboard.inputKeys(keys, long_click_time / 1000)

    def InputStrings(self, key_string):
        self.keyboard.inputString(key_string)

    def MouseMove(self, px, py):
        percent_x, percent_y = self.pixel_to_percent(px, py)
        self.mouse.move((percent_x, percent_y))

    def MouseClick(self, px, py):
        percent_x, percent_y = self.pixel_to_percent(px, py)
        self.mouse.click((percent_x, percent_y))

    def MouseDoubleClick(self, px, py):
        percent_x, percent_y = self.pixel_to_percent(px, py)
        self.mouse.doubleclick((percent_x, percent_y))

    def MouseRightClick(self, px, py):
        percent_x, percent_y = self.pixel_to_percent(px, py)
        self.mouse.rightclick((percent_x, percent_y))

    def MouseLongClick(self, px, py, long_click_time):
        percent_x, percent_y = self.pixel_to_percent(px, py)
        self.mouse.longclick(long_click_time / 1000, (percent_x, percent_y))

    def MouseDrag(self, fromX, fromY, toX, toY, during_time):
        percent_fromX, percent_fromY = self.pixel_to_percent(fromX, fromY)
        percent_toX, percent_toY = self.pixel_to_percent(toX, toY)
        self.mouse.drag(percent_fromX, percent_fromY, percent_toX, percent_toY, during_time)

    def pixel_to_percent(self, x, y):
        bbox, fullwin = self.get_bbox_fullwin()
        if not self.foregroundwin_only:     # -- Full screeen, instead of foregroundwindow
            bbox = fullwin
        scale_to_actual = max(bbox[2], bbox[3]) / self.long_edge if self.long_edge else 1
        actual_x, actual_y = x * scale_to_actual, y * scale_to_actual
        # -- Window may not start from (0, 0), so we originate the coordinates here
        actual_x_from_orig, actual_y_from_orig = actual_x + bbox[0], actual_y + bbox[1]
        percent_x = actual_x_from_orig / fullwin[2]
        percent_y = actual_y_from_orig / fullwin[3]
        return percent_x, percent_y

    def get_bbox_fullwin(self):
        """ Return (start_x_from_left, start_y_from_top, width, height) """
        if not self.win_names or len(self.win_names) == 0:
            raw_bbox = win32gui.GetWindowRect(win32gui.GetForegroundWindow())
        else:
            raw_bbox = self.bbox_from_winlist()
            
        # -- Change from (x, y, x+w, y+h) to (x, y, w, h)
        bbox = (raw_bbox[0], raw_bbox[1], raw_bbox[2] - raw_bbox[0], raw_bbox[3] - raw_bbox[1])
        fullwin = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))
        return bbox, fullwin

    def bbox_from_winlist(self):
        toplist, winlist = [], []
        def enum_cb(hwnd, results):
            winlist.append((hwnd, win32gui.GetWindowText(hwnd)))
        win32gui.EnumWindows(enum_cb, toplist)

        for win_name in self.win_names:
            curr_win = [(hwnd, title) for hwnd, title in winlist if win_name in title]
            if len(curr_win) > 0:
                break
        try:
            raw_bbox = win32gui.GetWindowRect(curr_win[0][0])
        except IndexError:
            self.__logger.info('screencap warn [Specfied window name Not Found. Use foreground instead.]')
            raw_bbox = win32gui.GetWindowRect(win32gui.GetForegroundWindow())
        return raw_bbox
