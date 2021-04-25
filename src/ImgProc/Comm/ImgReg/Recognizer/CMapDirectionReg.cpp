/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CMapDirectionReg.h"

// **************************************************************************************
//          CMapDirectionRegColorDet Class Define
// **************************************************************************************

CMapDirectionRegColorDet::CMapDirectionRegColorDet() {
    m_nTaskID = -1;
    m_oROI = cv::Rect(-1, -1, -1, -1);
    m_nErodeSize = 3;
    m_nRegionSize = 30;
    m_nDilateSize = 2;
}

CMapDirectionRegColorDet::~CMapDirectionRegColorDet() {
}

int CMapDirectionRegColorDet::Initialize(const int nTaskID, tagMapDirectionRegParam *pParam) {
    if (nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    tagMapDirectionRegParam stParam = *pParam;

    int nState;

    CColorDetParam oColorDetParam;

    // init color threshold of agent
    stParam.strCondition = stParam.strMyLocCondition;
    nState = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: MyLoc CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // detect location of agent according to color threshold
    nState = m_oMyLocDet.Initialize(&oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: MyLoc CColorDet initialization failed, please check", m_nTaskID);
        m_oMyLocDet.Release();
        return nState;
    }

    // init color threshold of view
    stParam.strCondition = stParam.strViewLocCondition;
    nState = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: ViewLoc CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // detect location of view
    nState = m_oViewLocDet.Initialize(&oColorDetParam);
    if (1 != nState) {
        LOGE("task ID %d: ViewLoc CColorDet initialization failed, please check", m_nTaskID);
        m_oViewLocDet.Release();
        return nState;
    }

    m_oROI = stParam.oROI;

    // if the foreground mask is defined, load the corresponding mask
    if (stParam.strMapMaskPath != "") {
        cv::Mat oMapMask;
        oMapMask = cv::imread(stParam.strMapMaskPath, 0);
        cv::threshold(oMapMask, m_oMapMask, 100, 255, CV_THRESH_BINARY);
    }

    m_nErodeSize = stParam.nErodeSize;
    m_nDilateSize = stParam.nDilateSize;
    m_nRegionSize = stParam.nRegionSize;

    return 1;
}

// detect location of the agent, the center of view and view vector
int CMapDirectionRegColorDet::Predict(const cv::Mat &oSrcImg, tagMapDirectionRegResult &stResult) {
    if (oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;
    cv::Mat oMapMask;
    cv::Mat oSrcImgROIMask;
    int             nLocPixelNumThresh = 2;
    cv::RotatedRect oMyLocRect;
    int             nMyLocState = 0;

    CPixDetData   oPixDetData;
    CPixDetResult oViewLocPixDetResult;
    CPixDetResult oMyLocPixDetResult;

    // clone mask and extract roi region
    cv::Mat oSrcImgMask = oSrcImg.clone();
    cv::Mat oSrcImgROI = oSrcImgMask(m_oROI);

    // resize mask to make it same size with the roi region
    cv::resize(m_oMapMask, oMapMask, m_oROI.size());
    oSrcImgROI.copyTo(oSrcImgROIMask, oMapMask);

    // obtain the image region under foreground mask
    cv::addWeighted(oSrcImgROI, 0, oSrcImgROIMask, 1, 0, oSrcImgROI);

    oPixDetData.m_oROI = m_oROI;
    oPixDetData.m_oSrcImg = oSrcImgMask;

    // obtain the location of agent
    nState = m_oMyLocDet.Predict(&oPixDetData, &oMyLocPixDetResult);

    cv::Mat structureElement = cv::getStructuringElement(cv::MORPH_RECT,
        cv::Size(m_nDilateSize, m_nDilateSize));

    // dilate binary result to generate larger region
    cv::dilate(oMyLocPixDetResult.m_oDstImg, oMyLocPixDetResult.m_oDstImg, structureElement);

    if (1 != nState) {
        LOGE("task ID %d: MyLoc CColorDet predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        return nState;
    }

    stResult.oROI = m_oROI;

    // detect the location of agent
    if (oMyLocPixDetResult.m_oVecPoints.empty()) {
        nMyLocState = 0;
        stResult.oMyLocPoint.x = -1;
        stResult.oMyLocPoint.y = -1;
    } else {
        std::vector<std::vector<cv::Point> > oVecImgContours;
        std::vector<cv::Vec4i>               oVecImgHierarchies;
        findContours(oMyLocPixDetResult.m_oDstImg, oVecImgContours, oVecImgHierarchies,
            cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

        if (oVecImgContours.empty()) {
            nMyLocState = 0;
            stResult.oMyLocPoint.x = -1;
            stResult.oMyLocPoint.y = -1;
        } else {
            // find the center of agent
            nMyLocState = 1;
            int nMaxSize = 0;

            for (int i = 0; i < static_cast<int>(oVecImgContours.size()); i++) {
                if (static_cast<int>(oVecImgContours[i].size()) >= nMaxSize &&
                    static_cast<int>(oVecImgContours[i].size()) >= nLocPixelNumThresh) {
                    nMaxSize = static_cast<int>(oVecImgContours[i].size());
                    oMyLocRect = cv::minAreaRect(oVecImgContours[i]);
                    stResult.oMyLocPoint = oMyLocRect.center;
                }
            }
        }
    }

    // detect center of view around agent
    // m_nRegionSize is set as the area for searching
    cv::Rect m_oROIRegion;
    if (nMyLocState == 1) {
        m_oROIRegion = cv::Rect(static_cast<int>(stResult.oMyLocPoint.x - m_nRegionSize),
            static_cast<int>(stResult.oMyLocPoint.y - m_nRegionSize),
            static_cast<int>(2 * m_nRegionSize),
            static_cast<int>(2 * m_nRegionSize));
    } else {
        m_oROIRegion = m_oROI;
    }

    oPixDetData.m_oSrcImg = oSrcImgMask;
    oPixDetData.m_oROI = m_oROIRegion;

    // Use color  threshold to find the corresponing region
    nState = m_oViewLocDet.Predict(&oPixDetData, &oViewLocPixDetResult);

    if (1 != nState) {
        LOGE("task ID %d: ViewLoc CColorDet predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        return nState;
    }

    // Use erode to reduce noise
    structureElement = cv::getStructuringElement(cv::MORPH_RECT,
        cv::Size(m_nErodeSize, m_nErodeSize));

    cv::erode(oViewLocPixDetResult.m_oDstImg, oViewLocPixDetResult.m_oDstImg, structureElement);

    cv::RotatedRect oViewLocRect;
    int             nViewLocState = 0;
    if (oViewLocPixDetResult.m_oVecPoints.empty()) {
        nViewLocState = 0;
        stResult.oViewLocPoint.x = -1;
        stResult.oViewLocPoint.y = -1;
    } else {
        std::vector<std::vector<cv::Point> > oVecImgContours;
        std::vector<cv::Vec4i>               oVecImgHierarchies;
        findContours(oViewLocPixDetResult.m_oDstImg, oVecImgContours, oVecImgHierarchies,
            cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

        // detect the location of view
        if (oVecImgContours.empty()) {
            nViewLocState = 0;
            stResult.oViewLocPoint.x = -1;
            stResult.oViewLocPoint.y = -1;
        } else {
            nViewLocState = 1;
            int nMaxSize = 0;

            for (int i = 0; i < static_cast<int>(oVecImgContours.size()); i++) {
                if (static_cast<int>(oVecImgContours[i].size()) >= nMaxSize) {
                    nMaxSize = static_cast<int>(oVecImgContours[i].size());
                    oViewLocRect = cv::minAreaRect(oVecImgContours[i]);
                    stResult.oViewLocPoint = oViewLocRect.center;
                }
            }
        }
    }

    if (nMyLocState == 1 || nViewLocState == 1) {
        stResult.nState = 1;
    } else {
        stResult.nState = 0;
    }

    // obtain the view direction based on the location of agent and view center
    if (nMyLocState == 1 && nViewLocState == 1) {
        stResult.oViewAnglePoint = stResult.oViewLocPoint - stResult.oMyLocPoint;
    } else {
        stResult.oViewAnglePoint.x = -1;
        stResult.oViewAnglePoint.y = -1;
    }

    return 1;
}

// **************************************************************************************
//          CMapDirectionRegColorDet Release Define
// **************************************************************************************


int CMapDirectionRegColorDet::Release() {
    m_oMyLocDet.Release();
    m_oViewLocDet.Release();

    return 1;
}

// **************************************************************************************
//          CMapDirectionReg FillColorDetParam Define
// **************************************************************************************

int CMapDirectionRegColorDet::FillColorDetParam(const tagMapDirectionRegParam &stParam,
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
        LOGE("task ID %d: get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CMapDirectionReg Class Define
// **************************************************************************************

CMapDirectionReg::CMapDirectionReg() {
    m_oVecParams.clear();
    m_oVecMethods.clear();
}

CMapDirectionReg::~CMapDirectionReg() {
}

// **************************************************************************************
//          CMapDirectionReg Initialize Define
// **************************************************************************************

int CMapDirectionReg::Initialize(IRegParam *pParam) {
    if (NULL == pParam) {
        LOGE("IRegParam pointer is NULL, please check");
        return -1;
    }

    CMapDirectionRegParam *pP = dynamic_cast<CMapDirectionRegParam*>(pParam);

    if (NULL == pP) {
        LOGE("CMapDirectionRegParam pointer is NULL, please check");
        return -1;
    }

    m_nTaskID = pP->m_nTaskID;

    if (pP->m_oVecElements.empty()) {
        LOGE("task ID %d: param vector is empty, please check", m_nTaskID);
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

    m_oVecParams = pP->m_oVecElements;

    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        CMapDirectionRegColorDet oMethod;

        int nState = oMethod.Initialize(m_nTaskID, &m_oVecParams[i]);
        if (1 != nState) {
            LOGE("task ID %d: CMapDirectionRegColorDet initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGI("task ID %d: CMapDirectionReg initialization successful", m_nTaskID);
    return 1;
}

// **************************************************************************************
//          CMapDirectionReg Predict Define
// **************************************************************************************

int CMapDirectionReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult) {
        LOGE("task ID %d: IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CMapDirectionRegResult *pR = dynamic_cast<CMapDirectionRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CDeformBloodRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagMapDirectionRegResult szResults[MAX_ELEMENT_SIZE];

    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState) {
            LOGE("task ID %d: CMapDirectionRegColorDet predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

// **************************************************************************************
//          CMapDirectionReg Release Define
// **************************************************************************************

int CMapDirectionReg::Release() {
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++) {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState) {
            LOGE("task ID %d: CMapDirectionRegColorDet release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear();
    m_oVecMethods.clear();

    LOGI("task ID %d: CMapDirectionReg release successful", m_nTaskID);
    return 1;
}

