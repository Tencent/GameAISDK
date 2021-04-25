/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_FRAMEWORKDEFINE_H_
#define GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_FRAMEWORKDEFINE_H_

#include <map>
#include <sstream>
#include <string>
#include <vector>

#include <opencv2/core/core.hpp>
#include <opencv2/core/version.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>

#if CV_VERSION_EPOCH == 2
#define OPENCV2
#elif CV_VERSION_MAJOR == 3
#define  OPENCV3
#else
#error Not support this OpenCV version
#endif

typedef std::vector<int> tagTaskElementArray;  // Task Element数组

enum ETestMode {
    SDK_TEST = 0,
    VIDEO_TEST = 1,
    SDKTOOL_TEST = 2,
};

// TaskID对应的task Element数组
struct tagTaskElements {
    int                 nObjTaskID;
    tagTaskElementArray nVecElements;
};

// refer任务ID 对应的游戏任务ID以及Element数组
typedef std::map<int, tagTaskElements>  tagReferObjTaskElements;

// 目标游戏任务ID对应的referID数组
typedef std::map<int, std::vector<int>> tagObjTaskReferID;

// 向MC发送TaskReport的标志
enum ESendTaskReportToMC {
    SEND_NO = 0,  // 不发送
    SEND_TRUE = 1,  // 发送成功
    SEND_FALSE = 2  // 发送失败
};

enum ETaskType {
    TYPE_REFER,
    TYPE_GAME
};

// 任务状态之一
enum ETaskExecState {
    TASK_STATE_WAITING,
    TASK_STATE_RUNNING,
    TASK_STATE_OVER
};

// 任务状态
struct tagTaskState {
    ETaskExecState eTaskExecState;
    bool           bState;

    tagTaskState() {
        bState = true;
        eTaskExecState = TASK_STATE_RUNNING;
    }

    bool IsActive() {
        if (bState && eTaskExecState == TASK_STATE_RUNNING) {
            return true;
        }

        return false;
    }
};

#define STANDARD_LONG_EDGE 1280

#define MEM_POOL_SIZE   1024 * 1024 * 512

#define LOOP_MAX_TIME  10000
#define LOOP_RUN_SLEEP 10

#define OUT_TIME 2000

/*#define GAMEREG_PLATFORM_PRE_CFG "../cfg/platform/gameReg.ini"
#define GAMEREG_PLATFORM_CFG "../cfg/platform/GameReg.ini"
#define TBUS_DIR "../cfg/platform/bus.ini"*/
#define GAMEREG_PLATFORM_PRE_CFG "cfg/platform/gameReg.ini"
#define GAMEREG_PLATFORM_CFG "cfg/platform/GameReg.ini"
#define TBUS_DIR "cfg/platform/bus.ini"

// #define GAMEREG_PLATFORM_PRE_LOG "../cfg/platform/gameReg_log.ini"
// #define GAMEREG_PLATFORM_LOG "../cfg/platform/GameRegLog.ini"

#define GAMEREG_TASKMGR_PRE_CFG  "cfg/task/gameReg/gameReg_mgr1.json"
#define GAMEREG_TASKMGR_CFG  "cfg/task/gameReg/GameRegMgr1.json"

#define PROJECT_CFG "prj.aisdk"

#define GAMEREG_TASK_CFG     "cfg/task/gameReg/task.json"
#define GAMEREG_REFER_CFG    "cfg/task/gameReg/refer.json"


#define KEY_MSG_ID    "msgID"
#define KEY_MSG_VALUE "value"

#define TQC_DELETE(ptr) {    \
        if ((ptr) != NULL) { \
            delete ((ptr)); \
            (ptr) = NULL;   \
        }                   \
}

inline std::string int2str(const int &nTemp) {
    std::stringstream stream;

    stream << nTemp;
    return stream.str();    // 此处也可以用 stream>>string_temp
}

inline int str2int(const std::string &strTemp) {
    std::stringstream stream(strTemp);
    int               nTemp;

    stream >> nTemp;
    return nTemp;
}

#endif  // GAME_AI_SDK_IMGPROC_GAMERECOGNIZE_FRAMEWORKDEFINE_H_
