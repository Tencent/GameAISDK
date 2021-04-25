# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler

from .windowsDeviceAPI import WindowsDeviceAPI
from .APIDefine import KEYBOARD_CMD_LIST, MOUSE_CMD_LIST, KEY_INPUT, KEY_INPUTSTRING, MOUSE_MOVE, MOUSE_CLICK, \
    MOUSE_DOUBLECLICK, MOUSE_RIGHTCLICK, MOUSE_LONGCLICK, MOUSE_DRAG, LOG_DEFAULT, LOG_FORMAT, KEY_PRESS, KEY_RELEASE
from ...iDevice import IDevice


cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cur_dir)


class WindowsDevice(IDevice):
    def __init__(self, platform):
        IDevice.__init__(self, platform)
        self.__logger = None
        self.__deviceApi = WindowsDeviceAPI(platform)

    def initialize(self, log_dir, **kwargs):
        level = kwargs.pop('level') if 'level' in kwargs else logging.DEBUG
        hwnd = kwargs.pop('hwnd') if 'hwnd' in kwargs else None
        query_path = kwargs.pop('query_path') if 'query_path' in kwargs else None
        window_size = kwargs.pop('window_size') if 'window_size' in kwargs else None

        if not self._LogInit(log_dir, level):
            raise RuntimeError("init log failed")

        self.__deviceApi.Initialize(hwnd=hwnd, query_path=query_path, window_size=window_size, **kwargs)
        hwnd = self.__deviceApi.window_handle
        if hwnd:
            self.__logger.info("find window: %x", hwnd)
        self.__logger.info("logging start")
        return True

    def deInitialize(self):
        return self.__deviceApi.DeInitialize()

    def getScreen(self, **kwargs):
        img = self.__deviceApi.ScreenCap(**kwargs)
        return img

    def doAction(self, **kwargs):
        aType = kwargs['aType']
        if aType in KEYBOARD_CMD_LIST:
            return self.keyboardCMD(**kwargs)
        if aType in MOUSE_CMD_LIST:
            return self.mouseCMD(**kwargs)
        raise Exception("unknown action type: %s, %s" % (aType, kwargs))

    def keyboardCMD(self, **kwargs):
        try:
            aType = kwargs['aType']
            keys = kwargs.get('keys', None)
            key_string = kwargs.get('key_string', None)
            long_click_time = kwargs.get('long_click_time', 0)

            if aType == KEY_INPUT:
                self.__logger.info("key input, keys: %s", keys)
                self.__deviceApi.InputKeys(keys, long_click_time)

            elif aType == KEY_INPUTSTRING:
                self.__logger.info("key input string, key_string: %s", key_string)
                self.__deviceApi.InputStrings(key_string)

            elif aType == KEY_PRESS:
                self.__logger.info("key_press: %s", keys)
                self.__deviceApi.PressKey(keys)

            elif aType == KEY_RELEASE:
                self.__logger.info("key_release: %s", keys)
                self.__deviceApi.ReleaseKey(keys)

        except Exception as e:
            self.__logger.error('keyboardCMD error: %s', e)
            raise e

    def mouseCMD(self, **kwargs):
        try:
            aType = kwargs['aType']
            px = kwargs.get('px', None)
            py = kwargs.get('py', None)
            by_post = kwargs.get('by_post', False)
            long_click_time = kwargs.get('long_click_time', 0)
            fromX = kwargs.get('fromX', None)
            fromY = kwargs.get('fromY', None)
            toX = kwargs.get('toX', None)
            toY = kwargs.get('toY', None)

            if aType == MOUSE_MOVE:
                self.__logger.info("mouse move, px: %s, py: %s", px, py)
                self.__deviceApi.MouseMove(px, py)

            elif aType == MOUSE_CLICK:
                self.__logger.info("mouse click, px: %s, py: %s", px, py)
                self.__deviceApi.MouseClick(px, py, by_post)

            elif aType == MOUSE_DOUBLECLICK:
                self.__logger.info("mouse double click, px: %s, py: %s", px, py)
                self.__deviceApi.MouseDoubleClick(px, py)

            elif aType == MOUSE_RIGHTCLICK:
                self.__logger.info("mouse right click, px: %s, py: %s", px, py)
                self.__deviceApi.MouseRightClick(px, py)

            elif aType == MOUSE_LONGCLICK:
                self.__logger.info("mouse long click, px: %s, py: %s, long_click_time: %s",
                                   px,
                                   py,
                                   long_click_time)
                self.__deviceApi.MouseLongClick(px, py, long_click_time)
            elif aType == MOUSE_DRAG:
                self.__logger.info("mouse drag, fromX: %s, fromY: %s, toX: %s, toY: %s",
                                   fromX,
                                   fromY,
                                   toX,
                                   toY)
                self.__deviceApi.MouseDrag(fromX, fromY, toX, toY)
        except Exception as e:
            self.__logger.error('mouseCMD error: %s', e)
            raise e

    def _LogInit(self, log_dir, level):
        if not isinstance(log_dir, str):
            logging.error('wrong log_dir when init LOG, log_dir: %s', log_dir)
            return False

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.__logger = logging.getLogger(LOG_DEFAULT)
        if not self.__logger.handlers:
            console = logging.StreamHandler()
            formatter = logging.Formatter(LOG_FORMAT)
            console.setFormatter(formatter)
            fileHandler = RotatingFileHandler(filename=os.path.join(log_dir, 'DeviceAPI.log'),
                                              maxBytes=2048000,
                                              backupCount=10)
            fileHandler.setFormatter(formatter)
            self.__logger.addHandler(fileHandler)
            self.__logger.addHandler(console)
            self.__logger.setLevel(level)

        return True

    # def _GetValuesInkwargs(self, key, isNessesary, defaultValue, kwargs):
    #     try:
    #         if not isNessesary:
    #             if key not in kwargs:
    #                 return defaultValue
    #             else:
    #                 return kwargs[key]
    #         else:
    #             return kwargs[key]
    #     except KeyError as e:
    #         self.__logger.error(e)
    #         raise e
