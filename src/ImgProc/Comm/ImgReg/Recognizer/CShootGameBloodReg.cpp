/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CShootGameBloodReg.h"

// **************************************************************************************
//          CShootGameBloodRegMethod Class Deifne
// **************************************************************************************

CShootGameBloodRegMethod::CShootGameBloodRegMethod() {
    m_nTaskID = -1;  // task ID
    m_nBloodLength = 123;  // blood length
    m_oROI = cv::Rect(-1, -1, -1, -1);  // detection ROI
}

CShootGameBloodRegMethod::~CShootGameBloodRegMethod() {
}

int CShootGameBloodRegMethod::Initialize(const int nTaskID,
    const tagShootGameBloodRegParam *pParam) {
    // check task ID
    if (nTaskID < 0) {
        LOGE("CShootGameBloodRegMethod -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    // copy task ID
    m_nTaskID = nTaskID;

    // check blood length
    if (pParam->nBloodLength <= 0) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- blood length %d is invalid, please check",
            m_nTaskID, pParam->nBloodLength);
        return -1;
    }

    tagShootGameBloodRegParam stParam = *pParam;

    int nState;

    // fill GradMatch parameters
    CGradMatchParam oGradMatchParam;
    nState = FillGradMatchParam(stParam, oGradMatchParam);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- CGradMatch fill param failed, please check",
            m_nTaskID);
        return nState;
    }

    // initialize GradMatch
    nState = m_oGradMatch.Initialize(&oGradMatchParam);
    if (1 != nState) {
        LOGE("task ID %d: CSGameBloodRegMethod -- CGradMatch initialization failed, please check",
            m_nTaskID);
        m_oGradMatch.Release();
        return nState;
    }

    // fill ColorDet parameters
    CColorDetParam oColorDetParam;
    stParam.strCondition = "55 < R < 125, 165 < G < 255, 0 < B < 100";
    nState = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- CColorDet fill param failed, please check",
            m_nTaskID);
        return nState;
    }

    // initialize ColorDet
    nState = m_oColorDet.Initialize(&oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: CShBloodRegMethod -- CColorDet initialization failed, please check",
            m_nTaskID);
        m_oColorDet.Release();
        return nState;
    }

    // copy parameters
    m_nBloodLength = stParam.nBloodLength;
    m_oROI = stParam.oROI;

    return 1;
}

int CShootGameBloodRegMethod::Predict(const cv::Mat &oSrcImg,
    tagShootGameBloodRegResult &stResult) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- source image is invalid, please check",
            m_nTaskID);
        return -1;
    }

    // check ROI
    int nState = CheckROI(m_nTaskID, oSrcImg, m_oROI);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- ROI rectangle is invalid, please check",
            m_nTaskID);
        return nState;
    }

    // set ObjDet input
    CObjDetData   oObjDetData;
    CObjDetResult oObjDetResult;
    oObjDetData.m_oSrcImg = oSrcImg;

    // run GradMatch
    nState = m_oGradMatch.Predict(&oObjDetData, &oObjDetResult);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- CGradMatch predict failed, please check",
            m_nTaskID);
        stResult.nState = 0;
        stResult.oROI = m_oROI;
        return nState;
    }

    if (oObjDetResult.m_oVecBBoxes.empty()) {
        stResult.nState = 0;
        stResult.oROI = m_oROI;
        return 1;
    }

    // compute blood rectangle
    cv::Rect oBloodRect;
    oBloodRect.x = oObjDetResult.m_oVecBBoxes[0].oRect.x - 45;
    oBloodRect.y = oObjDetResult.m_oVecBBoxes[0].oRect.y + 60;
    oBloodRect.width = 145;
    oBloodRect.height = 15;

    if (oBloodRect.x < 0 || oBloodRect.y < 0 ||
        oBloodRect.x + oBloodRect.width > oSrcImg.cols ||
        oBloodRect.y + oBloodRect.height > oSrcImg.rows) {
        stResult.nState = 0;
        stResult.oROI = m_oROI;
        return 1;
    }

    // cv::Mat oBloodImg = oSrcImg(oBlood);
    // cv::imshow("oBloodImg", oBloodImg);
    // cvWaitKey(0);

    // set PixDet input
    CPixDetData   oPixDetData;
    CPixDetResult oPixDetResult;
    oPixDetData.m_oSrcImg = oSrcImg;
    oPixDetData.m_oROI = oBloodRect;

    // run ColorDet
    nState = m_oColorDet.Predict(&oPixDetData, &oPixDetResult);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- CColorDet predict failed, please check",
            m_nTaskID);
        stResult.nState = 0;
        stResult.oROI = m_oROI;
        return nState;
    }

    if (oPixDetResult.m_oVecPoints.empty()) {
        stResult.nState = 1;
        stResult.oROI = m_oROI;
        stResult.stBlood.fPercent = 0.0f;
        stResult.stBlood.oRect = oBloodRect;
        stResult.stBlood.fScore = oObjDetResult.m_oVecBBoxes[0].fScore;
        return 1;
    }

    int nMinX = 1280;
    int nMaxX = 0;

    for (int i = 0; i < static_cast<int>(oPixDetResult.m_oVecPoints.size()); i++) {
        cv::Point oPt = oPixDetResult.m_oVecPoints[i];
        if (oPt.x <= nMinX) {
            nMinX = oPt.x;
        }

        if (oPt.x >= nMaxX) {
            nMaxX = oPt.x;
        }
    }

    // set blood percent and other information
    stResult.nState = 1;
    stResult.oROI = m_oROI;
    stResult.stBlood.fPercent = static_cast<float>(nMaxX - nMinX)
        / static_cast<float>(m_nBloodLength);
    stResult.stBlood.oRect = oBloodRect;
    stResult.stBlood.fScore = oObjDetResult.m_oVecBBoxes[0].fScore;

    return 1;
}

int CShootGameBloodRegMethod::Release() {
    return 1;
}

int CShootGameBloodRegMethod::FillGradMatchParam(const tagShootGameBloodRegParam &stParam,
    CGradMatchParam &oParam) {
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oROI;
    oParam.m_oVecTmpls = stParam.oVecTmpls;
    oParam.m_strOpt = "-featureNum 32";

    return 1;
}

int CShootGameBloodRegMethod::FillColorDetParam(const tagShootGameBloodRegParam &stParam,
    CColorDetParam &oParam) {
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nMaxPointNum = stParam.nMaxPointNum;
    oParam.m_nFilterSize = stParam.nFilterSize;
    oParam.m_oROI = stParam.oROI;

    int nState = GetRGB(m_nTaskID,
        stParam.strCondition,
        oParam.m_nRedLower, oParam.m_nRedUpper,
        oParam.m_nGreenLower, oParam.m_nGreenUpper,
        oParam.m_nBlueLower, oParam.m_nBlueUpper);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameBloodRegMethod -- get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CShootGameBloodReg Class Deifne
// **************************************************************************************

CShootGameBloodReg::CShootGameBloodReg() {
    m_oVecParams.clear();  // clear vector of parameters
    m_oVecMethods.clear();  // clear vector of methods
}

CShootGameBloodReg::~CShootGameBloodReg() {
}

int CShootGameBloodReg::Initialize(IRegParam *pParam) {
    // check parameters
    if (NULL == pParam) {
        LOGE("CShootGameBloodReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CShootGameBloodRegParam *pP = dynamic_cast<CShootGameBloodRegParam*>(pParam);

    if (NULL == pP) {
        LOGE("CShootGameBloodReg -- CShootGameBloodRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0) {
        LOGE("CShootGameBloodReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty()) {
        LOGE("task ID %d: CShootGameBloodReg -- param vector is empty, please check",
            pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE) {
        LOGE("task ID %d: CShootGameBloodReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        CShootGameBloodRegMethod oMethod;

        int nState = oMethod.Initialize(m_nTaskID, &m_oVecParams[i]);
        if (1 != nState) {
            LOGE("task ID %d: CShootGameBloodReg -- initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CShootGameBloodReg -- CShootGameBloodReg initialization successful",
        m_nTaskID);
    return 1;
}

int CShootGameBloodReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    // check parameters
    if (NULL == pResult) {
        LOGE("task ID %d: CShootGameBloodReg -- IRegResult pointer is NULL, please check",
            m_nTaskID);
        return -1;
    }

    CShootGameBloodRegResult *pR = dynamic_cast<CShootGameBloodRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CShootGameBloodReg -- CShBloodRegResult pointer is NULL, please check",
            m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: CShootGameBloodReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: CShootGameBloodReg -- frame index %d is invalid, please check",
            m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    tagShootGameBloodRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState) {
            LOGE("task ID %d: CShootGameBloodReg -- CSGBRegMethod predict failed, please check",
                m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CShootGameBloodReg::Release() {
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState) {
            LOGE("task ID %d: CShootGameBloodReg -- CSGBRegMethod release failed, please check",
                m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear();  // clear vector of parameters
    m_oVecMethods.clear();  // clear vector of methods

    LOGD("task ID %d: CShootGameBloodReg -- CShootGameBloodReg release successful", m_nTaskID);
    return 1;
}
