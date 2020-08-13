# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from APIDefine import *
from platformdefult.adbkit.ADBClient import ADBClient

PP_RET_OK = 0
PP_RET_ERR = -1
PP_RET_ERR_SOCKET_EXCEPTION = -2



class ADBWrapper(object):
    def __init__(self):
        pass

    def init(self, serial=None, is_portrait=True, long_edge=720):
        if serial is None:
            self.__logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.__logger = logging.getLogger(serial)
        adb = ADBClient()
        self.__device = adb.device(serial)

        self.__short_side, self.__long_side = self.__device.wmsize()

        self.__CoordinateScale = float(self.__long_side) / long_edge

        if is_portrait:
            self.__config_ori = UI_SCREEN_ORI_PORTRAIT
        else:
            self.__config_ori = UI_SCREEN_ORI_LANDSCAPE

    def install_app(self, apk_path):
        return self.__device.install(apk_path)

    def launch_app(self, package_name, activity_name):
        self.__logger.debug('Launch Game:[{0}/{1}]'.format(package_name, activity_name))
        self.wake()
        # self.__device.clear_app_data(package_name=MOBILEQQ_PACKAGE_NAME)
        self.exit_app(package_name)
        self.__device.launch_app(package_name=package_name, activity_name=activity_name)

    def exit_app(self, package_name):
        self.__device.kill_app(package_name=package_name)

    def current_app(self):
        return self.__device.current_app()

    def clear_app_data(self, app_package_name):
        self.__device.clear_app_data(package_name=app_package_name)

    def key(self, key):
        self.__device.keyevent(key)

    def text(self, text):
        self.__device.input_text(text)

    def sleep(self):
        self.__device.close_screen()

    def wake(self):
        self.__device.wake()
        self.__device.unlock()
        self.__device.keyevent('HOME')

    def vm_size(self):
        return self.__short_side, self.__long_side

    def take_screen_shot(self, target_path):
        self.__device.screenshot()
        self.__device.pull('/data/local/tmp/screenshot.png', target_path)

    def get_screen_ori(self):
        rot = self.__minicap.GetRotation()
        if rot in [0, 2]:
            return UI_SCREEN_ORI_PORTRAIT
        else:
            return UI_SCREEN_ORI_LANDSCAPE

    def adb_click(self, px, py):
        if self.get_screen_ori() != self.__config_ori:
            px, py = self._ConvertPos(px, py)
        px, py = self._ConvertCoordinates(px, py)
        self.__device.click(px, py)
    def adb_swipe(self, sx, sy, ex, ey, duration_ms=50):
        if self.get_screen_ori() != self.__config_ori:
            sx, sy = self._ConvertPos(sx, sy)
            ex, ey = self._ConvertPos(ex, ey)
        sx, sy = self._ConvertCoordinates(sx, sy)
        ex, ey = self._ConvertCoordinates(ex, ey)
        self.__device.swipe(sx, sy, ex, ey, durationMS=duration_ms)

    def device_param(self, packageName):
        deviceParam = dict()
        deviceParam['cpu'], deviceParam['mem'] = self.__device.cpu_mem_usage_with_top(packageName)
        deviceParam['temperature'] = self.__device.temperature()
        deviceParam['battery'] = self.__device.battery()
        if deviceParam['cpu'] == -1:
            self.__logger.error('get cpu param failed')
            return False

        if deviceParam['mem'] == -1:
            self.__logger.error('get mem param failed')
            return False

        if deviceParam['temperature'] == -1:
            self.__logger.error('get temperature param failed')
            return False

        if deviceParam['battery'] == -1:
            self.__logger.error('get battery param failed')
            return False
        return deviceParam
