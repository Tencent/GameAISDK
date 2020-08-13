/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

#include "Comm/Utils/Log.h"
#include "Comm/Utils/TSingleton.h"
#include "GameRecognize/src/GameRegFrameWork.h"
using namespace std;

#define SIGUSR1 10
#define SIGUSR2 12


// LockFree::LockFreeQueue<CTaskResult> g_oTaskResultQueue;
ThreadSafeQueue<CTaskResult> g_oTaskResultQueue;
std::string                  g_strBaseDir     = "..";
int                          g_nMaxResultSize = 5;


static CGameRegFrameWork *gs_poFramework = NULL;

// 信号处理函数，收到信号(SIGUSR1， SIGUSR2， SIGINT)时退出
static void SigHandle(int iSigNo)
{
    if (iSigNo == SIGUSR1 || iSigNo == SIGUSR2 || iSigNo == SIGINT)
    {
        gs_poFramework->SetExited();
    }
    return;
}

// 输出参数提示
void Help(const char *strProgName)
{
    LOGE("Running program %s with the following arguments.", strProgName);
    LOGE("There are 1 arguments,such as SDKTool / video.");
    LOGE("The first is name of game, such as running / poker.");
}

// 输出参数解析
bool ParseArg(int argc, char *argv[])
{
    if (NULL == gs_poFramework)
    {
        LOGE("gs_poFramework is NULL, please check");
        return false;
    }
    switch (argc)
    {
    case 1:
        // 默认为SDK模式
        LOGI("Run SDK Model");
        break;

    case 2:
        if (strcmp(argv[1], "SDKTool") == 0)
        {
            gs_poFramework->SetTestMode(true, SDKTOOL_TEST);
            LOGI("Run SDKTool Test Model");
        }
        else if (strcmp(argv[1], "video") == 0)
        {
            gs_poFramework->SetTestMode(true, VIDEO_TEST);
            LOGI("Run VIDEO Test Model");
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
    // 获取环境变量"AI_SDK_PATH"
    char *pPath = NULL;
    pPath = getenv("AI_SDK_PATH");

    if (pPath != NULL)
    {
        g_strBaseDir = std::string(pPath);
    }

    g_strBaseDir.append("/");

    gs_poFramework = new CGameRegFrameWork();
    if (NULL == gs_poFramework)
    {
        LOGE("new GameRegFrameWork failed");
    }
    try
    {
        // 初始化Framework
        if (0 == gs_poFramework->Initialize())
        {
            ParseArg(argc, argv);
            signal(SIGUSR1, SigHandle);
            signal(SIGUSR2, SigHandle);
            signal(SIGINT, SigHandle);

            // 运行
            if (-1 == gs_poFramework->Run())
            {
                LOGE("run failed");
            }
        }
        else
        {
            LOGE("Init GameRegFrameWork failed");
        }

        // 释放资源
        gs_poFramework->Release();
    }
    catch(...)
    {
        LOGE("catch an exception error");
    }

    delete gs_poFramework;
    LOGI("=================GameReg exit===================");

#ifdef WINDOWS
    system("pause");
#endif // WINDOWS

    return    0;
}
/*! @} */
