/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <signal.h>
#include "UI/Src/UIFrameWork.h"

#define SIGUSR1 10
#define SIGUSR2 12

char         *g_rootDataPath  = NULL;
int          g_nMaxResultSize = 1;
CUIFrameWork *g_poFramework   = NULL;
bool         g_bExit          = false;

extern CDataManager  g_dataMgr;
extern CPBMsgManager g_pbMsgMgr;

// SIGUSR1, SIGUSR2, SIGINT 信号处理函数
static void SigHandle(int iSigNo)
{
    if (iSigNo == SIGUSR1 || iSigNo == SIGUSR2 || iSigNo == SIGINT)
    {
        LOGI("UIRecongnize exist, receieve signo %d", iSigNo);
        g_bExit = true;
        g_dataMgr.SetExit(true);
        g_pbMsgMgr.SetExit(true);
    }

    return;
}

// 输入参数提示
void Help(const char *strProgName)
{
    LOGI("Running program %s with the 0 or 1 arguments.", strProgName);
    LOGI("such as SDKTool.");
}

// 输入参数解析
bool ParseArg(int argc, char *argv[])
{
    if (NULL == g_poFramework)
    {
        LOGE("g_poFramework is NULL, please check");
        return false;
    }

    switch (argc)
    {
    // 不加任何参数，默认启动的为SDK模式
    case 1:
        LOGI("Run SDK Model");
        break;

    // 如果加参数"SDKTool",启动的为 与SDKTool的调试模式
    case 2:
        if (strcmp(argv[1], "SDKTool") == 0)
        {
            g_poFramework->SetTestMode(SDKTOOL_TEST);
            LOGI("Run SDKTool Test Model");
        }

        break;

    default:
        Help(argv[0]);
        break;
    }

    return true;
}

int main(int argc, char *argv[])
{
    g_poFramework = new CUIFrameWork();
    if (NULL == g_poFramework)
    {
        LOGE("new UIFrameWork failed");
        return -1;
    }

    signal(SIGUSR1, SigHandle);
    signal(SIGUSR2, SigHandle);
    signal(SIGINT, SigHandle);

    // 解析输入参数
    ParseArg(argc, argv);

    // 获取环境变量"GAME_DATA_ENV_VAR"
    g_rootDataPath = getenv(GAME_DATA_ENV_VAR);

    // 如果不存在环境变量，默认的用 AI SDK 内部的配置
    if (NULL == g_rootDataPath)
    {
        g_rootDataPath = "../";
    }

    LOGI("root path is %s\n", g_rootDataPath);
    try
    {
        // 设置数据管理模块和消息管理模块
        g_poFramework->SetDataMgr(&g_dataMgr);
        g_poFramework->SetMsgMgr(&g_pbMsgMgr);
        // 初始化 framework(平台配置，游戏UI配置，识别器，消息管理模块，数据模块，执行动作等)
        bool bRst = g_poFramework->Initialize(g_rootDataPath);
        if (!bRst)
        {
            LOGE("frame work init failed");
            return -1;
        }

        // 注册MC， 循环处理图像，反注册MC
        g_poFramework->Run();

        // 释放资源
        g_poFramework->Release();
    }
    // 捕获异常
    catch (...)
    {
        LOGE("catch an exception error");
    }
    delete g_poFramework;
    return 0;
}
