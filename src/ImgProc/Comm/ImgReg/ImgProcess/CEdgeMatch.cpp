/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/ImgProcess/CEdgeMatch.h"

// **************************************************************************************
//          CEdgeMatch Factory Class Define
// **************************************************************************************

CEdgeMatchFactory::CEdgeMatchFactory() {
}

CEdgeMatchFactory::~CEdgeMatchFactory() {
}

IImgProc* CEdgeMatchFactory::CreateImgProc() {
    return new CEdgeMatch();
}

// **************************************************************************************
//          CEdgeMatch Class Define
// **************************************************************************************

CEdgeMatch::CEdgeMatch() {
    m_oVecTmpls.clear();  // clear vector of matching templates
}

CEdgeMatch::~CEdgeMatch() {
}

int CEdgeMatch::Initialize(IImgProcParam *pParam) {
    // check parameter pointer
    if (NULL == pParam) {
        LOGE("CEdgeMatch -- IImgProcParam pointer is NULL, please check");
        return -1;
    }

    // conver parameter pointer
    CEdgeMatchParam *pP = dynamic_cast<CEdgeMatchParam*>(pParam);
    if (NULL == pP) {
        LOGE("CEdgeMatch -- CEdgeMatchParam pointer is NULL, please check");
        return -1;
    }

    // parse parameters
    int nState = ParseParam(pP);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- parse parameters failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CEdgeMatch::Predict(IImgProcData *pData, IImgProcResult *pResult) {
    int nState = 0;

    // convert pointer
    nState = CheckPointer(pData, pResult);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- check pointer failed, please check", m_nTaskID);
        return nState;
    }

    // convert data pointer
    CObjDetData *pD = dynamic_cast<CObjDetData*>(pData);
    if (NULL == pD) {
        LOGE("task ID %d: CEdgeMatch -- CObjDetData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // convert result pointer
    CObjDetResult *pR = dynamic_cast<CObjDetResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CEdgeMatch -- CObjDetResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // clear result
    pR->m_oVecBBoxes.clear();

    // set ROI
    cv::Rect oROI;
    nState = SetROI(pD, &oROI);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- set ROI failed, please check", m_nTaskID);
        return nState;
    }

    // detect in ROI
    std::vector<tagBBox> oVecBBoxes;
    nState = MatchTemplate(pD->m_oSrcImg(oROI), m_oVecTmpls, oVecBBoxes);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- match template failed, please check", m_nTaskID);
        return nState;
    }

    // set result
    nState = SetResult(oROI, oVecBBoxes, pR);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- set Result failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CEdgeMatch::Release() {
    m_oVecTmpls.clear();  // clear vector of matching templates

    return 1;
}

int CEdgeMatch::ParseParam(const CEdgeMatchParam *pParam) {
    int nState = 0;

    // check task ID
    if (pParam->m_nTaskID < 0) {
        LOGE("CEdgeMatch -- task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    // set task ID
    m_nTaskID = pParam->m_nTaskID;

    // set ROI
    m_oROI = pParam->m_oROI;

    // compute scales for multi-scale matching
    std::vector<float> oVecScales;
    nState = ComputeScale(m_nTaskID, pParam->m_fMinScale, pParam->m_fMaxScale,
        pParam->m_nScaleLevel, &oVecScales);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- compute scale failed, please check", m_nTaskID);
        return nState;
    }

    // load matching templates
    nState = LoadTemplate(m_nTaskID, pParam->m_oVecTmpls, oVecScales, m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- load template failed, please check", m_nTaskID);
        return nState;
    }

    // extract edge for each template
    for (int i = 0; i < static_cast<int>(m_oVecTmpls.size()); i++) {
        cv::Mat oTmplImg;
        nState = ExtractEdge(m_oVecTmpls[i].oTmplImg, oTmplImg);
        if (1 != nState) {
            LOGE("task ID %d: CEdgeMatch -- extract edge in template image failed, please check",
                m_nTaskID);
            return nState;
        }

        m_oVecTmpls[i].oTmplImg = oTmplImg;
    }

    return 1;
}

int CEdgeMatch::ExtractEdge(const cv::Mat &oSrcImg, cv::Mat &oDstImg) {
    // check source image
    if (oSrcImg.empty()) {
        LOGE("task ID %d: CEdgeMatch -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // convert source image to gray image
    cv::Mat oGrayImg;
    int nState = ConvertColorToGray(m_nTaskID, oSrcImg, oGrayImg);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- convert color to gray failed, please check", m_nTaskID);
        return nState;
    }

    // binarize image to get edge
    cv::adaptiveThreshold(oGrayImg, oDstImg, 255.0, cv::ADAPTIVE_THRESH_MEAN_C,
        cv::THRESH_BINARY, 7, 5);

    return 1;
}

int CEdgeMatch::MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls,
    std::vector<tagBBox> &oVecBBoxes) {
    oVecBBoxes.clear();

    // extract edge in source image
    cv::Mat oEdgeImg;
    int nState = ExtractEdge(oSrcImg, oEdgeImg);
    if (1 != nState) {
        LOGE("task ID %d: CEdgeMatch -- extract edge in source image failed, please check",
            m_nTaskID);
        return nState;
    }

    // match edge image with each template
    for (int i = 0; i < static_cast<int>(oVecTmpls.size()); i++) {
        tagTmpl stTmpl = oVecTmpls.at(i);

        int nResultRows = oEdgeImg.rows - stTmpl.oTmplImg.rows + 1;
        int nResultCols = oEdgeImg.cols - stTmpl.oTmplImg.cols + 1;

        float fScale = (static_cast<float>(stTmpl.oTmplImg.rows) /
            static_cast<float>(stTmpl.oRect.height) + static_cast<float>(stTmpl.oTmplImg.cols) /
            static_cast<float>(stTmpl.oRect.width)) / 2.0f;

        // if edge image is smaller than template image, skip template matching
        if (nResultRows <= 0 || nResultCols <= 0) {
            LOGD("task ID %d: CEdgeMatch--edge image is smaller than template image in scale %f",
                m_nTaskID, fScale);
            continue;
        }

        cv::Mat oResult(nResultRows, nResultCols, CV_32FC1);

        // match template
        cv::matchTemplate(oEdgeImg, stTmpl.oTmplImg, oResult, CV_TM_CCOEFF_NORMED);

        // find matching bboxes that satisfies the condition
        for (int r = 0; r < nResultRows; r++) {
            float *pResult = oResult.ptr<float>(r);

            for (int c = 0; c < nResultCols; c++) {
                float fScore = static_cast<float>(pResult[c]);
                if (fScore >= stTmpl.fThreshold) {
                    tagBBox stBBox = tagBBox(stTmpl.nClassID, fScore, fScale, stTmpl.strTmplName,
                        cv::Rect(c, r, stTmpl.oTmplImg.cols, stTmpl.oTmplImg.rows));
                    oVecBBoxes.push_back(stBBox);
                }
            }
        }
    }

    return 1;
}
