/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CBloodLengthReg.h"

// **************************************************************************************
//          CBloodLengthRegTmplMatch Class
// **************************************************************************************

CBloodLengthRegTmplMatch::CBloodLengthRegTmplMatch() {
    m_fExpandWidth = 0.0f;
    m_fExpandHeight = 0.0f;
    m_nTaskID = -1;
}

CBloodLengthRegTmplMatch::~CBloodLengthRegTmplMatch() {
}

// **************************************************************************************
//          CBloodLengthRegTmplMatch: initialize task
// **************************************************************************************
int CBloodLengthRegTmplMatch::Initialize(const int nTaskID,
    const tagBloodLengthRegElement &stElement) {
    m_nTaskID = nTaskID;

    CColorBinMatchParam oParam;
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stElement.nScaleLevel;
    oParam.m_fMinScale = stElement.fMinScale;
    oParam.m_fMaxScale = stElement.fMaxScale;
    oParam.m_oROI = stElement.oROI;
    oParam.m_oVecTmpls = stElement.oVecTmpls;
    // oParam.m_strOpt = "-matchMethod CCORR_NORMED";
    oParam.m_strOpt = "-matchMethod SQDIFF_NORMED";
    oParam.m_oVecConditions = stElement.oVecConditions;

    m_fExpandWidth = stElement.fExpandWidth;
    m_fExpandHeight = stElement.fExpandHeight;
    m_oROI = oParam.m_oROI;

    CColorBinMatch oMethod;
    int            nState = oMethod.Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: initialize ColorBinMatch failed, please check", m_nTaskID);
        return nState;
    }

    m_oMethod = oMethod;

    return 1;
}

// calculate length of blood based on binary image
int CBloodLengthRegTmplMatch::Predict(const cv::Mat &oSrcImg, tagBloodLengthRegResult &stResult) {
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    CObjDetData oData;
    oData.m_oSrcImg = oSrcImg;

    // obtain roi region of image
    cv::Rect oROI;
    int longEdge = oSrcImg.rows;
    if (oSrcImg.cols > oSrcImg.rows) {
        longEdge = oSrcImg.cols;
    }
    // remove resize 1280
    /*ResizeRect(m_oROI, static_cast<float>(longEdge) / IMAGE_WIDTH,
        static_cast<float>(longEdge) / IMAGE_WIDTH, oROI);*/
    ResizeRect(m_oROI, 1.0f, 1.0f, oROI);
    ExpandRect(oROI, static_cast<int>(oSrcImg.cols * m_fExpandWidth),
        static_cast<int>(oSrcImg.rows * m_fExpandHeight), oROI);
    oData.m_oROI = oROI;

    float                 fScore = 0.0;
    float                 fScale = 0.0;
    std::vector<cv::Rect> oVecROIs;
    CObjDetResult         oResult;

    // extract forground binary image based on color threshold
    int nState = m_oMethod.Predict(&oData, &oResult);
    if (1 != nState) {
        LOGE("task ID %d: predict ColorBinMatch failed, please check", m_nTaskID);
        return nState;
    }

    // output result of blood length
    if (oResult.m_oVecBBoxes.size() > 0) {
        oVecROIs.push_back(oResult.m_oVecBBoxes[0].oRect);
        fScale = oResult.m_oVecBBoxes[0].fScale;
        fScore = oResult.m_oVecBBoxes[0].fScore;
    }

    // extract roi region
    if (oVecROIs.empty()) {
        stResult.nState = 0;
    } else {
        stResult.nState = 1;
        CombineROI(m_nTaskID, oVecROIs, stResult.oROI);
        stResult.fScale = fScale;
        stResult.fScore = fScore;
    }

    return 1;
}

int CBloodLengthRegTmplMatch::Release() {
    return 1;
}

// **************************************************************************************
//          CBloodLengthReg Class
// **************************************************************************************

CBloodLengthReg::CBloodLengthReg() {
    m_hResultTmpLock = TqcOsCreateMutex();
}

CBloodLengthReg::~CBloodLengthReg() {
    TqcOsDeleteMutex(m_hResultTmpLock);
}

// initialize CBloodLengthReg class
int CBloodLengthReg::Initialize(IRegParam *pParam) {
    if (NULL == pParam) {
        LOGE("param pointer is NULL, please check");
        return -1;
    }

    CBloodLengthRegParam *pP = dynamic_cast<CBloodLengthRegParam*>(pParam);
    if (NULL == pP) {
        LOGE("param pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    m_nTaskID = pP->m_nTaskID;

    m_oElement = pP->m_oElement;

    // initial binary template
    m_stElement = m_oElement;
    if ("TemplateMatch" == m_stElement.oAlgorithm) {
        CBloodLengthRegTmplMatch oMethod;
        int nState = oMethod.Initialize(m_nTaskID, m_stElement);
        if (1 != nState) {
            LOGE("task ID %d: initialize BloodLengthRegTmplMatch failed, please check", m_nTaskID);
            return nState;
        }

        m_oMethod = oMethod;
    } else {
        LOGE("task ID %d: algorithm is invalid, please check", m_nTaskID);
        return -1;
    }

    return 1;
}

// obtain length of blood
int CBloodLengthReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    if (NULL == pResult) {
        LOGE("task ID %d: result pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CBloodLengthRegResult *pR = dynamic_cast<CBloodLengthRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: result pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: frame index is invalid, please check", m_nTaskID);
        return -1;
    }

    tagBloodLengthRegResult szResult;

    // compute length of blood
    int nState = m_oMethod.Predict(stData.oSrcImg, szResult);
    if (1 != nState) {
        LOGE("task ID %d: predict failed, please check", m_nTaskID);
        return nState;
    }

    // add lock
    TqcOsAcquireMutex(m_hResultTmpLock);

    // save results of blood for several times
    if (szResult.fScale != -1) {
        if (m_oMatchCountCurrent == 0) {
            m_szResultTmp.fScale = szResult.fScale;
            m_szResultTmp.fScore = szResult.fScore;
            m_szResultTmp.oROI = szResult.oROI;
        } else {
            m_szResultTmp.fScale = szResult.fScale + m_szResultTmp.fScale;
            m_szResultTmp.fScore = szResult.fScore + m_szResultTmp.fScore;
            m_szResultTmp.oROI.x = szResult.oROI.x + m_szResultTmp.oROI.x;
            m_szResultTmp.oROI.y = szResult.oROI.y + m_szResultTmp.oROI.y;
            m_szResultTmp.oROI.width = szResult.oROI.width + m_szResultTmp.oROI.width;
            m_szResultTmp.oROI.height = szResult.oROI.height + m_szResultTmp.oROI.height;
        }

        m_oMatchCountCurrent = m_oMatchCountCurrent + 1;
    }

    // if the detected times is higher than threshold, then get the average value
    if (m_oMatchCountCurrent >= m_stElement.nMatchCount) {
        LOGD("task ID %d: MatchCountCurrent reaches MatchCount, which is %d\n",
            m_nTaskID, m_stElement.nMatchCount);
        szResult.nState = 1;
        szResult.fScale = m_szResultTmp.fScale / m_oMatchCountCurrent;
        szResult.fScore = m_szResultTmp.fScore / m_oMatchCountCurrent;
        szResult.oROI.x = m_szResultTmp.oROI.x / m_oMatchCountCurrent;
        szResult.oROI.y = m_szResultTmp.oROI.y / m_oMatchCountCurrent;
        szResult.oROI.width = m_szResultTmp.oROI.width / m_oMatchCountCurrent;
        szResult.oROI.height = m_szResultTmp.oROI.height / m_oMatchCountCurrent;
    } else {
        LOGD("task ID %d: MatchCountCurrent is %d\n", m_nTaskID, m_oMatchCountCurrent);
        szResult.nState = 0;
    }

    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResult);
    TqcOsReleaseMutex(m_hResultTmpLock);
    return 1;
}

// release class
int CBloodLengthReg::Release() {
    TqcOsDeleteMutex(m_hResultTmpLock);

    LOGD("task ID %d: release BloodLength reg", m_nTaskID);
    return 1;
}

