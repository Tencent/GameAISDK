# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import time

from ...WrappedDeviceAPI.wrappedDeviceConfig import Platform, DeviceType
from ...WrappedDeviceAPI.deviceAPI.mobileDevice.android.APIDefine import TOUCH_CLICK, TOUCH_SWIPE, DEVICE_KEY
from ...WrappedDeviceAPI.deviceAdapter import DeviceAdapter
from ...common.singleton import Singleton
from ...context.app_context import g_app_context


logger = logging.getLogger("sdktool")


class DeviceActionType(object):
    CLICK = 0
    SLIDE = 1
    PRESS = 2
    MOVE = 3
    RELEASE = 4
    INPUT_KEY = 5
    INPUT_TEXT = 6

    # PRESS_HOME_KEY = 10
    # PRESS_BACK_KEY = 11
    # PRESS_MENU_KEY = 12
    DOUBLE_CLICK = 20
    RIGHT_CLICK = 21
    KEY_DOWN = 22
    KEY_UP = 23


class DeviceActionParamName(object):
    X = "x"
    Y = "y"
    FROM_X = "x1"
    FROM_Y = "y1"
    TO_X = "x2"
    TO_Y = "y2"
    KEY = "key"
    TEXT = "text"


class DataSource(metaclass=Singleton):
    def __init__(self):
        self.__phone = None
        self._device_type = DeviceType.Android

    def init_phone(self,
                   serial,
                   device_type=DeviceType.Android.value,
                   platform=Platform.Local.value,
                   long_edge=1280):
        """ 初始化设备实例

        :param serial:
        :param device_type:
        :param platform:
        :param long_edge:
        :return:
        """
        # 先关闭之前的链接(如果有的话)
        self.finish()
        ret = True
        self._device_type = device_type
        if self.__phone is None:
            # 根据现有的配置，重新进行初始化
            self.__phone = DeviceAdapter(device_type, platform=platform)
            if device_type == DeviceType.Windows.value:
                ret = self.__phone.initialize(hwnd=serial)
            else:
                ret = self.__phone.initialize(device_serial=serial,
                                              long_edge=long_edge,
                                              show_raw_screen=False)
            if ret:
                g_app_context.set_info('device_connected', True)
        return ret

    def get_frame(self):
        try:
            if self.__phone:
                frame = self.__phone.getScreen()
                return frame
        except RuntimeError as err:
            logger.error("err: %s", err)
        return None

    def do_action(self, action_type=DeviceActionType.CLICK, **kwargs):
        if self._device_type == DeviceType.Android.value:
            if action_type == DeviceActionType.CLICK:
                kwargs['sx'] = int(kwargs.pop(DeviceActionParamName.X))
                kwargs['sy'] = int(kwargs.pop(DeviceActionParamName.Y))
                self.__phone.doAction(aType=TOUCH_CLICK, **kwargs)

            elif action_type == DeviceActionType.SLIDE:
                kwargs['sx'] = int(kwargs.pop(DeviceActionParamName.FROM_X))
                kwargs['sy'] = int(kwargs.pop(DeviceActionParamName.FROM_Y))
                kwargs['ex'] = int(kwargs.pop(DeviceActionParamName.TO_X))
                kwargs['ey'] = int(kwargs.pop(DeviceActionParamName.TO_Y))
                self.__phone.doAction(aType=TOUCH_SWIPE, **kwargs)

            # elif action_type == DeviceActionType.PRESS:
            #     self.__phone.doAction(aType=TOUCH_DOWN, **kwargs)
            #
            # elif action_type == DeviceActionType.MOVE:
            #     self.__phone.doAction(aType=TOUCH_MOVE, **kwargs)
            #
            # elif action_type == DeviceActionType.RELEASE:
            #     self.__phone.doAction(aType=TOUCH_UP, **kwargs)

            elif action_type == DeviceActionType.INPUT_KEY or action_type == DeviceActionType.INPUT_TEXT:
                self.__phone.doAction(aType=DEVICE_KEY, **kwargs)

        elif self._device_type == DeviceType.Windows.value:
            # 无需在windows上进行操作
            pass
            # if action_type == DeviceActionType.CLICK:
            #     kwargs['px'] = int(kwargs.pop(DeviceActionParamName.X))
            #     kwargs['py'] = int(kwargs.pop(DeviceActionParamName.Y))
            #     kwargs['by_post'] = True
            #     self.__phone.doAction(aType=MOUSE_CLICK, **kwargs)
            #
            # elif action_type == DeviceActionType.SLIDE:
            #     kwargs['by_post'] = True
            #     kwargs['fromX'] = int(kwargs.pop(DeviceActionParamName.FROM_X))
            #     kwargs['fromY'] = int(kwargs.pop(DeviceActionParamName.FROM_Y))
            #     kwargs['toX'] = int(kwargs.pop(DeviceActionParamName.TO_X))
            #     kwargs['toY'] = int(kwargs.pop(DeviceActionParamName.TO_Y))
            #     self.__phone.doAction(aType=MOUSE_DRAG, **kwargs)

            # elif action_type == DeviceActionType.PRESS:
            #     self.__phone.doAction(aType=MOUSE_PRESS, **kwargs)
            #
            # elif action_type == DeviceActionType.MOVE:
            #     self.__phone.doAction(aType=MOUSE_MOVE, **kwargs)
            #
            # elif action_type == DeviceActionType.RELEASE:
            #     self.__phone.doAction(aType=MOUSE_RELEASE, **kwargs)
            #
            # elif action_type == DeviceActionType.INPUT_KEY:
            #     self.__phone.doAction(aType=KEY_INPUT, **kwargs)
            #
            # elif action_type == DeviceActionType.INPUT_TEXT:
            #     self.__phone.doAction(aType=KEY_INPUTSTRING, **kwargs)

            # elif action_type == DeviceActionType.KEY_DOWN:
            #     self.__phone.doAction(aType=KEY_PRESS, **kwargs)
            #
            # elif action_type == DeviceActionType.KEY_UP:
            #     self.__phone.doAction(aType=KEY_RELEASE, **kwargs)
            #
            # elif action_type == DeviceActionType.DOUBLE_CLICK:
            #     self.__phone.doAction(aType=MOUSE_DOUBLECLICK, **kwargs)
            #
            # elif action_type == DeviceActionType.RIGHT_CLICK:
            #     self.__phone.doAction(aType=MOUSE_RIGHTCLICK, **kwargs)
        else:
            raise ValueError('device type(%s) is not supported!' % self._device_type)

    @property
    def device(self):
        return self.__phone

    def finish(self):
        ret = True
        if self.__phone:
            ret = self.__phone.deInitialize()
            # 退出需要耗时, 等待1s中，
            time.sleep(1)
            self.__phone = None
        g_app_context.set_info('device_connected', False)
        return ret

    def is_valid(self):
        if self.__phone is None:
            return False
        return True


g_data_source = DataSource()
