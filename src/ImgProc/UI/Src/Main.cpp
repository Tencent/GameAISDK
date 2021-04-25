/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <signal.h>
#include "UI/Src/UIFrameWork.h"
#include "Comm/Utils/TqcCommon.h"

#define SIGUSR1 10
#define SIGUSR2 12

char* g_rootDataPath = NULL;
char* g_userCfgPath = NULL;
int          g_nMaxResultSize = 1;
CUIFrameWork *g_poFramework = NULL;
bool         g_bExit = false;

extern CDataManager  g_dataMgr;
extern CPBMsgManager g_pbMsgMgr;


// SIGUSR1, SIGUSR2, SIGINT 信号处理函数
static void SigHandle(int iSigNo) {
    if (iSigNo == SIGUSR1 || iSigNo == SIGUSR2 || iSigNo == SIGINT) {
        LOGI("UIRecongnize exist, receieve signo %d", iSigNo);
        g_bExit = true;
        g_dataMgr.SetExit(true);
        g_pbMsgMgr.SetExit(true);
    }

    return;
}

// 输入参数提示
void Help(const char *strProgName) {
    LOGI("Running program %s error. format show as follow", strProgName);
    LOGI("%s mode SDKTool loglevel DEBUG/INFO/WARN/ERROR cfgpath /workspace/project/", strProgName);
}

// 输入参数解析
bool ParseArg(int argc, char *argv[]) {
    if (NULL == g_poFramework) {
        LOGE("g_poFramework is NULL, please check");
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
            if (0 == strcmp(argv[i + 1], "SDKTool"))
                g_poFramework->SetTestMode(SDKTOOL_TEST);
            LOGI("Run SDKTool Test Model");
        } else if (0 == strcmp(argv[i], "cfgpath")) {
            char cBuffDir[1024] = { 0 };
            GetPathDir(argv[i + 1], cBuffDir);
            memcpy(g_userCfgPath, cBuffDir, 1024);
            LOGI("use cfgpath, %s", g_userCfgPath);
        } else if (0 == strcmp(argv[i], "loglevel")) {
            // 如果加参数"DEBUG",则日志级别为DEBUG
            CLog *pLog = CLog::getInstance();
            g_logLevel = pLog->getLogLevel(argv[i + 1]);
            LOGI("log level: %s", argv[i + 1]);
        }
    }
    return true;
}

int main(int argc, char *argv[]) {
    g_poFramework = new CUIFrameWork();
    if (NULL == g_poFramework) {
        LOGE("new UIFrameWork failed");
        return -1;
    }

    signal(SIGUSR1, SigHandle);
    signal(SIGUSR2, SigHandle);
    signal(SIGINT, SigHandle);

    g_rootDataPath = new char[1024];
    memset(g_rootDataPath, 0, 1024);
    g_userCfgPath = new char[1024];
    memset(g_userCfgPath, 0, 1024);


    // 系统配置文件路径，
    memcpy(g_rootDataPath, SYS_CONFIG_DIR, 1024);

    // 解析输入参数
    bool isOk = ParseArg(argc, argv);
    if (!isOk) {
        return -1;
    }

    if (NULL == g_userCfgPath) {
        memcpy(g_userCfgPath, DEFAULT_USER_CONFIG_DIR, 1024);
        LOGI("use default config path, %s", g_userCfgPath);
    }
    LOGI("root path is %s", g_rootDataPath);
    LOGI("user cfg path is %s", g_userCfgPath);
    try {
        // 设置数据管理模块和消息管理模块
        g_poFramework->SetDataMgr(&g_dataMgr);
        g_poFramework->SetMsgMgr(&g_pbMsgMgr);
        // 初始化 framework(平台配置，游戏UI配置，识别器，消息管理模块，数据模块，执行动作等)
        bool bRst = g_poFramework->Initialize(g_rootDataPath, g_userCfgPath);
        if (!bRst) {
            LOGE("frame work init failed");
            return -1;
        }

        // 注册MC， 循环处理图像，反注册MC
        g_poFramework->Run();

        // 释放资源
        g_poFramework->Release();
    }
    // 捕获异常
    catch (...) {
        LOGE("catch an exception error");
    }
    delete g_poFramework;
    return 0;
}
