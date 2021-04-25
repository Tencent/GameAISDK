/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CShootGameHurtReg.h"

// **************************************************************************************
//          CShootGameHurtRegMethod Class Deifne
// **************************************************************************************

CShootGameHurtRegMethod::CShootGameHurtRegMethod() {
    m_nTaskID = -1;
    m_fThreshold = 0.75f;
}

CShootGameHurtRegMethod::~CShootGameHurtRegMethod() {
}

int CShootGameHurtRegMethod::Initialize(const int nTaskID,
    const tagShootGameHurtRegParam &stParam) {
    if (nTaskID < 0) {
        LOGE("CShootGameHurtRegMethod -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    if (stParam.fThreshold <= 0) {
        LOGE("task ID %d: CShootGameHurtRegMethod -- threshold %f is invalid, please check",
            m_nTaskID, stParam.fThreshold);
        return -1;
    }

    m_fThreshold = stParam.fThreshold;
    m_oROI = stParam.oROI;

    return 1;
}

int CShootGameHurtRegMethod::Predict(const cv::Mat &oSrcImg,
    tagShootGameHurtRegResult &stResult) {
    if (oSrcImg.empty()) {
        LOGE("task ID %d: CShootGameHurtRegMethod -- source image is invalid, please check",
            m_nTaskID);
        return -1;
    }

    int nState = CheckROI(m_nTaskID, oSrcImg, m_oROI);
    if (1 != nState) {
        LOGE("task ID %d: CShootGameHurtRegMethod -- ROI rectangle is invalid, please check",
            m_nTaskID);
        return nState;
    }

    cv::Mat oGrayImg;
    cv::cvtColor(oSrcImg, oGrayImg, cv::COLOR_BGR2GRAY);

    cv::Mat oBinImg;
    cv::threshold(oGrayImg, oBinImg, 70, 255, cv::THRESH_BINARY);

    // get left image
    cv::Rect oLeftROI = cv::Rect(0, 0, 5, oBinImg.rows);
    cv::Mat  oLeftImg = oBinImg(oLeftROI);

    // get right image
    cv::Rect oRightROI = cv::Rect(oBinImg.cols - 5, 0, 5, oBinImg.rows);
    cv::Mat  oRightImg = oBinImg(oRightROI);

    // get bottom image
    cv::Rect oBottomtROI = cv::Rect(0, oBinImg.rows - 5, oBinImg.cols, 5);
    cv::Mat  oBottomImg = oBinImg(oBottomtROI);

    // cv::imshow("oLeftImg", oLeftImg);
    // cv::imshow("oRightImg", oRightImg);
    // cv::imshow("oBottomImg", oBottomImg);
    // cvWaitKey(0);

    int nSum = cv::countNonZero(oLeftImg) + cv::countNonZero(oRightImg)
        + cv::countNonZero(oBottomImg);
    int nArea = 2 * 5 * oBinImg.rows + 5 * oBinImg.cols;

    if (static_cast<float>(nSum) / static_cast<float>(nArea) >= m_fThreshold) {
        stResult.nState = 1;
        stResult.oROI = m_oROI;
    } else {
        stResult.nState = 0;
        stResult.oROI = m_oROI;
    }

    return 1;
}

int CShootGameHurtRegMethod::Release() {
    return 1;
}

// **************************************************************************************
//          CShootGameHurtReg Class Deifne
// **************************************************************************************

CShootGameHurtReg::CShootGameHurtReg() {
    m_oVecParams.clear();  // clear vector of parameters
    m_oVecMethods.clear();  // clear vector of methods
}

CShootGameHurtReg::~CShootGameHurtReg() {
}

int CShootGameHurtReg::Initialize(IRegParam *pParam) {
    // check parameters
    if (NULL == pParam) {
        LOGE("CShootGameHurtReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CShootGameHurtRegParam *pP = dynamic_cast<CShootGameHurtRegParam*>(pParam);

    if (NULL == pP) {
        LOGE("CShootGameHurtReg -- CShootGameHurtRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0) {
        LOGE("CShootGameHurtReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty()) {
        LOGE("task ID %d: CShootGameHurtReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE) {
        LOGE("task ID %d: CShootGameHurtReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        CShootGameHurtRegMethod oMethod;

        int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
        if (1 != nState) {
            LOGE("task ID %d: CShootGameHurtReg -- initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CShootGameHurtReg -- CShootGameHurtReg initialization successful",
        m_nTaskID);
    return 1;
}

int CShootGameHurtReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    // check parameters
    if (NULL == pResult) {
        LOGE("task ID %d: CShootGameHurtReg -- IRegResult pointer is NULL, please check",
            m_nTaskID);
        return -1;
    }

    CShootGameHurtRegResult *pR = dynamic_cast<CShootGameHurtRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CShootGameHurtReg -- CShGHurtRegResult pointer is NULL, please check",
            m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: CShootGameHurtReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: CShootGameHurtReg -- frame index %d is invalid, please check",
            m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    tagShootGameHurtRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState) {
            LOGE("task ID %d: CShootGameHurtReg -- CShGHRegMethod predict failed, please check",
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

int CShootGameHurtReg::Release() {
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState) {
            LOGE("task ID %d: CShootGameHurtReg -- CShGHRegMethod release failed, please check",
                m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear();   // clear vector of parameters
    m_oVecMethods.clear();  // clear vector of methods

    LOGD("task ID %d: CShootGameHurtReg -- CShootGameHurtReg release successful", m_nTaskID);
    return 1;
}
