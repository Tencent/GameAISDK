# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import threading
import time
import cv2
import subprocess
import re
import os
import platform
import traceback

from .adb_event_parser import TouchPoint
from . import adb_event_parser as ADBEventParser
from WrappedDeviceAPI.deviceAPI.mobileDevice.android.plugin.Platform_plugin.PlatformWeTest import AdbTool
from WrappedDeviceAPI.deviceAPI.mobileDevice.android.plugin.Platform_plugin.PlatformWeTest import GetInstance

SCREEN_ORI_LANDSCAPE = 0  # 横屏
SCREEN_ORI_PORTRAIT = 1  # 竖屏

LOG = logging.getLogger('action_sampler')


class ADBTouchSampler(object):
    def __init__(self, device_id=None):
        # 设置设备id到全局变量中
        self.__device_id = device_id

        self.__device = AdbTool(device_id)
        self.__device_instance = GetInstance()

        self.__rotation = SCREEN_ORI_LANDSCAPE
        self.__touchXMax = None
        self.__touchYMax = None
        self._proc_getevent = None

    def init(self, long_edge, short_edge):
        self.__is_thread_running = False

        self.__device_instance.init(self.__device_id, long_edge=long_edge, standalone=True)
        device_info, err_msg = self.__device_instance.get_device_info()
        if not device_info:
            raise Exception(err_msg)

        max_contacts = device_info.touch_slot_number
        real_short_edge = int(long_edge * device_info.display_width / device_info.display_height)

        self.__screenCaptureHeight = long_edge
        self.__screenCaptureWidth = real_short_edge

        self.__short_edge_ratio = round(short_edge/real_short_edge, 3)

        output = self.__device.cmd("shell", "-x", "getevent", "-lp").communicate()[0].decode("utf-8")
        if output and output.find("ABS_MT_SLOT") != -1:
            LOG.info('This is Type B device')
            self.__parser = ADBEventParser.ADBEventParserTypeB(max_contacts)
        else:
            LOG.info('This is Type A device')
            self.__parser = ADBEventParser.ADBEventParserTypeA(max_contacts)

        self.__touchXMax, self.__touchYMax = device_info.touch_width, device_info.touch_height

        for i in range(50):
            err_code, img = self.__device_instance.get_image()
            if img is not None:
                break
            time.sleep(1)

        self.detect_rotation()

        self._proc_getevent = self.__device.raw_cmd('shell', '-x', 'getevent', '-l')

        # 启动一个线程去实时解析adb shell getevent返回的结果
        def pull_thread_main():
            self.__is_thread_running = True
            while self.__is_thread_running:
                line = self._proc_getevent.stdout.readline().strip()
                if not line:
                    continue
                else:
                    self.__parser.parse(line)

        self._t = threading.Thread(target=pull_thread_main)
        self._t.setDaemon(True)
        self._t.start()

    def __kill_unused_adb(self):
        if platform.platform().lower().startswith('window'):
            output = subprocess.Popen('tasklist /FI "IMAGENAME eq adb.exe" /FI "STATUS ne running" /NH',
                                      shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).communicate()[0].decode('UTF8')

            result = re.findall('adb.exe\s+(\d+)\s+', output)
            for pid in result:
                os.system('taskkill /F /PID %s' % pid)

    def deinit(self):
        """ 中止录制

        :return:
        """
        self.__is_thread_running = False
        self._t.join(10)
        if self._proc_getevent:
            self._proc_getevent.kill()
            self._proc_getevent = None
            self.__kill_unused_adb()
        self.__device_instance.deinit()

    def detect_rotation(self):
        """ 检测旋转调度

        :return:
        """
        rotation = self.__device_instance.get_rotation()
        if rotation % 2 == 0:  # 竖屏
            self.__rotation = SCREEN_ORI_PORTRAIT
        else:
            self.__rotation = SCREEN_ORI_LANDSCAPE

    def get_sample(self):
        # frame = self.__screen.GetScreen()
        err_code, frame = self.__device_instance.get_image()
        if err_code != 0:
            return None

        if frame is not None:
            h, w = frame.shape[:2]
            if h < w:
                h = int(h * self.__short_edge_ratio)
            else:
                w = int(w * self.__short_edge_ratio)
            frame = cv2.resize(frame.copy(), (w, h))

        ret_points = []
        points = self.__parser.get_touch_points()

        # 对points结果进行坐标转换到截图frame的坐标系下
        for p in points:
            if p is None:
                continue
            else:
                if p.x is None or p.y is None:
                    continue
                else:
                    if self.__rotation == SCREEN_ORI_PORTRAIT:
                        x = int(p.x / self.__touchXMax * self.__screenCaptureWidth * self.__short_edge_ratio)
                        y = int(p.y / self.__touchYMax * self.__screenCaptureHeight)
                    else:
                        x = int(p.y / self.__touchYMax * self.__screenCaptureHeight)
                        y = int(self.__screenCaptureWidth * self.__short_edge_ratio - p.x /
                                self.__touchXMax * self.__screenCaptureWidth * self.__short_edge_ratio)

                    ret_points.append(TouchPoint(p.trackingId, x, y))
        return frame, ret_points
