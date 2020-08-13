/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef UI_DEFINE_H_
#define UI_DEFINE_H_


#ifndef GAME_DEBUG_DUMP_UI
#define GAME_DEBUG_DUMP_UI 1
#endif // GAME_DEBUG_DUMP_UI

#ifdef LINUX
#define GAME_UI_SAMPLE_DATA_PATH "data/sample/"
#else
#define GAME_UI_SAMPLE_DATA_PATH "../../../Data/"
#endif // LINUX

#ifndef GAME_UI_CHECK_INTERVAL
#if NO_TBUS
#define GAME_UI_CHECK_INTERVAL 40
#else
#define GAME_UI_CHECK_INTERVAL 20
#endif // NO_TBUS
#endif // GAME_UI_CHECK_INTERVAL

#define UI_PLATFORM_CFG "../cfg/platform/UI.ini"

#define UI_TASK_CFG_FILE "cfg/task/ui/UIConfig.json"

#define GAME_DATA_ENV_VAR      "AI_SDK_PATH"
#define TBUS_CONFIG_FILE       "../cfg/platform/bus.ini"
#define UI_TBUS_ADDR_NAME      "UI1Addr"
#define SDKTOOL_TBUS_ADDR_NAME "SDKToolAddr"


#define DEFAULT_UI_LOG_FILE "../log/UIRecognize/UIRecognize.log"


#ifndef GAME_UI_DIALOG_CHECK_INTERVAL_UI
#define GAME_UI_DIALOG_CHECK_INTERVAL_UI (GAME_UI_CHECK_INTERVAL / 4)
#endif // GAME_UI_DIALOG_CHECK_INTERVAL_UI

#ifndef GAME_UI_DIALOG_CHECK_INTERVAL_AI
#define GAME_UI_DIALOG_CHECK_INTERVAL_AI (GAME_UI_CHECK_INTERVAL * 4)
#endif // GAME_UI_DIALOG_CHECK_INTERVAL_AI

#ifndef GAME_UI_DIALOG_ID
#define GAME_UI_DIALOG_ID 0x80000000
#endif // GAME_UI_DIALOG_ID

#define GAME_UI_DIALOG_SIZE_RATIO   0.8f
#define GAME_UI_DIALOG_BLOCK_WIDTH  8
#define GAME_UI_DIALOG_BLOCK_HEIGHT 4

#define GAME_UI_START_STATES 128
#define GAME_UI_END_STATES   128

#define GAME_UI_CACHED_FRAME_SIZE   32
#define GAME_UI_CACHED_FRAME_WIDTH  64
#define GAME_UI_CACHED_FRAME_HEIGHT 64

#define CHECK_SAME_UI_FRAME_CNT 5

#define YOLO_CFG_FILE    "../data/ButtonModel/yolov3-800.cfg"
#define YOLO_WEIGHT_FILE "../data/ButtonModel/yolov3-800_40000.weights"
#define YOLO_NAME_FILE   "../data/ButtonModel/UI.names"
#define YOLO_RETURN_NAME "return"
#define YOLO_CLOSE_NAME  "close"


#define NUM_CAND_NUM 2

#ifndef GAME_UI_TEMPLATE_NUM
#define GAME_UI_TEMPLATE_NUM 32
#endif // GAME_UI_TEMPLATE_NUM

#ifndef GAME_UI_SCRIPT_TASK_NUM
#define GAME_UI_SCRIPT_TASK_NUM 20
#endif // GAME_UI_SCRIPT_TASK_NUM


#define NUM_CAND_NUM 2

#ifndef GAME_UI_TEMPLATE_NUM
#define GAME_UI_TEMPLATE_NUM 32
#endif // GAME_UI_TEMPLATE_NUM

#ifndef GAME_UI_SCRIPT_TASK_NUM
#define GAME_UI_SCRIPT_TASK_NUM 20
#endif // GAME_UI_SCRIPT_TASK_NUM

#ifndef GAME_TEMPLATE_THRESHOLD
#define GAME_TEMPLATE_THRESHOLD 0.7f
#endif // GAME_TEMPLATE_THRESHOLD

#define NUM_CAND_NUM 2

#ifndef GAME_UI_TEMPLATE_NUM
#define GAME_UI_TEMPLATE_NUM 32
#endif // GAME_UI_TEMPLATE_NUM

#ifndef GAME_UI_SCRIPT_TASK_NUM
#define GAME_UI_SCRIPT_TASK_NUM 20
#endif // GAME_UI_SCRIPT_TASK_NUM

#ifndef GAME_TEMPLATE_THRESHOLD
#define GAME_TEMPLATE_THRESHOLD 0.7f
#endif // GAME_TEMPLATE_THRESHOLD

#endif // UI_DEFINE_H_
