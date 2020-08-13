/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"

// **************************************************************************************
//          CColorMatch Factory Class Define
// **************************************************************************************

CColorMatchFactory::CColorMatchFactory()
{}

CColorMatchFactory::~CColorMatchFactory()
{}

IImgProc* CColorMatchFactory::CreateImgProc()
{
    return new CColorMatch();
}

// **************************************************************************************
//          CColorMatch Class Define
// **************************************************************************************

CColorMatch::CColorMatch()
{
    m_strMethod = "CCOEFF_NORMED"; // name of matching method
    m_oVecTmpls.clear(); // clear vector of matching templates
}

CColorMatch::~CColorMatch()
{}

int CColorMatch::Initialize(IImgProcParam *pParam)
{
    // check parameter pointer
    if (NULL == pParam)
    {
        LOGE("CColorMatch -- IImgProcParam pointer is NULL, please check");
        return -1;
    }

    // conver parameter pointer
    CColorMatchParam *pP = dynamic_cast<CColorMatchParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CColorMatch -- CColorMatchParam pointer is NULL, please check");
        return -1;
    }

    // parse parameters
    int nState = ParseParam(pP);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- parse parameters failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CColorMatch::Predict(IImgProcData *pData, IImgProcResult *pResult)
{
    int nState = 0;

    // convert pointer
    nState = CheckPointer(pData, pResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- check pointer failed, please check", m_nTaskID);
        return nState;
    }

    // convert data pointer
    CObjDetData *pD = dynamic_cast<CObjDetData*>(pData);
    if (NULL == pD)
    {
        LOGE("task ID %d: CColorMatch -- CObjDetData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // convert result pointer
    CObjDetResult *pR = dynamic_cast<CObjDetResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CColorMatch -- CObjDetResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // clear result
    pR->m_oVecBBoxes.clear();

    // set ROI
    cv::Rect oROI;
    nState = SetROI(pD, &oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- set ROI failed, please check", m_nTaskID);
        return nState;
    }

    // detect in ROI
    std::vector<tagBBox> oVecBBoxes;
    nState = MatchTemplate(pD->m_oSrcImg(oROI), m_oVecTmpls, oVecBBoxes);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- match template failed, please check", m_nTaskID);
        return nState;
    }

    // set result
    nState = SetResult(oROI, oVecBBoxes, pR);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- set result failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CColorMatch::Release()
{
    m_oVecTmpls.clear(); // clear vector of matching templates

    return 1;
}

int CColorMatch::ParseParam(const CColorMatchParam *pParam)
{
    int nState = 0;

    // check task ID
    if (pParam->m_nTaskID < 0)
    {
        LOGE("CColorMatch -- task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    // set task ID
    m_nTaskID = pParam->m_nTaskID;

    // set ROI
    m_oROI = pParam->m_oROI;

    // set matching method
    if (-1 != pParam->m_strOpt.find("SQDIFF_NORMED"))
    {
        m_strMethod = "SQDIFF_NORMED";
    }

    if (-1 != pParam->m_strOpt.find("CCOEFF_NORMED"))
    {
        m_strMethod = "CCOEFF_NORMED";
    }

    if (-1 != pParam->m_strOpt.find("CCORR_NORMED"))
    {
        m_strMethod = "CCORR_NORMED";
    }

    // compute scales for multi-scale matching
    std::vector<float> oVecScales;
    nState = ComputeScale(m_nTaskID, pParam->m_fMinScale, pParam->m_fMaxScale, pParam->m_nScaleLevel, &oVecScales);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- compute scale failed, please check", m_nTaskID);
        return nState;
    }

    // load matching templates
    nState = LoadTemplate(m_nTaskID, pParam->m_oVecTmpls, oVecScales, m_oVecTmpls);
    if (1 != nState)
    {
        LOGE("task ID %d: CColorMatch -- load template failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CColorMatch::MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls,
    std::vector<tagBBox> &oVecBBoxes)
{
    oVecBBoxes.clear();

    // match source image with each template
    for (int i = 0; i < static_cast<int>(oVecTmpls.size()); i++)
    {
        tagTmpl stTmpl = oVecTmpls.at(i);

        int nResultRows = oSrcImg.rows - stTmpl.oTmplImg.rows + 1;
        int nResultCols = oSrcImg.cols - stTmpl.oTmplImg.cols + 1;

        float fScale = (static_cast<float>(stTmpl.oTmplImg.rows) / static_cast<float>(stTmpl.oRect.height) +
            static_cast<float>(stTmpl.oTmplImg.cols) / static_cast<float>(stTmpl.oRect.width)) / 2.0f;

        // if source image is smaller than template image, skip template matching
        if (nResultRows <= 0 || nResultCols <= 0)
        {
            LOGD("task ID %d: CColorMatch -- source image is smaller than template image in scale %f", m_nTaskID, fScale);
            continue;
        }

        cv::Mat oResult(nResultRows, nResultCols, CV_32FC1);

        // match template according to different matching methods
        if ("SQDIFF_NORMED" == m_strMethod)
        {
            cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_SQDIFF_NORMED);
        }

        if ("CCOEFF_NORMED" == m_strMethod)
        {
            cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_CCOEFF_NORMED);
        }

        if ("CCORR_NORMED" == m_strMethod)
        {
            if (stTmpl.oMaskImg.empty())
            {
                // not use mask in matching
                cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_CCORR_NORMED);
            }
            else
            {
                // use mask in matching
                cv::matchTemplate(oSrcImg, stTmpl.oTmplImg, oResult, CV_TM_CCORR_NORMED, stTmpl.oMaskImg);
            }
        }

        // find matching bboxes that satisfies the condition
        for (int r = 0; r < nResultRows; r++)
        {
            float *pResult = oResult.ptr<float>(r);

            for (int c = 0; c < nResultCols; c++)
            {
                float fScore = 0.0f;

                // compute score according to different matching methods
                if ("SQDIFF_NORMED" == m_strMethod)
                {
                    fScore = static_cast<float>(1 - pResult[c]);
                }

                if ("CCOEFF_NORMED" == m_strMethod || "CCORR_NORMED" == m_strMethod)
                {
                    fScore = static_cast<float>(pResult[c]);
                }

                if (fScore >= stTmpl.fThreshold)
                {
                    tagBBox stBBox = tagBBox(stTmpl.nClassID, fScore, fScale, stTmpl.strTmplName,
                        cv::Rect(c, r, stTmpl.oTmplImg.cols, stTmpl.oTmplImg.rows));
                    oVecBBoxes.push_back(stBBox);
                }
            }
        }
    }

    return 1;
}
