/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CLocationReg.h"
#include "Comm/Utils/TqcLog.h"
#include "UI/Src/UIReg/GameOverReg.h"


CGameOverReg::CGameOverReg() {
}

CGameOverReg::~CGameOverReg() {
}

bool CGameOverReg::Initialize(CUICfg *pUICfg) {
    // check parameters
    if (NULL == pUICfg) {
        LOGE("Input UICfg is NULL, POP UI Initialize failed");
        return false;
    }

    // fill game over recognizer parameters
    return FillGameOverRegParam(pUICfg);
}

bool CGameOverReg::FillGameOverRegParam(CUICfg *pUICfg) {
    CGameOverCfg *pGameOverCfg = dynamic_cast<CGameOverCfg*>(pUICfg);

    m_oVecCfg = pGameOverCfg->GetState();
    int nSize = m_oVecCfg.size();

    for (int i = 0; i < nSize; i++) {
        tagUIState stUIState = m_oVecCfg[i];

        tagGameOverParam stUIParam;
        // UID
        stUIParam.nID = stUIState.nId;
        // template match threshold
        stUIParam.fThreshold = stUIState.szTemplState[0].stTemplParam.fThreshold;
        // read ROI parameters(x, y, w, h) from configure
        int nSampleX = stUIState.szTemplState[0].stTemplParam.nSampleX;
        int nSampleY = stUIState.szTemplState[0].stTemplParam.nSampleY;
        int nSampleW = stUIState.szTemplState[0].stTemplParam.nSampleW;
        int nSampleH = stUIState.szTemplState[0].stTemplParam.nSampleH;
        stUIParam.oSrcRect = cv::Rect2i(nSampleX, nSampleY, nSampleW, nSampleH);
        // check image path is valid
        stUIParam.oTemplImg = cv::imread(stUIState.strSampleFile);
        if (stUIParam.oTemplImg.empty()) {
            LOGE("read image %s failed", stUIState.strSampleFile);
            return false;
        }

        m_stVecParam.push_back(stUIParam);
    }

    return true;
}

int CGameOverReg::Predict(const cv::Mat &frame, const std::vector<tagGameOverParam> &m_stParam,
    cv::Rect &DstRect) {
    int nDstIndex = -1;

    for (int i = 0; i < m_stParam.size(); i++) {
        float    fMinVal = 0.0f;
        cv::Rect srcRC = m_stParam[i].oSrcRect;
        cv::Rect dstRC;
        // detect rect with multi-process method, if return value is 1, match¡£
        int nRes = DetectRect(m_stParam[i].nID, frame, m_stParam[i].oTemplImg, srcRC,
            m_stParam[i].fThreshold, &dstRC, &fMinVal);
        if (nRes != 1) {
            LOGD("GameOVer Cannot Match: index(%d), tempIndex(%d)\n", m_stParam[i].nID, i);
        } else {
            if (dstRC.width != 0 && dstRC.height != 0) {
                DstRect = dstRC;
                nDstIndex = i;
                break;
            }
        }
    }

    return nDstIndex;
}

int CGameOverReg::Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst) {
    // check parameters, if size of m_oVecCfg is 0, there is no game over sample UIs
    if (0 == m_oVecCfg.size()) {
        LOGW("count of game over configure item is 0, please check");
        return -1;
    }

    // tagGameOverParam stUIParam;
    // tagUIState stUIState;
    cv::Mat  frame = stFrameCtx.oFrame;
    cv::Rect dstRect;
    int      nIndex = Predict(frame, m_stVecParam, dstRect);
    if (-1 == nIndex) {
        LOGI("not match game over state");
    } else {
        tagUIState stUIState;
        stUIState = m_oVecCfg[nIndex];
        stUIRegRst.nID = stUIState.nId;
        tagUnitAction stAction;
        stAction.eAction = stUIState.actionType;
        int nPtx = dstRect.x;
        int nPtY = dstRect.y;
        int nWidth = dstRect.width;
        int nHeight = dstRect.height;
        stAction.stClickPt = stUIState.stAction1;
        stAction.nDuringTimeMs = stUIState.nActionDuringTime;
        stAction.nSleepTimeMs = stUIState.nActionSleepTimeMs;
        stUIRegRst.oVecActions.push_back(stAction);
        stUIRegRst.oSampleImage = m_stVecParam[nIndex].oTemplImg;
    }

    return nIndex;
}
