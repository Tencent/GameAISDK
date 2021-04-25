/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CLocationReg.h"

// **************************************************************************************
//          CLocationRegTmplMatch Class Functions
// **************************************************************************************

CLocationRegTmplMatch::CLocationRegTmplMatch() {
    m_nTaskID = -1;  // task ID
    m_nMatchCount = 5;  // matching count
    m_fExpandWidth = 0.10f;  // width expand ratio
    m_fExpandHeight = 0.10f;  // height expand ratio
    m_strAlgorithm = "Detect";  // algorithm type
    m_oLocation = cv::Rect(-1, -1, -1, -1);  // inference locatioin
    m_oInferROI = cv::Rect(-1, -1, -1, -1);  // inference ROI

    m_oVecInferLocations.clear();  // clear vector of inference locatioins
    m_oVecLocationPoints.clear();  // clear vector of locatioin Points
    m_oVecROIPoints.clear();  // clear vector of ROI Points
    m_oVecDetRects.clear();  // clear vector of detection rectangles

    m_hDetRectLock = TqcOsCreateMutex();  // detection rectangle locker
}

CLocationRegTmplMatch::~CLocationRegTmplMatch() {
    TqcOsDeleteMutex(m_hDetRectLock);  // delete locker
}

int CLocationRegTmplMatch::Initialize(const int nTaskID, const tagLocationRegParam &stParam) {
    // check task ID
    if (nTaskID < 0) {
        LOGE("CLocationRegTmplMatch -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    // copy task ID
    m_nTaskID = nTaskID;

    // check matching count
    if (stParam.nMatchCount <= 0) {
        LOGE("task ID %d: CLocationRegTmplMatch -- match count %d is invalid, please check",
            m_nTaskID, stParam.nMatchCount);
        return -1;
    }

    // check width expand ratio
    if (stParam.fExpandWidth < 0 || stParam.fExpandWidth > 1) {
        LOGE("task ID %d: CLocationRegTmplMatch -- expand width %f is invalid, please check",
            m_nTaskID, stParam.fExpandWidth);
        return -1;
    }

    // check height expand ratio
    if (stParam.fExpandHeight < 0 || stParam.fExpandHeight > 1) {
        LOGE("task ID %d: CLocationRegTmplMatch -- expand height %f is invalid, please check",
            m_nTaskID, stParam.fExpandWidth);
        return -1;
    }

    // check algorithm type
    if ("Detect" != stParam.strAlgorithm && "Infer" != stParam.strAlgorithm) {
        LOGE("task ID %d: CLRegTmplMatch -- algorithm %s is invalid, please check",
            m_nTaskID, stParam.strAlgorithm.c_str());
        return -1;
    }

    int nState;

    // fill ColorMatch parameters
    CColorMatchParam oParam;
    nState = FillColorMatchParam(stParam, oParam);
    if (1 != nState) {
        LOGE("task ID %d: CLRegTmplMatch -- CColorMatch fill param failed, please check",
            m_nTaskID);
        return nState;
    }

    // initialize ColorMatch
    nState = m_oMethod.Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: CLRegTmplMatch -- CColorMatch initialization failed, please check",
            m_nTaskID);
        return nState;
    }

    // copy parameters
    if ("Detect" == stParam.strAlgorithm) {
        m_nMatchCount = stParam.nMatchCount;
        m_fExpandWidth = stParam.fExpandWidth;
        m_fExpandHeight = stParam.fExpandHeight;
        m_strAlgorithm = stParam.strAlgorithm;
        m_oLocation = stParam.oLocation;
    }

    if ("Infer" == stParam.strAlgorithm) {
        m_nMatchCount = stParam.nMatchCount;
        m_fExpandWidth = stParam.fExpandWidth;
        m_fExpandHeight = stParam.fExpandHeight;
        m_strAlgorithm = stParam.strAlgorithm;
        m_oLocation = stParam.oLocation;
        m_oInferROI = stParam.oInferROI;
        m_oVecInferLocations = stParam.oVecInferLocations;

        // set location points and ROI points
        SetPoint(m_oLocation, m_oVecLocationPoints);
        SetPoint(m_oInferROI, m_oVecROIPoints);
    }

    return 1;
}

int CLocationRegTmplMatch::Predict(const cv::Mat &oSrcImg, tagLocationRegResult &stResult) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: CLRegTmplMatch -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // set ROI
    cv::Rect oROI;
    SetROI(m_oLocation, oSrcImg.cols, oSrcImg.rows, oROI);

    // set ObjDet input
    CObjDetData   oData;
    CObjDetResult oResult;
    oData.m_oSrcImg = oSrcImg;
    oData.m_oROI = oROI;

    // run ObjDet
    int nState = m_oMethod.Predict(&oData, &oResult);
    if (1 != nState) {
        LOGE("task ID %d: CLRegTmplMatch -- CColorMatch predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        stResult.nRectNum = 0;
        stResult.fScale = 0.0f;
        return nState;
    }

    if (oResult.m_oVecBBoxes.empty()) {
        LOGI("task ID %d: CLRegTmplMatch -- cannot match template in ROI", m_nTaskID);
        stResult.nState = 1;
        stResult.nRectNum = 0;
        stResult.fScale = 0.0f;
        return 1;
    }

    // recode detection rectangles
    TqcOsAcquireMutex(m_hDetRectLock);
    m_oVecDetRects.push_back(oResult.m_oVecBBoxes[0].oRect);
    TqcOsReleaseMutex(m_hDetRectLock);
    if (m_oVecDetRects.size() < m_nMatchCount) {
        stResult.nState = 1;
        stResult.nRectNum = 0;
        stResult.fScale = 0.0f;
        return 1;
    }

    // compute average rectangle
    cv::Rect oAvgRect;
    TqcOsAcquireMutex(m_hDetRectLock);
    AverageRect(m_nTaskID, m_oVecDetRects, oAvgRect);
    TqcOsReleaseMutex(m_hDetRectLock);

    float fScale = 0.5f * (static_cast<float>(oAvgRect.width) / m_oLocation.width +
        static_cast<float>(oAvgRect.height) / m_oLocation.height);

    if ("Detect" == m_strAlgorithm) {
        stResult.nState = 1;
        stResult.nRectNum = 1;
        stResult.fScale = fScale;
        stResult.fScore = oResult.m_oVecBBoxes[0].fScore;
        stResult.szRects[0] = oAvgRect;

        return 1;
    }

    if ("Infer" == m_strAlgorithm) {
        cv::Rect oROILoc;
        InferROI(oAvgRect, fScale, oROILoc);
        nState = CheckROI(m_nTaskID, oSrcImg, oROILoc);

        std::vector<cv::Rect> oVecRects;
        InferLocation(oROILoc, fScale, oVecRects);

        stResult.nState = 1;
        stResult.nRectNum = static_cast<int>(oVecRects.size());
        stResult.fScale = fScale;

        for (int i = 0; i < static_cast<int>(oVecRects.size()); i++) {
            stResult.szRects[i] = oVecRects[i];
        }
    }

    return 1;
}

int CLocationRegTmplMatch::Release() {
    m_oVecInferLocations.clear();  // clear vector of inference locatioins
    m_oVecLocationPoints.clear();  // clear vector of locatioin Points
    m_oVecROIPoints.clear();  // clear vector of ROI Points
    m_oVecDetRects.clear();  // clear vector of detection rectangles

    // release ColorMatch
    int nState = m_oMethod.Release();
    if (1 != nState) {
        LOGE("task ID %d: CLocationRegTmplMatch -- CColorMatch release failed, please check",
            m_nTaskID);
        return nState;
    }

    return 1;
}

int CLocationRegTmplMatch::FillColorMatchParam(const tagLocationRegParam &stParam,
    CColorMatchParam &oParam) {
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oLocation;
    oParam.m_strOpt = "CCOEFF_NORMED";

    // analyze tmplate path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CLRegTmplMatch -- analyze template path failed, please check",
            m_nTaskID);
        return nState;
    }

    // copy location to template rectangle
    for (int i = 0; i < static_cast<int>(oParam.m_oVecTmpls.size()); i++) {
        if ((-1 == oParam.m_oVecTmpls[i].oRect.width && -1 == oParam.m_oVecTmpls[i].oRect.height) ||
            (0 == oParam.m_oVecTmpls[i].oRect.width && 0 == oParam.m_oVecTmpls[i].oRect.height)) {
            oParam.m_oVecTmpls[i].oRect = stParam.oLocation;
        }
    }

    return 1;
}

int CLocationRegTmplMatch::SetPoint(const cv::Rect &oRect, std::vector<cv::Point> &oVecPoints) {
    oVecPoints.clear();
    int x = 0;
    int y = 0;

    // left - top
    x = oRect.x;
    y = oRect.y;
    oVecPoints.push_back(cv::Point(x, y));

    // left-down
    x = oRect.x;
    y = oRect.y + oRect.height;
    oVecPoints.push_back(cv::Point(x, y));

    // right-top
    x = oRect.x + oRect.width;
    y = oRect.y;
    oVecPoints.push_back(cv::Point(x, y));

    // right-down
    x = oRect.x + oRect.width;
    y = oRect.y + oRect.height;
    oVecPoints.push_back(cv::Point(x, y));

    // top-middle
    x = static_cast<int>(oRect.x + 0.5 * oRect.width);
    y = oRect.y;
    oVecPoints.push_back(cv::Point(x, y));

    // left-middle
    x = oRect.x;
    y = static_cast<int>(oRect.y + 0.5 * oRect.height);
    oVecPoints.push_back(cv::Point(x, y));

    // right-middle
    x = oRect.x + oRect.width;
    y = static_cast<int>(oRect.y + 0.5 * oRect.height);
    oVecPoints.push_back(cv::Point(x, y));

    // down-middle
    x = static_cast<int>(oRect.x + 0.5 * oRect.width);
    y = oRect.y + oRect.height;
    oVecPoints.push_back(cv::Point(x, y));

    // center
    x = static_cast<int>(oRect.x + 0.5 * oRect.width);
    y = static_cast<int>(oRect.y + 0.5 * oRect.height);
    oVecPoints.push_back(cv::Point(x, y));

    return 1;
}

int CLocationRegTmplMatch::SetROI(const cv::Rect &oRect, int nImgWidth, int nImgHeight,
    cv::Rect &oROI) {
    // remove resize 1280
    /*
    if (nImgWidth > nImgHeight)
    {
        ResizeRect(oRect, static_cast<float>(nImgWidth) / IMAGE_LONG_SIDE,
                   static_cast<float>(nImgWidth) / IMAGE_LONG_SIDE, oROI);
    }
    else
    {
        ResizeRect(oRect, static_cast<float>(nImgHeight) / IMAGE_LONG_SIDE,
                   static_cast<float>(nImgHeight) / IMAGE_LONG_SIDE, oROI);
    }*/
    ResizeRect(oRect, 1.0f, 1.0f, oROI);

    ExpandRect(oROI, static_cast<int>(nImgWidth * m_fExpandWidth),
        static_cast<int>(nImgHeight * m_fExpandHeight), oROI);

    return 1;
}

int CLocationRegTmplMatch::InferROI(const cv::Rect &oRect, float fScale, cv::Rect &oROILoc) {
    // search closest two points between location points and ROI points
    int   nLocIdx = 0;
    int   nROIIdx = 0;
    float fMinDist = static_cast<float>(1e+8);

    for (int i = 0; i < m_oVecLocationPoints.size(); i++) {
        cv::Point oPt1 = m_oVecLocationPoints[i];

        for (int j = 0; j < m_oVecROIPoints.size(); j++) {
            cv::Point oPt2 = m_oVecROIPoints[j];

            int nDx = oPt1.x - oPt2.x;
            int nDy = oPt1.y - oPt2.y;

            float fDist = static_cast<float>(std::sqrt(nDx * nDx + nDy * nDy));
            if (fDist < fMinDist) {
                fMinDist = fDist;
                nLocIdx = i;
                nROIIdx = j;
            }
        }
    }

    // compute the offset of location points
    cv::Point oOffset = cv::Point(0, 0);
    ComputeOffset(nLocIdx, m_oLocation, oRect, oOffset);

    // apply offset to ROI point
    cv::Point oROIPoint;
    oROIPoint.x = m_oVecROIPoints[nROIIdx].x - oOffset.x;
    oROIPoint.y = m_oVecROIPoints[nROIIdx].y - oOffset.y;

    // infer ROI location
    int nInferWidth = static_cast<int>(fScale * m_oInferROI.width);
    int nInferHeight = static_cast<int>(fScale * m_oInferROI.height);

    if (0 == nROIIdx) {
        // left-top
        oROILoc.x = oROIPoint.x;
        oROILoc.y = oROIPoint.y;
    } else if (1 == nROIIdx) {
        // left-down
        oROILoc.x = oROIPoint.x;
        oROILoc.y = oROIPoint.y - nInferHeight;
    } else if (2 == nROIIdx) {
        // right-top
        oROILoc.x = oROIPoint.x - nInferWidth;
        oROILoc.y = oROIPoint.y;
    } else if (3 == nROIIdx) {
        // right-down
        oROILoc.x = oROIPoint.x - nInferWidth;
        oROILoc.y = oROIPoint.y - nInferHeight;
    } else if (4 == nROIIdx) {
        // top-middle
        oROILoc.x = static_cast<int>(oROIPoint.x - 0.5 * nInferWidth);
        oROILoc.y = oROIPoint.y;
    } else if (5 == nROIIdx) {
        // left-middle
        oROILoc.x = oROIPoint.x;
        oROILoc.y = static_cast<int>(oROIPoint.y - 0.5 * nInferHeight);
    } else if (6 == nROIIdx) {
        // right-middle
        oROILoc.x = oROIPoint.x - nInferWidth;
        oROILoc.y = static_cast<int>(oROIPoint.y - 0.5 * nInferHeight);
    } else if (7 == nROIIdx) {
        // down-middle
        oROILoc.x = static_cast<int>(oROIPoint.x - 0.5 * nInferWidth);
        oROILoc.y = oROIPoint.y - nInferHeight;
    } else {
        // center
        oROILoc.x = static_cast<int>(oROIPoint.x - 0.5 * nInferWidth);
        oROILoc.y = static_cast<int>(oROIPoint.y - 0.5 * nInferHeight);
    }

    oROILoc.width = nInferWidth;
    oROILoc.height = nInferHeight;

    return 1;
}

int CLocationRegTmplMatch::InferLocation(const cv::Rect &oROILoc, float fScale,
    std::vector<cv::Rect> &oVecRects) {
    oVecRects.clear();

    for (int i = 0; i < m_oVecInferLocations.size(); i++) {
        cv::Rect oRect;
        oRect.x = static_cast<int>((m_oVecInferLocations[i].x - m_oInferROI.x)
            * fScale + oROILoc.x);
        oRect.y = static_cast<int>((m_oVecInferLocations[i].y - m_oInferROI.y)
            * fScale + oROILoc.y);
        oRect.width = static_cast<int>(m_oVecInferLocations[i].width * fScale);
        oRect.height = static_cast<int>(m_oVecInferLocations[i].height * fScale);
        oVecRects.push_back(oRect);
    }

    return 1;
}

int CLocationRegTmplMatch::ComputeOffset(const int nLocIdx, const cv::Rect &oLocation,
    const cv::Rect &oRect, cv::Point &oOffset) {
    if (0 == nLocIdx) {
        // left - top
        oOffset.x = m_oLocation.x - oRect.x;
        oOffset.y = m_oLocation.y - oRect.y;
    } else if (1 == nLocIdx) {
        // left-down
        oOffset.x = m_oLocation.x - oRect.x;
        oOffset.y = m_oLocation.y + m_oLocation.height - oRect.y - oRect.height;
    } else if (2 == nLocIdx) {
        // right-top
        oOffset.x = m_oLocation.x + m_oLocation.width - oRect.x - oRect.width;
        oOffset.y = m_oLocation.y - oRect.y;
    } else if (3 == nLocIdx) {
        // right-down
        oOffset.x = m_oLocation.x + m_oLocation.width - oRect.x - oRect.width;
        oOffset.y = m_oLocation.y + m_oLocation.height - oRect.y - oRect.height;
    } else if (4 == nLocIdx) {
        // top-middle
        oOffset.x = static_cast<int>(m_oLocation.x + 0.5 * m_oLocation.width
            - oRect.x - 0.5 * oRect.width);
        oOffset.y = m_oLocation.y - oRect.y;
    } else if (5 == nLocIdx) {
        // left-middle
        oOffset.x = m_oLocation.x - oRect.x;
        oOffset.y = static_cast<int>(m_oLocation.y + 0.5 * m_oLocation.height
            - oRect.y - 0.5 * oRect.height);
    } else if (6 == nLocIdx) {
        // right-middle
        oOffset.x = m_oLocation.x + m_oLocation.width - oRect.x - oRect.width;
        oOffset.y = static_cast<int>(m_oLocation.y + 0.5 * m_oLocation.height - oRect.y
            - 0.5 * oRect.height);
    } else if (7 == nLocIdx) {
        // down-middle
        oOffset.x = static_cast<int>(m_oLocation.x + 0.5 * m_oLocation.width - oRect.x
            - 0.5 * oRect.width);
        oOffset.y = m_oLocation.y + m_oLocation.height - oRect.y - oRect.height;
    } else {
        // center
        oOffset.x = static_cast<int>(m_oLocation.x + 0.5 * m_oLocation.width - oRect.x
            - 0.5 * oRect.width);
        oOffset.y = static_cast<int>(m_oLocation.y + 0.5 * m_oLocation.height - oRect.y
            - 0.5 * oRect.height);
    }

    return 1;
}

// **************************************************************************************
//          CLocationReg Class Functions
// **************************************************************************************

CLocationReg::CLocationReg() {
}

CLocationReg::~CLocationReg() {
}

int CLocationReg::Initialize(IRegParam *pParam) {
    // check parameters
    if (NULL == pParam) {
        LOGE("CLocationReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CLocationRegParam *pP = dynamic_cast<CLocationRegParam*>(pParam);

    if (NULL == pP) {
        LOGE("CLocationReg -- CLRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0) {
        LOGE("CLocationReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_stParam = pP->m_stParam;

    // initialize method
    int nState = m_oMethod.Initialize(m_nTaskID, m_stParam);
    if (1 != nState) {
        LOGE("task ID %d: CLocationReg -- initialization failed, please check", m_nTaskID);
        return nState;
    }

    LOGD("task ID %d: CLocationReg -- CLocationReg initialization successful", m_nTaskID);
    return 1;
}

int CLocationReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    // check parameters
    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: CLocationReg -- frame index %d is invalid, please check",
            m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: CLocationReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult) {
        LOGE("task ID %d: CLocationReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CLocationRegResult *pR = dynamic_cast<CLocationRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CLocationReg -- CLocationRegResult pointer is NULL, please check",
            m_nTaskID);
        return -1;
    }

    tagLocationRegResult stResult;

    // run method
    int nState = m_oMethod.Predict(stData.oSrcImg, stResult);
    if (1 != nState) {
        LOGE("task ID %d: CLocationReg -- CLocationRegTmplMatch predict failed, please check",
            m_nTaskID);
        return nState;
    }

    // set result
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(&stResult);

    return 1;
}

int CLocationReg::Release() {
    // release method
    int nState = m_oMethod.Release();

    if (1 != nState) {
        LOGE("task ID %d: CLocationReg -- CLocationRegTmplMatch release failed, please check",
            m_nTaskID);
        return nState;
    }

    LOGD("task ID %d: CLocationReg -- CLocationReg release successful", m_nTaskID);
    return 1;
}

// **************************************************************************************
//          Interface for UI
// **************************************************************************************
int Detect(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg, const cv::Rect &oSrcRect,
    const float fThreshold, const float fExpandWidth, const float fExpandHeight,
    cv::Rect *pDstRect, float *pScore) {
    float   fResizeSrcRatio;
    cv::Mat oResizeSrcImg;

    ConvertImgTo720P(nID, oSrcImg, oResizeSrcImg, fResizeSrcRatio);

    float   fResizeTmplRatio;
    cv::Mat oResizeTmplImg;
    ConvertImgTo720P(nID, oTmplImg, oResizeTmplImg, fResizeTmplRatio);

    cv::Rect oResizeSrcRect;
    oResizeSrcRect.x = static_cast<int>(oSrcRect.x / fResizeTmplRatio);
    oResizeSrcRect.y = static_cast<int>(oSrcRect.y / fResizeTmplRatio);
    oResizeSrcRect.width = static_cast<int>(oSrcRect.width / fResizeTmplRatio);
    oResizeSrcRect.height = static_cast<int>(oSrcRect.height / fResizeTmplRatio);

    int nState = 0;

    nState = CheckROI(nID, oResizeTmplImg, oResizeSrcRect);
    if (1 != nState) {
        LOGE("UI ID %d: template rectangle is invalid, please check", nID);
        return nState;
    }

    tagTmpl stTmpl;
    stTmpl.fThreshold = fThreshold;
    stTmpl.oTmplImg = oResizeTmplImg(oResizeSrcRect);

    // it should recalculate position in source image according to template position
    cv::Rect oRealLocation;
    oRealLocation.x = static_cast<int>(oResizeSrcImg.cols * oResizeSrcRect.x / oResizeTmplImg.cols);
    oRealLocation.y = static_cast<int>(oResizeSrcImg.rows * oResizeSrcRect.y / oResizeTmplImg.rows);
    oRealLocation.width = static_cast<int>(oResizeSrcImg.cols
        * oResizeSrcRect.width / oResizeTmplImg.cols);
    oRealLocation.height = static_cast<int>(oResizeSrcImg.rows
        * oResizeSrcRect.height / oResizeTmplImg.rows);

    tagLocationRegParam stParam;
    stParam.strAlgorithm = "Detect";
    stParam.fMinScale = 0.8f;
    stParam.fMaxScale = 1.2f;
    stParam.nScaleLevel = 9;
    stParam.nMatchCount = 1;
    // stParam.oLocation = oResizeSrcRect;
    stParam.oLocation = oRealLocation;
    stParam.fExpandWidth = fExpandWidth;
    stParam.fExpandHeight = fExpandHeight;
    stParam.oVecTmpls.push_back(stTmpl);

    CLocationRegParam oParam;
    oParam.m_nTaskID = nID;
    oParam.m_stParam = stParam;

    tagRegData stData;
    stData.nFrameIdx = 1;
    stData.oSrcImg = oResizeSrcImg;

    CLocationReg oReg;
    nState = oReg.Initialize(&oParam);
    if (1 != nState) {
        LOGE("UI ID %d: CLocationReg initialize failed, please check", nID);
        return nState;
    }

    CLocationRegResult oResult;
    nState = oReg.Predict(stData, &oResult);
    if (1 != nState) {
        LOGE("UI ID %d: CLocationReg predict failed, please check", nID);
        return nState;
    }

    nState = oReg.Release();
    if (1 != nState) {
        LOGE("UI ID %d: CLocationReg release failed, please check", nID);
        return nState;
    }

    tagLocationRegResult stResult;
    oResult.GetResult(&stResult);

    if (1 == stResult.nState) {
        pDstRect->x = static_cast<int>(stResult.szRects[0].x * fResizeSrcRatio);
        pDstRect->y = static_cast<int>(stResult.szRects[0].y * fResizeSrcRatio);
        pDstRect->width = static_cast<int>(stResult.szRects[0].width * fResizeSrcRatio);
        pDstRect->height = static_cast<int>(stResult.szRects[0].height * fResizeSrcRatio);
        *pScore = stResult.fScore;
        return 1;
    } else {
        pDstRect->x = 0;
        pDstRect->y = 0;
        pDstRect->width = 0;
        pDstRect->height = 0;
        *pScore = 0.0f;
        return -1;
    }

    return 1;
}

int DetectPoint(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg,
    const tagActionState &oSrcPoint, cv::Point *pDstPoint) {
    int nExpandWidth = oSrcPoint.nTmplExpdWPixel;
    int nExpandHeight = oSrcPoint.nTmplExpdHPixel;
    int nCenterX = oSrcPoint.nActionX;
    int nCenterY = oSrcPoint.nActionY;

    int nLeft = MAX(nCenterX - nExpandWidth, 0);
    int nRight = MIN(nCenterX + nExpandWidth, oTmplImg.cols);
    int nTop = MAX(nCenterY - nExpandHeight, 0);
    int nDown = MIN(nCenterY + nExpandHeight, oTmplImg.rows);

    int nW = MIN(nCenterX - nLeft, nRight - nCenterX) * 2;
    int nH = MIN(nCenterY - nTop, nDown - nCenterY) * 2;
    int nX = nCenterX - nW / 2;
    int nY = nCenterY - nH / 2;

    cv::Rect oSrcRect = cv::Rect(nX, nY, nW, nH);

    float fThreshold = oSrcPoint.fActionThreshold;
    float fExpandWidth = oSrcPoint.fROIExpdWRatio;
    float fExpandHeight = oSrcPoint.fROIExpdHRatio;

    cv::Rect oDstRect;
    float fScore;
    int nState = Detect(nID, oSrcImg, oTmplImg, oSrcRect, fThreshold,
        fExpandWidth, fExpandHeight, &oDstRect, &fScore);
    if (1 != nState) {
        LOGE("UI ID %d: detect point failed, please check", nID);
        pDstPoint->x = 0;
        pDstPoint->y = 0;

        /*
        char szImageName[512] = { 0 };
        SNPRINTF(szImageName, 512, "src_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x,
        oSrcPoint.y, pDstPoint->x, pDstPoint->y);
        cv::imwrite(szImageName, oSrcImg);
        memset(szImageName, 0, sizeof(szImageName));
        printf("save src_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x, oSrcPoint.y,
        pDstPoint->x, pDstPoint->y);
        SNPRINTF(szImageName, 512, "template_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x,
        oSrcPoint.y, pDstPoint->x, pDstPoint->y);
        cv::imwrite(szImageName, oTmplImg);
        g_nImageIndex++;
        */

        return nState;
    }

    pDstPoint->x = static_cast<int>(oDstRect.x + oDstRect.width / 2);
    pDstPoint->y = static_cast<int>(oDstRect.y + oDstRect.height / 2);
    LOGI("UI ID %d: point x %d, x %d", nID, pDstPoint->x, pDstPoint->y);

    /*
    char szImageName[512] = { 0 };
    printf("save src_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x, oSrcPoint.y,
    pDstPoint->x, pDstPoint->y);
    SNPRINTF(szImageName, 512, "src_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x,
    oSrcPoint.y, pDstPoint->x, pDstPoint->y);
    cv::imwrite(szImageName, oSrcImg);
    memset(szImageName, 0, sizeof(szImageName));
    SNPRINTF(szImageName, 512, "template_%d__%d_%d-%d_%d.jpg", g_nImageIndex, oSrcPoint.x,
    oSrcPoint.y, pDstPoint->x, pDstPoint->y);
    cv::imwrite(szImageName, oTmplImg);
    g_nImageIndex++;
    */

    return 1;
}

int DetectRect(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg, const cv::Rect &oSrcRect,
    const float fThreshold, cv::Rect *pDstRect, float *pScore) {
    float fExpandWidth = 0.275f;
    float fExpandHeight = 0.275f;

    int nState = Detect(nID, oSrcImg, oTmplImg, oSrcRect, fThreshold, fExpandWidth,
        fExpandHeight, pDstRect, pScore);
    if (1 != nState) {
        LOGE("UI ID %d: detect rect failed, please check", nID);
        return nState;
    }

    return 1;
}

int DetectCloseIcon(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg,
    const cv::Rect &oSrcRect, const float fThreshold, cv::Rect *pDstRect, float *pScore) {
    float fExpandWidth = 1.0f;
    float fExpandHeight = 1.0f;

    int nState = Detect(nID, oSrcImg, oTmplImg, oSrcRect, fThreshold,
        fExpandWidth, fExpandHeight, pDstRect, pScore);
    if (1 != nState) {
        LOGE("UI ID %d: detect close icon failed, please check", nID);
        return nState;
    }

    return 1;
}
