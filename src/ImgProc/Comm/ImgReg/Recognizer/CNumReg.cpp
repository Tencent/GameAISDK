/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CNumReg.h"

// **************************************************************************************
//          CNumRegTmplMatch Class Functions
// **************************************************************************************

CNumRegTmplMatch::CNumRegTmplMatch()
{
    m_nTaskID = -1; // task ID
    m_oROI = cv::Rect(-1, -1, -1, -1); // detection ROI
}

CNumRegTmplMatch::~CNumRegTmplMatch()
{}

int CNumRegTmplMatch::Initialize(const int nTaskID, const tagNumRegElement &stElement)
{
    // check task ID
    if (nTaskID < 0)
    {
        LOGE("CNumRegTmplMatch -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    // copy task ID
    m_nTaskID = nTaskID;

    // fill ColorMatch parameters
    CColorMatchParam oParam;
    oParam.m_nTaskID = nTaskID;
    oParam.m_nScaleLevel = stElement.nScaleLevel;
    oParam.m_fMinScale = stElement.fMinScale;
    oParam.m_fMaxScale = stElement.fMaxScale;
    oParam.m_oROI = stElement.oROI;
    oParam.m_oVecTmpls = stElement.oVecTmpls;
    oParam.m_strOpt = "-matchMethod CCOEFF_NORMED";

    // initialize method
    int nState = m_oMatchMethod.Initialize(&oParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CNumRegTmplMatch -- CColorMatch initialization failed, please check", m_nTaskID);
        return nState;
    }

    // copy ROI
    m_oROI = stElement.oROI;

    return 1;
}

int CNumRegTmplMatch::Predict(const cv::Mat &oSrcImg, tagNumRegResult &stResult)
{
    // check source image
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: CNumRegTmplMatch -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // set ObjDet input
    CObjDetData oData;
    CObjDetResult oResult;
    oData.m_oSrcImg = oSrcImg;

    // run ObjDet
    int nState = m_oMatchMethod.Predict(&oData, &oResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CNumRegTmplMatch -- CColorMatch predict failed, please check", m_nTaskID);
        return nState;
    }

    if (oResult.m_oVecBBoxes.empty())
    {
        stResult.nState = 0;
        stResult.fNum = 0.0f;
        stResult.oROI = m_oROI;
        return 1;
    }

    // merge and sort bboxes
    std::vector<tagBBox> oVecBBoxes;
    MergeBBox(oResult.m_oVecBBoxes, oVecBBoxes, 0.25);
    sort(oVecBBoxes.begin(), oVecBBoxes.end(), AscendBBoxX);

    // compute number
    float fNum = 0.0;
    for (int i = 0; i < static_cast<int>(oVecBBoxes.size()); i++)
    {
        fNum = fNum * 10 + oVecBBoxes[i].nClassID;
    }

    // set result
    stResult.nState = 1;
    stResult.fNum   = fNum;
    stResult.oROI = m_oROI;

    return 1;
}

int CNumRegTmplMatch::Release()
{
    // release method
    int nState = m_oMatchMethod.Release();
    if (1 != nState)
    {
        LOGE("task ID %d: CNumRegTmplMatch -- CColorMatch release failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CNumReg Class Functions
// **************************************************************************************

CNumReg::CNumReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CNumReg::~CNumReg()
{}

int CNumReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CNumReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CNumRegParam *pP = dynamic_cast<CNumRegParam*>(pParam);

    if (NULL == pP)
    {
        LOGE("CNumReg -- CNumRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CNumReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CNumReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CNumReg -- element number is more than max element size %d",
            pParam->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        if ("TemplateMatch" == m_oVecParams[i].oAlgorithm)
        {
            CNumRegTmplMatch oMethod;

            int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
            if (1 != nState)
            {
                LOGE("task ID %d: CNumReg -- CNumRegTmplMatch initialization failed, please check", m_nTaskID);
                return nState;
            }

            m_oVecMethods.push_back(oMethod);
        }
        else
        {
            LOGE("task ID %d: CNumReg -- algorithm %s is invalid, please check",
                m_nTaskID, m_oVecParams[i].oAlgorithm.c_str());
            return -1;
        }
    }

    LOGD("task ID %d: CNumReg -- CNumReg initialization successful", m_nTaskID);
    return 1;
}

int CNumReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (NULL == pResult)
    {
        LOGE("task ID %d: CNumReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CNumRegResult *pR = dynamic_cast<CNumRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CNumReg -- CNumRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CNumReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CNumReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    tagNumRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CNumReg -- CNumRegTmplMatch predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CNumReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CNumReg -- CNumRegTmplMatch release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGD("task ID %d: CNumReg -- CNumReg release successful", m_nTaskID);
    return 1;
}
