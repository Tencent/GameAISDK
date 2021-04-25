/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

#include "Comm/Utils/Log.h"
#include "Comm/Utils/TSingleton.h"
#include "Comm/Utils/TqcCommon.h"
#include "GameRecognize/src/GameRegFrameWork.h"

using namespace std;

#define SIGUSR1 10
#define SIGUSR2 12


// LockFree::LockFreeQueue<CTaskResult> g_oTaskResultQueue;
ThreadSafeQueue<CTaskResult> g_oTaskResultQueue;
std::string                  g_strBaseDir = "../";
std::string                  g_userCfgPath = "../tools/SDKTool/project/TTKP";
std::string                  g_userCfgFilePath = "";

int                          g_nMaxResultSize = 5;


static CGameRegFrameWork *gs_poFramework = NULL;

// 信号处理函数，收到信号(SIGUSR1， SIGUSR2， SIGINT)时退出
static void SigHandle(int iSigNo) {
    if (iSigNo == SIGUSR1 || iSigNo == SIGUSR2 || iSigNo == SIGINT) {
        gs_poFramework->SetExited();
    }
    return;
}

// 输入参数提示
void Help(const char *strProgName) {
    LOGI("Running program %s error. format show as follow", strProgName);
    LOGI("%s mode SDKTool/video loglevel DEBUG/INFO/WARN/ERROR cfgpath /workspace/project/",
        strProgName);
}

// 输出参数解析
bool ParseArg(int argc, char *argv[]) {
    if (NULL == gs_poFramework) {
        LOGE("gs_poFramework is NULL, please check");
        return false;
    }
    if (1 == argc) {
        // 不加任何参数，默认启动的为SDK模式
        LOGI("Run SDK Model");
        return true;
    }
    if (0 == argc % 2) {
        LOGE("args error, please check");
        Help(argv[0]);
        return false;
    }
    for (int i = 1; i < argc; i += 2) {
        if (0 == strcmp(argv[i], "mode")) {
            // 如果加参数"SDKTool",启动的为 与SDKTool的调试模式
            if (0 == strcmp(argv[i + 1], "SDKTool")) {
                gs_poFramework->SetTestMode(true, SDKTOOL_TEST);
                LOGI("Run SDKTool Test Model");
            } else if (0 == strcmp(argv[i + 1], "video")) {
                gs_poFramework->SetTestMode(true, VIDEO_TEST);
                LOGI("Run VIDEO Test Model");
            }
        } else if (0 == strcmp(argv[i], "cfgpath")) {
            char cBuffDir[1024] = { 0 };
            g_userCfgFilePath = std::string(argv[i + 1]);
            GetPathDir(argv[i + 1], cBuffDir);

            g_userCfgPath = std::string(cBuffDir);

            // g_userCfgPath = argv[i + 1];
            LOGI("use cfgpath, %s", g_userCfgPath.data());
        } else if (0 == strcmp(argv[i], "loglevel")) {
            CLog *pLog = CLog::getInstance();
            g_logLevel = pLog->getLogLevel(argv[i + 1]);
            LOGI("log level: %s", argv[i + 1]);
        }
    }
    return true;
}


int main(int argc, char *argv[]) {
    LOGI("root dir:%s", g_strBaseDir.data());

    gs_poFramework = new CGameRegFrameWork();
    if (NULL == gs_poFramework) {
        LOGE("new GameRegFrameWork failed");
    }

    // 解析参数
    bool isOk = ParseArg(argc, argv);
    if (!isOk) {
        return -1;
    }

    g_userCfgPath = g_userCfgPath.append("/");
    LOGI("user config path:%s", g_userCfgPath.data());


    try {
        // 初始化Framework
        if (0 == gs_poFramework->Initialize((char*)g_strBaseDir.data(),
            (char*)g_userCfgFilePath.data())) {
            signal(SIGUSR1, SigHandle);
            signal(SIGUSR2, SigHandle);
            signal(SIGINT, SigHandle);

            // 运行
            if (-1 == gs_poFramework->Run()) {
                LOGE("run failed");
            }
        } else {
            LOGE("Init GameRegFrameWork failed");
        }

        // 释放资源
        gs_poFramework->Release();
    }
    catch (...) {
        LOGE("catch an exception error");
    }

    delete gs_poFramework;
    LOGI("=================GameReg exit===================");

#ifdef WINDOWS
    system("pause");
#endif  // WINDOWS

    return    0;
}
/*! @} */
