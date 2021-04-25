/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_COMMUNICATE_DATACOMM_H_
#define GAME_AI_SDK_IMGPROC_UI_COMMUNICATE_DATACOMM_H_

#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/opencv.hpp>
#ifdef OPENCV_2
#include <opencv2/highgui/highgui.hpp>
#else
#include <opencv2/highgui.hpp>
#endif

#include <map>
#include <queue>
#include <string>

#include "Comm/Utils/GameUtils.h"
#include "Comm/Utils/TqcCommon.h"
#include "Comm/Utils/TqcLock.h"


enum enSourceType {
    DATA_SRC_VIDEO = 0,
    DATA_SRC_PICTURE,
    DATA_SRC_TBUS,
    DATA_SRC_FILE,
    DATA_SRC_INVALID
};

enum enPeerName {
    PEER_AGENT = 0,
    PEER_UIAUTO,
    PEER_UIRECOGNIZE,
    PEER_IMG_RECOGNIZE,
    PEER_STRATEGY,
    PEER_UIMATCH,
    PEER_UIREGMGR,
    PEER_MC,
    PEER_SDK_TOOLS,
    PEER_NONE
};

struct tagPicParams {
    char filePath[TQC_PATH_STR_LEN];
    char fileName[TQC_PATH_STR_LEN];
    char fileSuffix[TQC_PATH_STR_LEN];
    int  nStart;
    int  nEnd;

    tagPicParams() {
        memset(filePath, 0, TQC_PATH_STR_LEN);
        memset(fileName, 0, TQC_PATH_STR_LEN);
        memset(fileSuffix, 0, TQC_PATH_STR_LEN);

        nStart = -1;
        nEnd = -1;
    }
};

#define MAXNUMPEER         2
#define AGENTPEER          0
#define UIAUTOPEER         1
#define MAX_IMAGE_DATA_LEN 1024 * 1000 * 8
#define FRAME_QUEUE_NUM    4

struct  stTBUSParas {
    // char szConfigFile[TQC_PATH_STR_LEN];
    int                        nSelfAddr;
    std::map<std::string, int> mapAddr;
    // int narryPeerAddr[MAXNUMPEER];
    stTBUSParas() {
        //  memset(szConfigFile, 0, TQC_PATH_STR_LEN);
        // memset(narryPeerAddr, 0, sizeof(int)*MAXNUMPEER);
        nSelfAddr = 0;
    }
};

// tbus parameters.
struct stTBUSInitParams {
    char                               szConfigFile[TQC_PATH_STR_LEN];
    std::string                        strSelfAddr;  // tbus address
    std::map<std::string, std::string> mapStrAddr;   // the other processes tbus address.
    stTBUSInitParams() {
        memset(szConfigFile, 0, TQC_PATH_STR_LEN);
    }
};



typedef void(*MSG_HANDLER_ROUTINE)(void *pMsg);

#endif  // GAME_AI_SDK_IMGPROC_UI_COMMUNICATE_DATACOMM_H_
