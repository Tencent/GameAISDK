/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/ImgProcess/CColorBinMatch.h"

// **************************************************************************************
//          CColorBinMatchFactory Class
// **************************************************************************************

CColorBinMatchFactory::CColorBinMatchFactory() {
}

CColorBinMatchFactory::~CColorBinMatchFactory() {
}

IImgProc* CColorBinMatchFactory::CreateImgProc() {
    return new CColorBinMatch();
}

// **************************************************************************************
//          CColorBinMatch Class
// **************************************************************************************

CColorBinMatch::CColorBinMatch() {
    m_oROI = cv::Rect(-1, -1, -1, -1);
    m_strMatchMethod = "CCOEFF_NORMED";
    m_oVecTmpls.clear();
}

CColorBinMatch::~CColorBinMatch() {
}


// init CColorBinMatch
int CColorBinMatch::Initialize(IImgProcParam *pParam) {
    if (NULL == pParam) {
        LOGE("ColorBinMatch: param point is NULL, please check");
        return -1;
    }

    CColorBinMatchParam *pP = dynamic_cast<CColorBinMatchParam*>(pParam);
    if (NULL == pP) {
        LOGE("ColorBinMatch: param point is NULL, please check");
        return -1;
    }

    int nState = ParseParam(pP);
    if (1 != nState) {
        LOGE("task ID %d: ColorBinMatch: parse param failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// given input image, return match result
int CColorBinMatch::Predict(IImgProcData *pData, IImgProcResult *pResult) {
    if (NULL == pData) {
        LOGE("task ID %d: ColorBinMatch: data point is NULL, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult) {
        LOGE("task ID %d: ColorBinMatch: result point is NULL, please check", m_nTaskID);
        return -1;
    }

    CObjDetData *pD = dynamic_cast<CObjDetData*>(pData);
    if (NULL == pD) {
        LOGE("task ID %d: ColorBinMatch: data point is NULL, please check", m_nTaskID);
        return -1;
    }

    CObjDetResult *pR = dynamic_cast<CObjDetResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: ColorBinMatch: result point is NULL, please check", m_nTaskID);
        return -1;
    }

    if (pD->m_oSrcImg.empty()) {
        LOGE("task ID %d: ColorBinMatch: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    // check roi region in image
    nState = CheckROI(m_nTaskID, pD->m_oSrcImg, m_oROI);
    if (1 != nState) {
        LOGE("task ID %d: ColorBinMatch: ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    //  extract roi region
    cv::Mat m_oSrcImgRoI = pD->m_oSrcImg(m_oROI);

    // if there exsits condition for binary, extract binary image based on condition
    if (m_oVecConditions.size() != 0) {
        ColorBinaryImage(m_oSrcImgRoI, m_oSrcImgRoI);
    }

    //    cv::imshow("m_oROI", m_oSrcImgRoI);
    //    cv::waitKey();
        // mathch template

        // perform template match based on rgb image or binary image
    nState = MatchTemplate(m_oSrcImgRoI, m_oVecTmpls, pR->m_oVecBBoxes);
    if (1 != nState) {
        LOGE("task ID %d: ColorBinMatch: match template failed, please check", m_nTaskID);
        return nState;
    }

    // re-compute the detected result
    for (int i = 0; i < static_cast<int>(pR->m_oVecBBoxes.size()); i++) {
        pR->m_oVecBBoxes[i].oRect.x = pR->m_oVecBBoxes[i].oRect.x + m_oROI.x;
        pR->m_oVecBBoxes[i].oRect.y = pR->m_oVecBBoxes[i].oRect.y + m_oROI.y;
    }

    // sort the detected results based on scores
    sort(pR->m_oVecBBoxes.begin(), pR->m_oVecBBoxes.end(), LessScore);

    return 1;
}

// release CColorBinMatch class
int CColorBinMatch::Release() {
    m_oVecTmpls.clear();

    return 1;
}

// parse string condition from json file
int CColorBinMatch::ParseParam(const CColorBinMatchParam *pParam) {
    if (pParam->m_nTaskID < 0) {
        LOGE("task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    m_nTaskID = pParam->m_nTaskID;

    int                nState;
    std::vector<float> oVecScales;

    // use the condition of color
    m_oVecConditions = pParam->m_oVecConditions;
    CColorDetParam oParam;
    if (m_oVecConditions.size() != 0) {
        for (int i = 0; i < static_cast<int>(m_oVecConditions.size()); i++) {
            nState = FillColorDetParam(m_oVecConditions[i], oParam);
            if (1 != nState) {
                LOGE("task ID %d: fill ColorDetParam failed, please check", m_nTaskID);
                return nState;
            }

            // printf("%f\n", oParam.m_fBlueOffset);
            // printf("%f\n", oParam.m_fGreenOffset);
            // printf("%f\n", oParam.m_fRedOffset);
            m_oVecParams.push_back(oParam);
        }
    }

    // compute scale considering multi-solution
    nState = ComputeScale(m_nTaskID, pParam->m_fMinScale, pParam->m_fMaxScale,
        pParam->m_nScaleLevel, &oVecScales);
    if (1 != nState) {
        LOGE("task ID %d: ColorBinMatch: compute scale failed, please check", m_nTaskID);
        return nState;
    }

    m_oROI = pParam->m_oROI;

    // dertemine type of template matching
    if (-1 != pParam->m_strOpt.find("CCORR_NORMED")) {
        m_strMatchMethod = "CCORR_NORMED";
    } else {
        m_strMatchMethod = "SQDIFF_NORMED";
    }

    if (pParam->m_oVecTmpls.empty()) {
        LOGE("task ID %d: ColorBinMatch: there is no template, please check", m_nTaskID);
        return -1;
    }

    // load template
    nState = LoadTemplate(m_nTaskID, pParam->m_oVecTmpls, oVecScales, m_oVecTmpls);

    if (1 != nState) {
        LOGE("task ID %d: ColorBinMatch: load template failed, please check", m_nTaskID);
        return nState;
    }

    // perform image binary
    if (m_oVecConditions.size() != 0) {
        ColorBinaryVector(&m_oVecTmpls);
    }

    return 1;
}

// binary image based on color threshold
void CColorBinMatch::ColorBinaryVector(std::vector<tagTmpl> *pVecTmpls) {
    for (int i = 0; i < static_cast<int>(pVecTmpls->size()); i++) {
        cv::Mat dstImage;
        ColorBinaryImage(pVecTmpls->at(i).oTmplImg, dstImage);
        pVecTmpls->at(i).oTmplImg = dstImage;
    }

    return;
}

// define how to get binary image
void CColorBinMatch::ColorBinaryImage(const cv::Mat &oSrcImg, cv::Mat &oDstImg) {
    cv::Mat dstImg;
    cv::Mat dstImgTotalOld;
    cv::Mat dstImgTotalNew;

    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        cv::inRange(oSrcImg,
            cv::Scalar(static_cast<double>(m_oVecParams[i].m_nBlueLower),
                static_cast<double>(m_oVecParams[i].m_nGreenLower),
                static_cast<double>(m_oVecParams[i].m_nRedLower)),
            cv::Scalar(static_cast<double>(m_oVecParams[i].m_nBlueUpper),
                static_cast<double>(m_oVecParams[i].m_nGreenUpper),
                static_cast<double>(m_oVecParams[i].m_nRedUpper)),
            dstImg);

        if (i == 0) {
            dstImg.copyTo(dstImgTotalOld);
            dstImg.copyTo(dstImgTotalNew);
        } else {
            dstImgTotalNew.copyTo(dstImgTotalOld);
            cv::bitwise_or(dstImgTotalOld, dstImg, dstImgTotalNew);
        }
    }

    //    cv::imshow("dstImgTotalNew", dstImgTotalNew);
    //    cv::waitKey();
    oDstImg = dstImgTotalNew;
    return;
}

// define how to match template based on RGB image or binary image
int CColorBinMatch::MatchTemplate(const cv::Mat &oSrcImg,
    const std::vector<tagTmpl> &oVecTmpls,
    std::vector<tagBBox> &oVecBBoxes) {
    oVecBBoxes.clear();

    for (int i = 0; i < static_cast<int>(oVecTmpls.size()); i++) {
        tagTmpl stTmpl = oVecTmpls.at(i);

        int nResultRows = oSrcImg.rows - stTmpl.oTmplImg.rows + 1;
        int nResultCols = oSrcImg.cols - stTmpl.oTmplImg.cols + 1;

        float hScale = (static_cast<float>(stTmpl.oTmplImg.rows)
            / static_cast<float>(stTmpl.oRect.height));

        float wScale = static_cast<float>(stTmpl.oTmplImg.cols)
            / static_cast<float>(stTmpl.oRect.width);

        float fScale = (hScale + wScale) / 2.0f;

        if (nResultRows <= 0 || nResultCols <= 0) {
            LOGD("task ID %d: source image is smaller than template image in scale %f",
                m_nTaskID, fScale);
            continue;
        }

        cv::Mat oResult(nResultRows, nResultCols, CV_32FC1);

        if ("SQDIFF_NORMED" == m_strMatchMethod) {
            // perform template matching
            cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_SQDIFF_NORMED);

            double    dMinVal;
            double    dMaxVal;
            cv::Point oMinLoc;
            cv::Point oMaxLoc;
            cv::minMaxLoc(oResult, &dMinVal, &dMaxVal, &oMinLoc, &oMaxLoc);

            float fScore = static_cast<float>(1 - dMinVal);
            if (fScore >= stTmpl.fThreshold) {
                tagBBox stBBox;
                stBBox.nClassID = stTmpl.nClassID;
                stBBox.fScore = fScore;
                stBBox.fScale = fScale;
                snprintf(stBBox.szTmplName, sizeof(stBBox.szTmplName), "%s",
                    stTmpl.strTmplName.c_str());
                stBBox.oRect = cv::Rect(oMinLoc.x, oMinLoc.y, stTmpl.oTmplImg.cols,
                    stTmpl.oTmplImg.rows);
                oVecBBoxes.push_back(stBBox);
            }
        } else {
            if (stTmpl.oMaskImg.empty()) {
                cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_CCORR_NORMED);
            } else {
#ifdef OPENCV2
                cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_CCORR_NORMED);
#endif

#ifdef OPENCV3
                cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult,
                    CV_TM_CCORR_NORMED, stTmpl.oMaskImg);
#endif
            }

            // get location with maximum score
            double    dMinVal;
            double    dMaxVal;
            cv::Point oMinLoc;
            cv::Point oMaxLoc;
            cv::minMaxLoc(oResult, &dMinVal, &dMaxVal, &oMinLoc, &oMaxLoc);

            float fScore = static_cast<float>(dMaxVal);
            if (fScore >= stTmpl.fThreshold) {
                tagBBox stBBox;
                stBBox.nClassID = stTmpl.nClassID;
                stBBox.fScore = fScore;
                stBBox.fScale = fScale;
                snprintf(stBBox.szTmplName, sizeof(stBBox.szTmplName), "%s",
                    stTmpl.strTmplName.c_str());
                stBBox.oRect = cv::Rect(oMaxLoc.x, oMaxLoc.y, stTmpl.oTmplImg.cols,
                    stTmpl.oTmplImg.rows);
                oVecBBoxes.push_back(stBBox);
            }
        }
    }

    return 1;
}

// set ROI region of image
int CColorBinMatch::SetROI(cv::Rect const &oROI) {
    m_oROI = oROI;

    return 1;
}

// get threshold for RGB channels
int CColorBinMatch::FillColorDetParam(const std::string &strCondition, CColorDetParam &oParam) {
    if (strCondition.empty()) {
        LOGE("task ID %d: condition is empty, please check", m_nTaskID);
        return -1;
    }

    int nState = GetRGB(m_nTaskID,
        strCondition,
        oParam.m_nRedLower, oParam.m_nRedUpper,
        oParam.m_nGreenLower, oParam.m_nGreenUpper,
        oParam.m_nBlueLower, oParam.m_nBlueUpper);
    if (1 != nState) {
        LOGE("task ID %d: get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

