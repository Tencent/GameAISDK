/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CPixReg.h"

// **************************************************************************************
//          CPixReg Class Define
// **************************************************************************************

CPixReg::CPixReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CPixReg::~CPixReg()
{}

int CPixReg::Initialize(IRegParam *pParam)
{
    // check pointer
    if (NULL == pParam)
    {
        LOGE("CPixReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CPixRegParam *pP = dynamic_cast<CPixRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CPixReg -- CPixRegParam pointer is NULL, please check");
        return -1;
    }

    // check taskID
    if (pP->m_nTaskID < 0)
    {
        LOGE("CPixReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    // check element
    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CPixReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CPixReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        int nState;

        // fill parameters
        CColorDetParam oParam;
        nState = FillColorDetParam(m_oVecParams[i], oParam);
        if (1 != nState)
        {
            LOGE("task ID %d: CPixReg -- CColorDet fill param failed, please check", m_nTaskID);
            return nState;
        }

        // initialize method
        CColorDet oMethod;
        nState = oMethod.Initialize(&oParam);
        if (1 != nState)
        {
            LOGE("task ID %d: CPixReg -- CColorDet initialization failed, please check", m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CPixReg -- CPixReg initialization successful", m_nTaskID);
    return 1;
}

int CPixReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check frame index
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CPixReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    // check source image
    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CPixReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // check result pointer
    if (NULL == pResult)
    {
        LOGE("task ID %d: CPixReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CPixRegResult *pR = dynamic_cast<CPixRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CPixReg -- CPixRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagPixRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        // set PixDet input
        CPixDetData   oData;
        CPixDetResult oResult;
        oData.m_oSrcImg = stData.oSrcImg;

        // run PixDet
        int nState = m_oVecMethods[i].Predict(&oData, &oResult);
        if (1 != nState)
        {
            LOGE("task ID %d: CPixReg -- CColorDet predict failed, please check", m_nTaskID);
            return nState;
        }

        if (oResult.m_oVecPoints.empty())
        {
            szResults[i].nState    = 0;
            szResults[i].nPointNum = 0;
            szResults[i].oDstImg   = cv::Mat::zeros(oData.m_oSrcImg.rows, oData.m_oSrcImg.cols,
                                                    cv::DataType<uchar>::type);
        }
        else
        {
            szResults[i].nState    = 1;
            szResults[i].nPointNum = MIN(static_cast<int>(oResult.m_oVecPoints.size()), MAX_POINT_SIZE);
            szResults[i].oDstImg   = oResult.m_oDstImg;

            for (int j = 0; j < szResults[i].nPointNum; j++)
            {
                if (j < MAX_POINT_SIZE)
                {
                    szResults[i].szPoints[j] = oResult.m_oVecPoints[j];
                }
                else
                {
                    LOGD("task ID %d: CPixReg -- point number is more than max point size %d",
                        m_nTaskID, MAX_POINT_SIZE);
                }
            }
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CPixReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CPixReg -- CColorDet release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGD("task ID %d: CPixReg -- CPixReg release successful", m_nTaskID);
    return 1;
}

int CPixReg::FillColorDetParam(const tagPixRegElement &stParam, CColorDetParam &oParam)
{
    oParam.m_nTaskID      = m_nTaskID;
    oParam.m_nFilterSize  = stParam.nFilterSize;
    oParam.m_nMaxPointNum = stParam.nMaxPointNum;
    oParam.m_oROI         = stParam.oROI;

    int nState = GetRGB(m_nTaskID,
                        stParam.strCondition,
                        oParam.m_nRedLower, oParam.m_nRedUpper,
                        oParam.m_nGreenLower, oParam.m_nGreenUpper,
                        oParam.m_nBlueLower, oParam.m_nBlueUpper);
    if (1 != nState)
    {
        LOGE("task ID %d: CPixReg -- get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}
