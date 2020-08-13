/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef UI_TYPES_H
#define UI_TYPES_H

#include <string>
#include <vector>

#include "Comm/Utils/GameUtils.h"
#include "Comm/Utils/JsonConfig.h"
#include "UI/Src/UIDefine.h"

enum ETestMode
{
    SDK_TEST     = 0,
    VIDEO_TEST   = 1,
    IMG_TEST     = 2,
    SDKTOOL_TEST = 3,
    NONE_TEST    = 4
};

typedef enum _eUIActionType
{
    UI_ACTION_NONE = 0,
    UI_ACTION_CLICK,
    UI_ACTION_DRAG,
    UI_ACTION_TEXT,
    UI_ACTION_DRAG_AND_CHECK,
    UI_ACTION_SCRIPT,
    UI_ACTION_MAX
} eUIActionType;

typedef enum _eTemplateOp
{
    UI_TEMPLATE_NONE = 0,
    UI_TEMPLATE_AND,
    UI_TEMPLATE_OR,
    UI_TEMPLATE_MAX
} eTemplateOp;


struct tagUITemplateState
{
    tagUITemplateParam stTemplParam;
    int                nShift;
    cv::Mat            tempImg;

    tagUITemplateState()
    {
        nShift = 20;
    }
};


// For drag only, we encounter some drag operation that does not
// drag the same distance. Therefore, we have to drag and check.
struct tagUIDragCheckState
{
    int          dragAction;    // 0 for none, 1 for down, 2 for up, 3 for left, 4 for right
    tagPoint     stDragPt;
    int          dragLen;       // distance of drag by pixels
    int          dragCount;     // count of max drag operation.
    char         strDragTargetFile[TQC_PATH_STR_LEN];       // path of drag target file
    int          nTarget;
    tagRectangle stTargetRect;
    float        fDragThreshold;
    cv::Mat      targetImg[GAME_UI_TEMPLATE_NUM];
    // CTemplateMatch  targetTemp; // Using template match to check

    tagUIDragCheckState()
    {
        dragAction     = 0; // 0 for none
        dragLen        = 0;
        dragCount      = 0;
        nTarget        = 0;
        fDragThreshold = GAME_TEMPLATE_THRESHOLD;
    }
};

// UI state definition
struct tagUIState
{
    int                nId;
    int                nMatched;
    char               strSampleFile[TQC_PATH_STR_LEN];
    char               strStateName[TQC_PATH_STR_LEN];
    cv::Mat            sampleImg;
    bool               bDelete;
    int                nTemplate; // Number of template sample images.
    eTemplateOp        tempOp; // operation of template match algorithm.
    tagUITemplateState szTemplState[GAME_UI_TEMPLATE_NUM];
    // Action during time for click.
    int nActionDuringTime;
    // UI Action
    eUIActionType  actionType;
    tagActionState stAction1;
    tagActionState stAction2;

    tagUIDragCheckState stDragCheckState;
    tagRectangle        stTempRect;
    int                 nCheckSameFrameCnt;
    // added over

    // action type: "script"
    int         nScrpitExtNum;
    char        strScriptPath[TQC_PATH_STR_LEN];
    Json::Value jsonScriptParams;
    int         nActionSleepTimeMs;

    tagUIState()
    {
        nId       = -1;
        nMatched  = 100;
        bDelete   = false;
        nTemplate = 0;
        tempOp    = UI_TEMPLATE_NONE;
        // bUseTempMatch = false;
        memset(strSampleFile, 0, TQC_PATH_STR_LEN);
        // memset(strStateName, 0, TQC_PATH_STR_LEN);

        actionType = UI_ACTION_NONE;

        nActionDuringTime  = 200; // default action during time is 200ms.
        nCheckSameFrameCnt = CHECK_SAME_UI_FRAME_CNT;

        nScrpitExtNum = 0;
        memset(strScriptPath, 0, TQC_PATH_STR_LEN);
        nActionSleepTimeMs = 100;
    }
};

typedef std::vector<tagUIState> UIStateArray;

enum enGameState
{
    GAME_REG_STATE_HALL  = 0,
    GAME_REG_STATE_START = 1,
    GAME_REG_STATE_RUN   = 2,
    GAME_REG_STATE_OVER  = 3,
    GAME_REG_STATE_NONE  = 4
};

//
// Store matched frame
//
struct tagMatchedFrame
{
    // Cached frame
    cv::Mat matchedFrame;

    // cached frame's index of related UI sample.
    int nUIIndex;

    // UI Action
    eUIActionType actionType;
    tagPoint      stActionPt1;
    tagPoint      stActionPt2;

    tagMatchedFrame()
    {
        nUIIndex   = -1;
        actionType = UI_ACTION_MAX;
    }
};


struct tagUnitAction
{
    std::string    strText;
    _eUIActionType eAction;
    // cv::Point clickPt;
    // std::vector<cv::Point> stVecDragPt;
    tagActionState              stClickPt;
    std::vector<tagActionState> stVecDragPt;
    int                         nDuringTimeMs;
    int                         nSleepTimeMs;
    std::string                 strScriptPath;
    Json::Value                 jsonScriptParams;
};


struct tagUIRegResult
{
    std::vector<tagUnitAction> oVecActions;
    int                        nID;
    cv::Mat                    oSampleImage;
    tagUIRegResult()
    {
        nID = -1;
    }
};


struct tagFrameContext
{
    cv::Mat oFrame;
    int     nFrameSeq; // 从网络受到的图像帧的帧序号（直接转发）
    int     nFrameCount; // UI进程的接收到的图像数量
    tagFrameContext()
    {
        nFrameSeq   = -1;
        nFrameCount = 0;
    }
};

#endif // UI_TYPES_H
