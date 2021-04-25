# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

TOUCH_IP = '127.0.0.1'
TOUCH_PORT = 1112
LOG_DEFAULT = "default_device"
LOG_FORMAT = '[%(asctime)s][%(pathname)s:%(lineno)d][%(levelname)s] : %(message)s'

UI_SCREEN_ORI_LANDSCAPE = 0
UI_SCREEN_ORI_PORTRAIT = 1

WAITTIME_MS = 1
WAITTIME_POINT = 4
PLUGIN_TOUCH_DIR = '/Platform_plugin/'

TOUCH_KEY = [
    'aType',
    'sx',
    'sy',
    'ex',
    'ey',
    'contact',
    'durationMS',
    'wait_time',
    'needUp'
]

LOG_DEBUG = logging.DEBUG
LOG_INFO = logging.INFO
LOG_WARNING = logging.WARNING
LOG_ERROR = logging.ERROR
LOG_CRITICAL = logging.CRITICAL
LOG_LIST = [
    LOG_DEBUG,
    LOG_INFO,
    LOG_WARNING,
    LOG_ERROR,
    LOG_CRITICAL
]

TOUCH_CLICK = 'touch_click'
TOUCH_DOWN = 'touch_down'
TOUCH_UP = 'touch_up'
TOUCH_SWIPE = 'touch_swipe'
TOUCH_MOVE = 'touch_move'
TOUCH_RESET = 'touch_reset'
TOUCH_SWIPEMOVE = 'touch_swipemove'
TOUCH_CMD_LIST = [
    TOUCH_CLICK,
    TOUCH_DOWN,
    TOUCH_UP,
    TOUCH_SWIPE,
    TOUCH_MOVE,
    TOUCH_SWIPEMOVE,
    TOUCH_RESET
]

DEVICE_INSTALL = 'device_install'
DEVICE_START = 'device_start'
DEVICE_EXIT = 'device_exit'
DEVICE_CURAPP = 'device_current'
DEVICE_CLEARAPP = 'device_clear'
DEVICE_WAKE = 'device_wake'
DEVICE_SLEEP = 'device_sleep'
DEVICE_WMSIZE = 'device_wmsize'
DEVICE_BINDRO = 'device_bindrotation'
DEVICE_SCREENSHOT = 'device_screenshot'
DEVICE_SCREENORI = 'device_screenori'
DEVICE_KEY = 'device_key'
DEVICE_TEXT = 'device_text'
DEVICE_MAXCONTACT = 'device_maxcontact'
DEVICE_CLICK = 'device_click'
DEVICE_SWIPE = 'device_swip'
DEVICE_PARAM = 'device_param'
DEVICE_CMD_LIST = [
    DEVICE_INSTALL,
    DEVICE_START,
    DEVICE_EXIT,
    DEVICE_CURAPP,
    DEVICE_CLEARAPP,
    DEVICE_WAKE,
    DEVICE_SLEEP,
    DEVICE_WMSIZE,
    DEVICE_BINDRO,
    DEVICE_SCREENSHOT,
    DEVICE_SCREENORI,
    DEVICE_KEY,
    DEVICE_TEXT,
    DEVICE_MAXCONTACT,
    DEVICE_CLICK,
    DEVICE_SWIPE,
    DEVICE_PARAM
]


class DeviceKeys(object):
    HOME = "{HOME}"
    MENU = "{MENU}"
    BACK = "{BACK}"

PORTRAIT_UP = 0
LANDSCAPE_RIGHT = 1
PORTRAIT_DOWN = 2
LANDSCAPE_LEFT = 3
ROTATION_LIST = [
    PORTRAIT_UP,
    LANDSCAPE_RIGHT,
    PORTRAIT_DOWN,
    LANDSCAPE_LEFT
]
