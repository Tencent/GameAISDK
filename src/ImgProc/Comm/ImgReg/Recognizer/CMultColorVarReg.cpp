/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CMultColorVarReg.h"

// **************************************************************************************
//          CMultColorVarRegCalculate Class Deifne
// **************************************************************************************

CMultColorVarRegCalculate::CMultColorVarRegCalculate() {
    m_nTaskID = -1;
}

CMultColorVarRegCalculate::~CMultColorVarRegCalculate() {
}

int CMultColorVarRegCalculate::Initialize(const int nTaskID,
    const tagMultColorVarRegElement &stParam) {
    if (nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    for (int i = 0; i < DIRECTION_SIZE; i++) {
        m_oTmplImg[i] = cv::imread(stParam.strImageFilePath +
            '/' + stParam.szDirectionNames[i] + ".png", 1);
        m_oTmplMask[i] = cv::imread(stParam.strImageFilePath +
            '/' + stParam.szDirectionNames[i] + "Mask.png", 0);
        cv::Mat result = m_oTmplMask[i].clone();
        threshold(m_oTmplMask[i], result, 100, 255.0, CV_THRESH_BINARY);
        // cv::imshow("result", result);
        // cv::waitKey();

        cv::Mat matMean, matStddev;
        matMean = cv::Mat::zeros(3, 1, CV_32F);
        cv::meanStdDev(m_oTmplImg[i], matMean, matStddev, result);

        m_szColorMean[i][0] = matMean.at<double>(0, 0);
        m_szColorMean[i][1] = matMean.at<double>(1, 0);
        m_szColorMean[i][2] = matMean.at<double>(2, 0);

        // cv::imshow("m_oTmplImg", m_oTmplImg[i]);
        // cv::imshow("m_oTmplMask", m_oTmplMask[i]);
        // cv::waitKey();
    }

    return 1;
}

int CMultColorVarRegCalculate::Predict(const cv::Mat &oSrcImg, const int nFrameIdx,
    tagMultColorVarRegResult &stResult) {
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }


    cv::Mat oSrcImgCopy = oSrcImg.clone();
    cv::resize(oSrcImg, oSrcImgCopy, m_oTmplMask[0].size());

    double szColorMean[DIRECTION_SIZE][3];

    for (int i = 0; i < DIRECTION_SIZE; i++) {
        cv::Mat result = m_oTmplMask[i].clone();
        threshold(m_oTmplMask[i], result, 100, 255.0, CV_THRESH_BINARY);
        // cv::imshow("result", result);
        // cv::waitKey();

        cv::Mat matMean, matStddev;
        matMean = cv::Mat::zeros(3, 1, CV_32F);
        cv::meanStdDev(oSrcImgCopy, matMean, matStddev, result);

        szColorMean[i][0] = matMean.at<double>(0, 0);
        szColorMean[i][1] = matMean.at<double>(1, 0);
        szColorMean[i][2] = matMean.at<double>(2, 0);

        stResult.colorMeanVar[i] = abs(szColorMean[i][0] - m_szColorMean[i][0]) +
            abs(szColorMean[i][1] - m_szColorMean[i][1]) +
            abs(szColorMean[i][2] - m_szColorMean[i][2]);


        // cv::imshow("m_oTmplImg", m_oTmplImg[i]);
        // cv::imshow("m_oTmplMask", m_oTmplMask[i]);
        // cv::waitKey();
    }

    stResult.nState = 1;

    return 1;
}

int CMultColorVarRegCalculate::Release() {
    // TqcOsDeleteMutex(m_hStateLock);
    // TqcOsDeleteMutex(m_hTimeLock);

    return 1;
}

// **************************************************************************************
//          CMultColorVarReg Class Deifne
// **************************************************************************************

CMultColorVarReg::CMultColorVarReg() {
    m_oVecParams.clear();
    m_oVecMethods.clear();
}

CMultColorVarReg::~CMultColorVarReg() {
}

int CMultColorVarReg::Initialize(IRegParam *pParam) {
    if (NULL == pParam) {
        LOGE("IRegParam pointer is NULL, please check");
        return -1;
    }

    CMultColorVarRegParam *pP = dynamic_cast<CMultColorVarRegParam*>(pParam);

    if (NULL == pP) {
        LOGE("CMultColorVarRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE) {
        LOGE("task ID %d: element number is more than max element size %d",
            m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    m_nTaskID = pP->m_nTaskID;

    if (pP->m_oVecElements.empty()) {
        LOGE("task ID %d: param vector is empty, please check", m_nTaskID);
        return -1;
    }

    m_oVecParams = pP->m_oVecElements;

    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        CMultColorVarRegCalculate oMethod;

        int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
        if (1 != nState) {
            LOGE("task ID %d: CMultColorVarRegCalculate initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CMultColorVarReg initialization successful", m_nTaskID);
    return 1;
}

int CMultColorVarReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    if (NULL == pResult) {
        LOGE("task ID %d: IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CMultColorVarRegResult *pR = dynamic_cast<CMultColorVarRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CMultColorVarRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    tagMultColorVarRegResult szResults[MAX_ELEMENT_SIZE];

    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, stData.nFrameIdx, szResults[i]);
        if (1 != nState) {
            LOGE("task ID %d: CMultColorVarRegCalculate predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CMultColorVarReg::Release() {
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState) {
            LOGE("task ID %d: CMultColorVarRegCalculate release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear();
    m_oVecMethods.clear();

    LOGD("task ID %d: CMultColorVarReg release successful", m_nTaskID);
    return 1;
}

