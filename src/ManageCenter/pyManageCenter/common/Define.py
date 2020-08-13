# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

# 运行服务类型
RUN_TYPE_UI_AI = 'UI+AI'
RUN_TYPE_AI = 'AI'
RUN_TYPE_UI = 'UI'

# 结果流程类型
RESULT_TYPE_UI = 'UI'
RESULT_TYPE_AI = 'AI'

# 服务注册类型reg_type枚举
SERVICE_REGISTER = 0  # 注册
SERVICE_UNREGISTER = 1  # 反注册

# 服务节点类型service_type枚举
SERVICE_TYPE_AGENT = 0  # AGENT服务
SERVICE_TYPE_UI = 1  # UI服务
SERVICE_TYPE_REG = 2  # 游戏识别REG服务

# UI识别的游戏状态game_state枚举，语义和PB协议一致
GAME_STATE_NONE = 0
GAME_STATE_UI = 1
GAME_STATE_START = 2
GAME_STATE_OVER = 3
GAME_STATE_MATCH_WIN = 4

# 横竖屏枚举
UI_SCREEN_ORI_LANDSCAPE = 0
UI_SCREEN_ORI_PORTRAIT = 1

# 任务状态枚举
TASK_STATUS_NONE = -1
TASK_STATUS_INIT_SUCCESS = 0
TASK_STATUS_INIT_FAILURE = 1

# monitor位标识
ALL_NORMAL = 0b00000000
AGENT_EXIT = 0b00000001
REG_EXIT = 0b00000010
UI_EXIT = 0b00000100

AGENT_STATE_WAITING_START = 0
AGENT_STATE_PLAYING = 1
AGENT_STATE_PAUSE_PLAYING = 2
AGENT_STATE_RESTORE_PLAYING = 3
AGENT_STATE_OVER = 4
