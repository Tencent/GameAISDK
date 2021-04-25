/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Os/TqcOs.h"
#include "UI/Src/UICfg/GameOverCfg.h"

bool ReadClickActionCfg(const int nIndex, CJsonConfig *pConfig, tagUIState *puiState) {
    puiState->actionType = UI_ACTION_CLICK;
    int nLen = 0;
    // x position of click in the image.
    // memset(buf, 0, TQC_PATH_STR_LEN);
    char buf[TQC_PATH_STR_LEN] = { 0 };
    bool bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionX", buf, &nLen, DATA_STR);
    if (!bRst) {
        LOGE("get state description failed. gameOver actionX: %d", nIndex);
        return false;
    }

    // y position of click in the image.
    puiState->stAction1.nActionX = atoi(buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionY", buf, &nLen, DATA_STR);
    if (!bRst) {
        LOGE("get state description failed. gameOver actionY: %d", nIndex);
        return false;
    }

    puiState->stAction1.nActionY = atoi(buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionThreshold", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fActionThreshold = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdWPixel", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.nTmplExpdWPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdHPixel", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.nTmplExpdHPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdWRatio", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fROIExpdWRatio = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdHRatio", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fROIExpdHRatio = atof(buf);
    }

    // LOGD("x, y: %d, %d", uiState.stAction1.nXAction, uiState.stAction1.nActionY);
    LOGI("index: %d, id: %d, x, y: %d, %d, %f, %d, %d, %f, %f",
        nIndex, puiState->nId, puiState->stAction1.nActionX, puiState->stAction1.nActionY,
        puiState->stAction1.fActionThreshold, puiState->stAction1.nTmplExpdWPixel,
        puiState->stAction1.nTmplExpdHPixel, puiState->stAction1.fROIExpdWRatio,
        puiState->stAction1.fROIExpdHRatio);

    puiState->stAction2.nActionX = 0;
    puiState->stAction2.nActionY = 0;
    return true;
}

bool  ReadDragActionCfg(const int nIndex, CJsonConfig *pConfig, tagUIState *puiState) {
    // For drag operation, we will set the start point and
    // end point. The drag is from (x1, y1) to (x2, y2).
    char buf[TQC_PATH_STR_LEN] = { 0 };
    int  nLen = 0;
    bool bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionX1", buf, &nLen, DATA_STR);

    if (!bRst) {
        LOGE("get state description failed. uiStates actionX1: %d", nIndex);
        delete pConfig;
        return false;
    }

    // uiState.x1Action = atoi(buf);
    puiState->stAction1.nActionX = atoi(buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionY1", buf, &nLen, DATA_STR);
    if (!bRst) {
        LOGE("get state description failed. uiStates actionY1: %d", nIndex);
        delete pConfig;
        return false;
    }

    puiState->stAction1.nActionY = atoi(buf);

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionThreshold1", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fActionThreshold = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdWPixel1",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.nTmplExpdWPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdHPixel1",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.nTmplExpdHPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdWRatio1",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fROIExpdWRatio = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdHRatio1",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction1.fROIExpdHRatio = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionX2", buf, &nLen, DATA_STR);
    if (!bRst) {
        LOGE("get state description failed. uiStates actionX2: %d", nIndex);
        delete pConfig;
        return false;
    }

    // uiState.x2Action = atoi(buf);
    puiState->stAction2.nActionX = atoi(buf);
    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionY2", buf, &nLen, DATA_STR);
    if (!bRst) {
        LOGE("get state description failed. uiStates actionY2: %d", nIndex);
        delete pConfig;
        return false;
    }

    // uiState.y2Action = atoi(buf);
    puiState->stAction2.nActionY = atoi(buf);

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionThreshold2", buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction2.fActionThreshold = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdWPixel2",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction2.nTmplExpdWPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionTmplExpdHPixel2",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction2.nTmplExpdHPixel = atoi(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdWRatio2",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction2.fROIExpdWRatio = atof(buf);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetArrayValue("gameOver", nIndex, "actionROIExpdHRatio2",
        buf, &nLen, DATA_STR);
    if (bRst) {
        puiState->stAction2.fROIExpdHRatio = atof(buf);
    }

    return true;
}

bool ReadActionCfg(const char *pszActionType, const int nIndex, CJsonConfig *pConfig,
    tagUIState *puiState) {
    if (strstr(pszActionType, "click")) {
        return ReadClickActionCfg(nIndex, pConfig, puiState);
    } else if (strstr(pszActionType, "drag")) {
        return ReadDragActionCfg(nIndex, pConfig, puiState);
    }

    return false;
}

CGameOverCfg::CGameOverCfg() {
    m_stateArr.clear();
    m_nCheckInterval = GAME_UI_CHECK_INTERVAL / 2;
}

CGameOverCfg::~CGameOverCfg() {
}

bool CGameOverCfg::Initialize(const char *pszRootDir, const char *pszCftPath) {
    CJsonConfig *pConfig = new CJsonConfig();

    // Cannot create json config parser.
    if (pConfig == NULL) {
        LOGE("Cannot create json config parser.");
        return false;
    }

    char szPath[TQC_PATH_STR_LEN] = { 0 };
    SNPRINTF(szPath, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, pszCftPath);
    // Check if UI config file exists.
    if (!IsFileExist(szPath)) {
        LOGE("ui configuration  file %s is not exist", szPath);
        delete pConfig;
        return false;
    }

    // Load UI config file.
    bool bRst = pConfig->loadFile(szPath);
    if (!bRst) {
        LOGE("Load file %s failed", szPath);
        delete pConfig;
        return false;
    }

    bRst = ReadGameOverCfg(pszRootDir, pConfig);
    delete pConfig;
    return bRst;
}

bool CGameOverCfg::ReadGameOverCfg(const char *pszRootDir, CJsonConfig *pConfig) {
    int  nSize = pConfig->GetArraySize("gameOver");
    int  nLen = 0;
    char buf[TQC_PATH_STR_LEN];
    bool bRst = false;

    // There is no game over state.
    if (nSize <= 0) {
        LOGI("There is no game over state.");
        return true;
    }

    // Parse each of game over states.
    for (int i = 0; i < nSize; i++) {
        tagUIState uiState;

        // Description of game over.
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "desc", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver desc: %d", i);
            // delete pConfig;
            return false;
        }

        // id of game over should not be duplicated.
        memset(uiState.strStateName, 0, TQC_PATH_STR_LEN);
        memcpy(uiState.strStateName, buf, nLen);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "id", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver id: %d", i);
            // delete pConfig;
            return false;
        }

        // Game over uses the template match. We should provide path of sample image.
        uiState.nId = atoi(buf);

        // "actionSleepTimeMs"
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "actionSleepTimeMs", buf, &nLen, DATA_STR);
        if (bRst) {
            uiState.nActionSleepTimeMs = atoi(buf);
        }

        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "imgPath", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed.  gameOver imgPath: %d", i);
            // delete pConfig;
            return false;
        }

        // We should set the x, y, width and height of sample in the image.
        memset(uiState.strSampleFile, 0, TQC_PATH_STR_LEN);
        SNPRINTF(uiState.strSampleFile, TQC_PATH_STR_LEN, "%s/%s", pszRootDir, buf);

        cv::Mat oImage = cv::imread(uiState.strSampleFile);
        if (!oImage.empty()) {
            uiState.sampleImg = oImage;
        }

        // memcpy(uiState.strSampleFile, buf, nLen);
        // uiState.bUseTempMatch = true;
        uiState.nTemplate = 1;
        uiState.tempOp = UI_TEMPLATE_AND;
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "x", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver x: %d", i);
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleX = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "y", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver y: %d", i);
            return false;
        }

        uiState.szTemplState[0].stTemplParam.nSampleY = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "w", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver w: %d", i);
            return false;
        }

        // uiState.nWidth[0] = atoi(buf);
        uiState.szTemplState[0].stTemplParam.nSampleW = atoi(buf);
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "h", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get state description failed. gameOver h: %d", i);
            // delete pConfig;
            return false;
        }

        // We can search template in some region, not exact position of sample in
        // the image.
        uiState.szTemplState[0].stTemplParam.nSampleH = atoi(buf);
        // memset(buf, 0, TQC_PATH_STR_LEN);
        // bRst = pConfig->GetArrayValue("gameOver", i, "shift", buf, &nLen, DATA_STR);
        // if (!bRst)
        // {
        //     LOGE("get state description failed. gameOver shift: %d", i);
        //     delete pConfig;
        //     return false;
        // }

        // read threshold
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "templateThreshold", buf, &nLen, DATA_STR);
        if (bRst) {
            uiState.szTemplState[0].stTemplParam.fThreshold = atof(buf);
        }

        // The action will send to client if game over is matched.
        uiState.szTemplState[0].nShift = atoi(buf);

        // Set action during time.
        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "during", buf, &nLen, DATA_STR);
        if (bRst) {
            uiState.nActionDuringTime = atoi(buf);
        }

        memset(buf, 0, TQC_PATH_STR_LEN);
        bRst = pConfig->GetArrayValue("gameOver", i, "actionType", buf, &nLen, DATA_STR);
        if (!bRst) {
            LOGE("get UI %d gameOver actionType failed", i);
            return false;
        }

        bRst = ReadActionCfg(buf, i, pConfig, &uiState);
        if (!bRst) {
            LOGE("read UI %d action config failed", i);
            return false;
        }

        // Load sample images of game over.
        // memset(buf, 0, TQC_PATH_STR_LEN);
        // SNPRINTF(buf, sizeof(buf), "%s/%s", pszRootDir, uiState.strSampleFile);
        // LOGW("Load game over image: %s", buf);
        // cv::Mat origImg = cv::imread(buf);
        // if (origImg.empty())
        // {
        //     LOGE("Cannot open image file: %s", buf);
        //     return false;
        // }

        // int nOrigW = origImg.cols;
        // int nOrigH = origImg.rows;

        // If not supporting multi-resolution, we should resize the sample based on
        // current screen size.
        // Saving the current game over state.
        // We will check each one of here to determine if it is game over.
        LOGI("load game over %d configure", uiState.nId);
        m_stateArr.push_back(uiState);
    }

    memset(buf, 0, TQC_PATH_STR_LEN);
    bRst = pConfig->GetConfValue("checkInterVal", buf, &nLen, DATA_STR);
    if (bRst) {
        int nInterval = atof(buf);
        if (nInterval == 0) {
            LOGE("can not set checkInterVal as 0");
        } else {
            m_nCheckInterval = nInterval;
        }
    }

    LOGI("checkInterVal is %d", m_nCheckInterval);
    return true;
}

UIStateArray CGameOverCfg::GetState() {
    return m_stateArr;
}

void CGameOverCfg::SetState(const UIStateArray &oVecStateArr) {
    m_stateArr = oVecStateArr;
}

int CGameOverCfg::GetCheckInterval() {
    return m_nCheckInterval;
}
