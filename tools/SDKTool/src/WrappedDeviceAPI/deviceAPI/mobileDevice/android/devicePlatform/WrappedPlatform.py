# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import re

import numpy as np

from ..APIDefine import LOG_DEFAULT, WAITTIME_POINT
from ..plugin.getPlatformInstance import GetPlatformInstance
from ..plugin.Platform_plugin.PlatformWeTest import AdbTool


class ADBClient(object):
    """ ADB功能接口

    """
    def __init__(self, serial=None):
        self._adb = AdbTool(serial)

    def shell_cmd(self, *args):
        output, _ = self._adb.cmd('shell', *args).communicate()

        if output:
            return output.decode("utf-8", 'ignore').strip()
        return None

    def input_keys(self, keys, repeat=1):
        if keys.startswith('{') and keys.endswith('}'):
            keyValues = {'{HOME}': 3, '{BACK}': 4, '{MENU}': 82, '{VOLUME_UP}': 24,
                         '{VOLUME_DOWN}': 25, '{POWER}': 26, '{TAB}': 61,
                         '{ENTER}': 66, '{SPACE}': 62, '{DEL}': 67, '{END}': 6, '{SEARCH}': 84,
                         '{MOVE_END}': 123, '{MOVE_HOME}': 122, '{ESCAPE}': 111,
                         '{DOUBLEHOME}': '3 3', '{DOUBLEMENU}': '82 82',
                         '{LONGHOME}': '--longpress 3', '{LONGMENU}': '--longpress 82',
                         '{APP_SWITCH}': 187, '{ESC}': 111}
            if keys in keyValues:
                value = str(keyValues[keys])
                if repeat > 1:
                    value = " ".join([value for i in range(repeat)])
                cmd = 'input keyevent "' + value + '"'
                self.shell_cmd(cmd)
            else:
                raise ValueError('输入的不是特殊字符，非特殊字符不需要用{}括起来。')
        else:
            mos = re.findall("(\s*)([^\s]+)(\s*)", keys)
            for mo in mos:
                if mo[0]:
                    for _ in range(len(mo[0])):
                        cmd = 'input keyevent SPACE'
                        self.shell_cmd(cmd)
                cmd = 'input text \'%s\'' % mo[1]
                self.shell_cmd(cmd)   # 某些机器不需要空格
                if mo[2]:
                    for _ in range(len(mo[2])):
                        cmd = 'input keyevent SPACE'
                        self.shell_cmd(cmd)


class PlatformWrapper(object):
    """ 平台操作的包裹器，提供统一的操作接口

    """
    def __init__(self, platform_type):
        self.__platform = platform_type
        self.__actionClass = None
        self.__platformInstance = None
        self.__contactState = []
        self.__logger = None
        self.__adb_client = None

    def Initialize(self, serial=None, long_edge=1280, **kwargs):
        if serial is None:
            self.__logger = logging.getLogger(LOG_DEFAULT)
        else:
            self.__logger = logging.getLogger(serial)
        self.__logger.info('platform: %s', self.__platform)
        self.__platformInstance = GetPlatformInstance(serial, self.__platform)
        if self.__platformInstance is None:
            self.__logger.error('get platform class failed')
            return False, "get platform class failed"

        self.__logger.info('get platform class succeed')

        ret, err_info = self.__platformInstance.init(serial, True, long_edge, **kwargs)
        if not ret:
            self.__logger.error('platform init failed: %s', err_info)
            return False, err_info

        self.__logger.info("platform init successful")
        self.__contactState = [None] * self.GetMaxContact()
        self.__adb_client = ADBClient(serial)
        return True, str()

    def DeInitialize(self):
        self.__platformInstance.deinit()
        return True

    def GetFrame(self):
        err_code, img_data = self.__platformInstance.get_image()
        if err_code != 0:
            self.__logger.error('Get frame failed, error code:%s', err_code)

        return err_code, img_data

    def Down(self, px, py, contact=0, pressure=50):
        self.__platformInstance.touch_down(px, py, contact, pressure)
        self.__contactState[contact] = (px, py)

    def Up(self, contact=0):
        self.__platformInstance.touch_up(contact)
        self.__contactState[contact] = None

    def Move(self, px, py, contact=0, pressure=50):
        self.__platformInstance.touch_move(px, py, contact, pressure)
        if self.__contactState[contact] is not None:
            self.__contactState[contact] = (px, py)
        else:
            self.__logger.warning('contact(%s) not down when move to ((%s), (%s))', contact, px, py)

    def SwipeMove(self, px, py, contact=0, duration_ms=50, pressure=50):
        if self.__contactState[contact] is not None:
            self._AddPoint(self.__contactState[contact][0],
                           self.__contactState[contact][1],
                           px,
                           py,
                           contact,
                           duration_ms,
                           pressure)
        else:
            self.__logger.warning('contact %s not down when swipemove to (%s, %s)', contact, px, py)

    def Click(self, px, py, contact=0, duration_ms=-1, pressure=50):
        if duration_ms < 0:
            duration_ms = 50

        self.Down(px, py, contact, pressure)
        self.Wait(duration_ms)
        self.Up(contact)

    def UpAll(self):
        for contact in range(self.GetMaxContact()):
            self.Up(contact)

    def SwipeDownMoveUp(self, sx, sy, ex, ey, contact=0, duration_ms=50, pressure=50):
        self.Up(contact)
        self.Down(sx, sy, contact, pressure)
        self.Wait(WAITTIME_POINT)
        self._AddPoint(sx, sy, ex, ey, contact, duration_ms, pressure)
        self.Up(contact)

    def SwipeDownMove(self, sx, sy, ex, ey, contact=0, duration_ms=50, pressure=50):
        self.Up(contact)
        self.Down(sx, sy, contact, pressure)
        self.Wait(WAITTIME_POINT)
        self._AddPoint(sx, sy, ex, ey, contact, duration_ms, pressure)

    def Wait(self, waitMS):
        self.__platformInstance.touch_wait(waitMS)

    def GetScreenResolution(self):
        device_info, err_info = self.__platformInstance.get_device_info()
        if device_info is None:
            return -1, -1, err_info

        return device_info.display_height, device_info.display_width, str()

    def GetMaxContact(self):
        device_info, err_info = self.__platformInstance.get_device_info()
        if device_info is None:
            raise Exception("get contact number failed, error msg:%s" % err_info)

        return device_info.touch_slot_number

    def Reset(self):
        self.__platformInstance.touch_reset()

    def Finish(self):
        self.__platformInstance.touch_finish()

    def InstallAPP(self, APKPath):
        raise NotImplementedError

    def LauchAPP(self, PackageName, ActivityName):
        raise NotImplementedError

    def ExitAPP(self, PackageName):
        raise NotImplementedError

    def CurrentApp(self):
        raise NotImplementedError

    def ClearAppData(self, appPackageName):
        raise NotImplementedError

    def Key(self, key):
        self.__adb_client.input_keys(key)

    def Text(self, text):
        self.__adb_client.input_keys(text)

    def Sleep(self):
        raise NotImplementedError

    def Wake(self):
        raise NotImplementedError

    def WMSize(self):
        raise NotImplementedError

    def TakeScreenshot(self, targetPath):
        raise NotImplementedError

    def GetScreenOri(self):
        raise NotImplementedError

    def ADBClick(self, px, py):
        raise NotImplementedError

    def ADBSwipe(self, sx, sy, ex, ey, duration_ms=50):
        raise NotImplementedError

    def DeviceParam(self, packageName):
        raise NotImplementedError

    def _AddPoint(self, sx, sy, ex, ey, contact=0, duration_ms=50, pressure=50):
        beginPoint = np.array([sx, sy])
        targetPoint = np.array([ex, ey])
        numMovingPoints = int(duration_ms / WAITTIME_POINT)
        movingX = np.linspace(beginPoint[0], targetPoint[0], numMovingPoints).astype(int)
        movingY = np.linspace(beginPoint[1], targetPoint[1], numMovingPoints).astype(int)

        for i in range(numMovingPoints - 1):
            self.Move(movingX[i + 1], movingY[i + 1], contact=contact, pressure=pressure)
            self.Wait(WAITTIME_POINT)
