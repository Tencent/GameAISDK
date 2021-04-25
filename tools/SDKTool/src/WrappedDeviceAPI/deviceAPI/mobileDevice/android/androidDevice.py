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
from logging.handlers import RotatingFileHandler

import cv2

from .androidDeviceAPI import AndroidDeviceAPI
from .APIDefine import LOG_DEBUG, LOG_DEFAULT, TOUCH_CMD_LIST, DEVICE_CMD_LIST, TOUCH_KEY, \
    TOUCH_CLICK, TOUCH_UP, TOUCH_MOVE, TOUCH_DOWN, TOUCH_SWIPE, TOUCH_SWIPEMOVE, TOUCH_RESET, DEVICE_KEY, \
    DEVICE_CLICK, DEVICE_CLEARAPP, DEVICE_CURAPP, DEVICE_EXIT, DEVICE_INSTALL, DEVICE_START, \
    DEVICE_TEXT, DEVICE_SCREENORI, DEVICE_SCREENSHOT, DEVICE_MAXCONTACT, DEVICE_PARAM, DEVICE_SLEEP, \
    DEVICE_SWIPE, DEVICE_WAKE, DEVICE_WMSIZE, LOG_LIST, LOG_FORMAT

from ...iDevice import IDevice

cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cur_dir)
PP_RET_OK = 0


class AndroidDevice(IDevice):
    def __init__(self, platform_type):
        super(AndroidDevice, self).__init__(platform_type)
        self.__deviceApi = AndroidDeviceAPI(platform_type)
        self.__height = -1
        self.__width = -1
        self.__pid = os.getpid()
        self.__serial = '*'
        self.__showScreen = False
        self.__maxContact = 10
        self.__logger = None

    def initialize(self, log_dir, **kwargs):
        """
        :param device_serial: str, 手机序列号,默认为None，当接入一个设备时可不指定序列号，当接入多个设备时需要指定
        :param long_edge: int, 长边的长度
        :param log_dir: str, 日志存放目录
        :param level: enum, 指定日志级别，
                      取值为[LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_CRITICAL]，默认为LOG_DEBUG
        :param show_raw_screen: bool, 是否显示手机图片
        :param kwargs: dict, 一些组件需要的参数，可以自己定义，例如端口号等等
        """
        level = kwargs.pop('level') if 'level' in kwargs else logging.DEBUG
        long_edge = kwargs.pop('long_edge') if 'long_edge' in kwargs else 1280
        device_serial = kwargs.pop('device_serial') if 'device_serial' in kwargs else None
        show_raw_screen = kwargs.pop('show_raw_screen') if 'show_raw_screen' in kwargs else False

        if device_serial is not None:
            log_dir = os.path.join(log_dir, device_serial.replace(':', "_")) + os.path.sep
            self.__serial = device_serial
            if not self._LogInit(log_dir, level, device_serial):
                raise RuntimeError("init log failed")
        else:
            log_dir = os.path.join(log_dir, LOG_DEFAULT) + os.path.sep
            if not self._LogInit(log_dir, level, LOG_DEFAULT):
                raise RuntimeError("init log failed")

        kwargs['standalone'] = 0 if os.environ.get("PLATFORM_IP") else 1
        if not self.__deviceApi.Initialize(device_serial, long_edge, **kwargs):
            self.__logger.error('DeviceAPI initial failed')
            raise RuntimeError("DeviceAPI initial failed")
        self.__showScreen = show_raw_screen
        self.__maxContact = self.__deviceApi.GetMaxContact()
        self.__height, self.__width, strError = self.__deviceApi.GetScreenResolution()
        if self.__height == -1 and self.__width == -1:
            self.__logger.error(strError)
            raise RuntimeError(strError)

        height = long_edge
        width = self.__width * height / self.__height

        self.__width = width
        self.__height = height
        self.__logger.info("init successful")
        return True

    def deInitialize(self):
        return self.__deviceApi.DeInitialize()

    def getScreen(self, **kwargs):
        """
        :return: Mat类型的图像/None
        """
        err, image = self.__deviceApi.GetFrame()
        if err != PP_RET_OK:
            self.__logger.error('failed to get frame')
            return None

        if image is not None and self.__showScreen:
            self.__logger.info("get image")
            cv2.imshow('pid:' + str(self.__pid) + ' serial:' + str(self.__serial), image)
            cv2.waitKey(1)
        return image

    def doAction(self, **kwargs):
        aType = kwargs['aType']
        if aType in TOUCH_CMD_LIST:
            return self.TouchCMD(**kwargs)
        if aType in DEVICE_CMD_LIST:
            return self.DeviceCMD(**kwargs)
        raise Exception("unknown action type: %s, %s", aType, kwargs)

    def TouchCMD(self, **kwargs):
        """ 执行操作

        :kwargs: dict,
            aType参数表示动作类型[TOUCH_CLICK, TOUCH_DOWN, TOUCH_UP, TOUCH_SWIPE, TOUCH_MOVE]
            sx为x坐标，当aType为[TOUCH_CLICK, TOUCH_DOWN]时表示按压点的x坐标，
                当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示起始点的x坐标
            sy为y坐标，当aType为[TOUCH_CLICK, TOUCH_DOWN]时表示按压点的y坐标，
                当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示起始点的y坐标
            ex为x坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示结束点的x坐标
            ex为y坐标，当aType为[TOUCH_SWIPE, TOUCH_MOVE]时表示结束点的y坐标
            DaType为执行该操作的方式，有minitouch方式和ADB命令方式，分别表示为[DACT_TOUCH, DACT_ADB]，默认为DACT_TOUCH
            contact为触点，默认为0
            durationMS为执行一次动作持续的时间，在aType为[TOUCH_CLICK, TOUCH_SWIPE]时使用，
                当aType为TOUCH_CLICK时默认为-1，当aType为TOUCH_SWIPE时默认为50
            needUp仅在aType为TOUCH_SWIPE时使用，表示滑动后是否需要抬起，默认为True
        :return: True or False
        """
        for key in kwargs:
            if key not in TOUCH_KEY:
                self.__logger.error('wrong key of kwargs: %s', key)
                return False

        actionType = kwargs.get('aType')
        if not actionType:
            self.__logger.error('aType is needed when exec TouchCommand')
            return False

        px = sx = kwargs.get('sx', None)
        py = sy = kwargs.get('sy', None)
        ex = kwargs.get('ex', None)
        ey = kwargs.get('ey', None)
        contact = kwargs.get('contact', 0)
        durationMS = kwargs.get('durationMS', 0)
        needUp = kwargs.get('needUp', True)
        wait_time = kwargs.get('wait_time', 0)

        if actionType == TOUCH_CLICK:
            self.__logger.info("platform Click, x: %s, y: %s, contact: %s, durationMS: %s, waitTime: %s",
                               px,
                               py,
                               contact,
                               durationMS,
                               wait_time)
            self.__deviceApi.Click(px, py, contact, durationMS, wait_time)

        elif actionType == TOUCH_DOWN:
            self.__logger.info(
                "platform Down, x: %s, y: %s, contact: %s, waitTime: %s", px, py, contact, wait_time)
            self.__deviceApi.Down(px, py, contact, wait_time)

        elif actionType == TOUCH_UP:
            self.__logger.info("platform Up, contact: %s, waitTime: %s", contact, wait_time)
            self.__deviceApi.Up(contact, wait_time)

        elif actionType == TOUCH_SWIPE:
            if durationMS <= 0:
                durationMS = 50
            self.__logger.info("platform Swipe, sx: %s, sy: %s, ex: %s, ey: %s, "
                               "contact: %s, durationMS: %s, waitTime: %s",
                               sx,
                               sy,
                               ex,
                               ey,
                               contact,
                               durationMS,
                               wait_time)
            self.__deviceApi.Swipe(sx, sy, ex, ey, contact, durationMS, needUp, wait_time)

        elif actionType == TOUCH_MOVE:
            self.__logger.info(
                "platform Move, x: %s, y: %s, contact: %s, waitTime: %s", px, py, contact, wait_time)
            self.__deviceApi.Move(px, py, contact, wait_time)

        elif actionType == TOUCH_SWIPEMOVE:
            if durationMS <= 0:
                durationMS = 50
            self.__logger.info(
                "platform SwipeMove, px: %s, py: %s, contact: %s, durationMS: %s waitTime: %s", px,
                                                                                                py,
                                                                                                contact,
                                                                                                durationMS,
                                                                                                wait_time)
            self.__deviceApi.SwipeMove(px, py, contact, durationMS, wait_time)

        elif actionType == TOUCH_RESET:
            self.__logger.info("platform Reset, waitTime: %s", wait_time)
            self.__deviceApi.Reset(wait_time=wait_time)

        else:
            self.__logger.error('Wrong aType when TouchCommand, aType:%s', actionType)
            return False

        return True

    def DeviceCMD(self, **kwargs):
        """ 执行设备相关的操作

        aType:操作类型[DEVICE_INSTALL, DEVICE_START, DEVICE_EXIT, DEVICE_CURAPP, DEVICE_CLEARAPP, DEVICE_KEY,
                      DEVICE_TEXT, DEVICE_SLEEP, DEVICE_WAKE, DEVICE_WMSIZE, DEVICE_BINDRO, DEVICE_SCREENSHOT,
                      DEVICE_SCREENORI, DEVICE_PARAM]
        APKPath:安装包路径
        PKGName：包名
        ActivityName：包的activity
        key：字母
        text：键盘输入的字符串
        """
        actionType = kwargs.get('aType')
        if not actionType:
            self.__logger.error('aType is needed when exec DeviceCommand')
            return False

        if actionType == DEVICE_INSTALL:
            APKPath = kwargs.get('APKPath', None)
            if not self.__deviceApi.InstallAPP(APKPath):
                self.__logger.error('install app failed: %s', APKPath)
                return False

        elif actionType == DEVICE_START:
            PKGName = kwargs.get('PKGName', None)
            ActivityName = kwargs.get('ActivityName', None)
            self.__deviceApi.LaunchAPP(PKGName, ActivityName)

        elif actionType == DEVICE_EXIT:
            PKGName = kwargs.get('PKGName', None)
            self.__deviceApi.ExitAPP(PKGName)

        elif actionType == DEVICE_CURAPP:
            return self.__deviceApi.CurrentApp()

        elif actionType == DEVICE_CLEARAPP:
            PKGName = kwargs.get('PKGName', None)
            self.__deviceApi.ClearAppData(PKGName)

        elif actionType == DEVICE_KEY:
            key = kwargs.get('key', None)
            self.__deviceApi.Key(key)

        elif actionType == DEVICE_TEXT:
            text = kwargs.get('text', None)
            self.__deviceApi.Text(text)

        elif actionType == DEVICE_SLEEP:
            self.__deviceApi.Sleep()

        elif actionType == DEVICE_WAKE:
            self.__deviceApi.Wake()

        elif actionType == DEVICE_WMSIZE:
            return self.__deviceApi.WMSize()

        elif actionType == DEVICE_SCREENSHOT:
            targetPath = kwargs.get('targetPath', None)
            self.__deviceApi.TakeScreenshot(targetPath)

        elif actionType == DEVICE_SCREENORI:
            return self.__deviceApi.GetScreenOri()

        elif actionType == DEVICE_MAXCONTACT:
            return self.__maxContact

        elif actionType == DEVICE_CLICK:
            px = kwargs.get('sx', None)
            py = kwargs.get('sy', None)
            self.__deviceApi.ADBClick(px, py)

        elif actionType == DEVICE_SWIPE:
            sx = kwargs.get('sx', None)
            sy = kwargs.get('sy', None)
            ex = kwargs.get('ex', None)
            ey = kwargs.get('ey', None)
            durationMS = kwargs.get('durationMS', 50)
            self.__deviceApi.ADBSwipe(sx, sy, ex, ey, durationMS=durationMS)

        elif actionType == DEVICE_PARAM:
            packageName = kwargs.get('PKGName', None)
            return self.__deviceApi.GetDeviceParame(packageName)

        else:
            self.__logger.error('wrong aType when exec DeviceCommand, aType:%s', actionType)
            return False

        return True

    # def _GetValuesInkwargs(self, key, isNessesary, defaultValue, kwargs):
    #     try:
    #         if not isNessesary:
    #             if key not in kwargs:
    #                 return True, defaultValue
    #             else:
    #                 return True, kwargs[key]
    #         else:
    #             return True, kwargs[key]
    #     except KeyError as e:
    #         self.__logger.error(e)
    #         return False, 'key error'

    def _LogInit(self, log_dir, level, device_serial):
        if not isinstance(log_dir, str):
            logging.error('wrong log_dir when init LOG, log_dir:%s', log_dir)
            return False

        if level not in LOG_LIST:
            logging.warning('wrong level when init LOG, level:%s, use default level: DEBUG', level)
            level = LOG_DEBUG

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.__logger = logging.getLogger(device_serial)
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

        loggerWeTest = logging.getLogger('PlatformWeTest')
        if not loggerWeTest.handlers:
            fileHandler = RotatingFileHandler(filename=os.path.join(log_dir, 'PlatformWeTest.log'),
                                              maxBytes=2048000,
                                              backupCount=10)
            fileHandler.setFormatter(formatter)
            loggerWeTest.addHandler(fileHandler)
            loggerWeTest.setLevel(level)
        return True

    # def _CheckException(self):
    #     if exceptionQueue.empty() is False:
    #         errorStr = exceptionQueue.get()
    #         while exceptionQueue.empty() is False:
    #             errorStr = exceptionQueue.get()
    #         raise Exception(errorStr)
