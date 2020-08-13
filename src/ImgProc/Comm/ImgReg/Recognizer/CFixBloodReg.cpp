/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CFixBloodReg.h"

// **************************************************************************************
//          CFixBloodRegColorDet Class Define
// **************************************************************************************

CFixBloodRegColorDet::CFixBloodRegColorDet()
{
    m_nTaskID      = -1; // task id
    m_nBloodLength = 100; // blood length
    m_oROI         = cv::Rect(-1, -1, -1, -1); // detection ROI
}

CFixBloodRegColorDet::~CFixBloodRegColorDet()
{}

int CFixBloodRegColorDet::Initialize(const int nTaskID, const tagFixBloodRegParam &stParam)
{
    // check parameters
    if (nTaskID < 0)
    {
        LOGE("CFixBloodRegColorDet -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    if (stParam.nBloodLength <= 0)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- blood length %d is invalid, please check",
            nTaskID, stParam.nBloodLength);
        return -1;
    }

    // copy task id
    m_nTaskID = nTaskID;

    int nState;

    // fill parameters
    CColorDetParam oParam;
    nState = FillColorDetParam(stParam, oParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize method
    nState = m_oMethod.Initialize(&oParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- CColorDet initialization failed, please check", m_nTaskID);
        m_oMethod.Release();
        return nState;
    }

    // copy parameters
    m_nBloodLength = stParam.nBloodLength;
    m_oROI         = stParam.oROI;

    return 1;
}

int CFixBloodRegColorDet::Predict(const cv::Mat &oSrcImg, tagFixBloodRegResult &stResult)
{
    // check parameters
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    // check ROI
    nState = CheckROI(m_nTaskID, oSrcImg, m_oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    // set input data
    CPixDetData   oData;
    CPixDetResult oResult;
    oData.m_oSrcImg = oSrcImg;

    // run method
    nState = m_oMethod.Predict(&oData, &oResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- CColorDet predict failed, please check", m_nTaskID);
        return nState;
    }

    if (oResult.m_oVecPoints.empty())
    {
        stResult.nState   = 0;
        stResult.fPercent = 0.0f;
        stResult.oROI     = m_oROI;
        return 1;
    }

    // find blood contours
    std::vector<std::vector<cv::Point> > oVecContours;
    std::vector<cv::Vec4i>               oVecHierarchies;
    findContours(oResult.m_oDstImg, oVecContours, oVecHierarchies, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

    if (oVecContours.empty())
    {
        stResult.nState   = 0;
        stResult.fPercent = 0.0f;
        stResult.oROI     = m_oROI;
        return 1;
    }

    // compute blood rectangles
    cv::RotatedRect oRect;
    int nMaxSize = 0;
    for (int i = 0; i < static_cast<int>(oVecContours.size()); i++)
    {
        if (static_cast<int>(oVecContours[i].size()) >= nMaxSize)
        {
            nMaxSize = static_cast<int>(oVecContours[i].size());
            oRect    = cv::minAreaRect(oVecContours[i]);
        }
    }

    // get blood percent and other infomation
    stResult.nState   = 1;
    stResult.fPercent = round(((MAX(oRect.size.width, oRect.size.height) / m_nBloodLength) * 100.0) / 20.0) * 20.0;
    stResult.oROI     = m_oROI;
    stResult.oRect    = oRect.boundingRect();

    return 1;
}

int CFixBloodRegColorDet::Release()
{
    // release method
    m_oMethod.Release();

    return 1;
}

int CFixBloodRegColorDet::FillColorDetParam(const tagFixBloodRegParam &stParam, CColorDetParam &oParam)
{
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nMaxPointNum = stParam.nMaxPointNum;
    oParam.m_nFilterSize  = stParam.nFilterSize;
    oParam.m_oROI         = stParam.oROI;

    int nState = GetRGB(m_nTaskID,
                        stParam.strCondition,
                        oParam.m_nRedLower, oParam.m_nRedUpper,
                        oParam.m_nGreenLower, oParam.m_nGreenUpper,
                        oParam.m_nBlueLower, oParam.m_nBlueUpper);
    if (1 != nState)
    {
        LOGE("task ID %d: CFixBloodRegColorDet -- get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CFixBloodReg Class Define
// **************************************************************************************

CFixBloodReg::CFixBloodReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CFixBloodReg::~CFixBloodReg()
{}

int CFixBloodReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CFixBloodReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CFixBloodRegParam *pP = dynamic_cast<CFixBloodRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CFixBloodReg -- CFixBloodRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CFixBloodReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CFixBloodReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CFixBloodReg -- element number is more than max element size %d",
            pParam->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        CFixBloodRegColorDet oMethod;

        int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CFixBloodReg -- CFixBloodRegColorDet initialization failed, please check", m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CFixBloodReg -- CFixBloodReg initialization successful", m_nTaskID);
    return 1;
}

int CFixBloodReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CFixBloodReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CFixBloodReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: CFixBloodReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CFixBloodRegResult *pR = dynamic_cast<CFixBloodRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CFixBloodReg -- CFixBloodRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagFixBloodRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CFixBloodReg -- CFixBloodRegColorDet predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CFixBloodReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CFixBloodReg -- CFixBloodRegColorDet release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGD("task ID %d: CFixBloodReg -- CFixBloodReg release successful", m_nTaskID);
    return 1;
}
