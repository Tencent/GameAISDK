# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

LOG_FORMAT = '[%(asctime)s][%(pathname)s:%(lineno)d][%(levelname)s] : %(message)s'
LOG_DEFAULT = "default_device"

# keyboard operations
KEY_INPUT = 'key_input'
KEY_INPUTSTRING = 'key_inputstring'
KEY_LONGPRESS = 'key_longpress'
KEY_PRESS = 'key_press'
KEY_RELEASE = 'key_release'
# KEY_RELEASE_ALL = 'key_release_all'

# keyboard command list
KEYBOARD_CMD_LIST = [
    KEY_INPUT,
    KEY_INPUTSTRING,
    KEY_LONGPRESS,
    KEY_PRESS,
    KEY_RELEASE,
    # KEY_RELEASE_ALL
]

# mouse operations
MOUSE_MOVE = 'mouse_move'
MOUSE_PRESS = 'mouse_press'
MOUSE_RELEASE = 'mouse_release'
MOUSE_CLICK = 'mouse_click'
MOUSE_RIGHTCLICK = 'mouse_rightclick'
MOUSE_DOUBLECLICK = 'mouse_doubleclick'
MOUSE_LONGCLICK = 'mouse_longclick'
MOUSE_DRAG = 'mouse_drag'

# mouse command list
MOUSE_CMD_LIST = [
    MOUSE_MOVE,
    MOUSE_PRESS,
    MOUSE_RELEASE,
    MOUSE_CLICK,
    MOUSE_RIGHTCLICK,
    MOUSE_DOUBLECLICK,
    MOUSE_LONGCLICK,
    # MOUSE_LONGRIGHTCLICK,
    # MOUSE_SCROLL,
    MOUSE_DRAG
]
