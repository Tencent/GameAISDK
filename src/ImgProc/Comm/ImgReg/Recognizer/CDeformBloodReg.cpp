/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CDeformBloodReg.h"

// **************************************************************************************
//          CDeformBloodRegColorDet Class Define
// **************************************************************************************

CDeformBloodRegColorDet::CDeformBloodRegColorDet()
{
    m_nTaskID      = -1; // task id
    m_nBloodLength = 100; // blood length
    m_oROI         = cv::Rect(-1, -1, -1, -1); // detection ROI
}

CDeformBloodRegColorDet::~CDeformBloodRegColorDet()
{}

int CDeformBloodRegColorDet::Initialize(const int nTaskID, const tagDeformBloodRegParam &stParam)
{
    if (nTaskID < 0)
    {
        LOGE("CDeformBloodRegColorDet -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    if (stParam.nBloodLength <= 0)
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- blood length %d is invalid, please check",
            m_nTaskID, stParam.nBloodLength);
        return -1;
    }

    int nState;

    // fill parameters of yolo recognizer
    CYOLOAPIParam oYOLOAPIParam;
    nState = FillYOLOAPIParam(stParam, oYOLOAPIParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- CYOLOAPI fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize yolo recognizer
    nState = m_oYOLOAPI.Initialize(oYOLOAPIParam);
    if (1 != nState)
    {
        m_oYOLOAPI.Release();
        LOGE("task ID %d: CDeformBloodRegColorDet -- CYOLOAPI initialization failed, please check", m_nTaskID);
        return nState;
    }

    // fill parameters of color detection recognizer
    CColorDetParam oColorDetParam;
    nState = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize color detection recognizer
    nState = m_oColorDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- CColorDet initialization failed, please check", m_nTaskID);
        m_oColorDet.Release();
        return nState;
    }

    m_nBloodLength = stParam.nBloodLength;
    m_oROI         = stParam.oROI;

    return 1;
}

int CDeformBloodRegColorDet::Predict(const cv::Mat &oSrcImg, tagDeformBloodRegResult &stResult)
{
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    CYOLOAPIData   oYOLOAPIData;
    CYOLOAPIResult oYOLOAPIResult;
    oYOLOAPIData.m_oSrcImg = oSrcImg;

    // detect bloods
    nState = m_oYOLOAPI.Predict(oYOLOAPIData, oYOLOAPIResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CDeformBloodRegColorDet -- CYOLOAPI predict failed, please check", m_nTaskID);
        stResult.nState    = 0;
        stResult.nBloodNum = 0;
        stResult.oROI      = m_oROI;
        return nState;
    }

    if (oYOLOAPIResult.m_oVecBBoxes.empty())
    {
        stResult.nState    = 1;
        stResult.nBloodNum = 0;
        stResult.oROI      = m_oROI;
    }

    std::vector<tagBlood> oVecBloods;

    for (int i = 0; i < static_cast<int>(oYOLOAPIResult.m_oVecBBoxes.size()); i++)
    {
        CPixDetData   oPixDetData;
        CPixDetResult oPixDetResult;
        oPixDetData.m_oSrcImg = oSrcImg;
        oPixDetData.m_oROI    = oYOLOAPIResult.m_oVecBBoxes[i].oRect;

        // detect blood color in blood location
        nState = m_oColorDet.Predict(&oPixDetData, &oPixDetResult);
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformBloodRegColorDet -- CColorDet predict failed, please check", m_nTaskID);
            stResult.nState    = 0;
            stResult.nBloodNum = 0;
            stResult.oROI      = m_oROI;
            return nState;
        }

        if (oPixDetResult.m_oVecPoints.empty())
        {
            continue;
        }

        // find blood contours
        std::vector<std::vector<cv::Point> > oVecContours;
        std::vector<cv::Vec4i>               oVecHierarchies;
        findContours(oPixDetResult.m_oDstImg, oVecContours, oVecHierarchies, cv::RETR_EXTERNAL,
            cv::CHAIN_APPROX_NONE, cv::Point());

        if (oVecContours.empty())
        {
            continue;
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
        tagBlood stBlood;
        stBlood.fPercent = (MAX(oRect.size.width, oRect.size.height) / m_nBloodLength) * 100;
        stBlood.oRect    = oYOLOAPIResult.m_oVecBBoxes[i].oRect;
        stBlood.fScore   = oYOLOAPIResult.m_oVecBBoxes[i].fScore;
        snprintf(stBlood.szName, sizeof(stBlood.szName), "%s", oYOLOAPIResult.m_oVecBBoxes[i].szTmplName);
        oVecBloods.push_back(stBlood);
    }

    // set blood result
    stResult.nState    = 1;
    stResult.nBloodNum = MIN(static_cast<int>(oVecBloods.size()), MAX_BLOOD_SIZE);
    stResult.oROI      = m_oROI;

    for (int i = 0; i < static_cast<int>(oVecBloods.size()); i++)
    {
        if (i < MAX_BLOOD_SIZE)
        {
            stResult.szBloods[i] = oVecBloods[i];
        }
        else
        {
            LOGD("task ID %d: CDeformBloodRegColorDet -- blood number is more than max blood size %d",
                m_nTaskID, MAX_BLOOD_SIZE);
        }
    }

    return 1;
}

int CDeformBloodRegColorDet::Release()
{
    // release recognizers
    m_oYOLOAPI.Release();
    m_oColorDet.Release();

    return 1;
}

int CDeformBloodRegColorDet::FillColorDetParam(const tagDeformBloodRegParam &stParam, CColorDetParam &oParam)
{
    oParam.m_nTaskID      = m_nTaskID;
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
        LOGE("task ID %d: CDeformBloodRegColorDet -- get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CDeformBloodRegColorDet::FillYOLOAPIParam(const tagDeformBloodRegParam &stElement, CYOLOAPIParam &oParam)
{
    oParam.m_nTaskID       = m_nTaskID;
    oParam.m_fThreshold    = stElement.fThreshold;
    oParam.m_oROI          = stElement.oROI;
    oParam.m_strCfgPath    = stElement.strCfgPath;
    oParam.m_strWeightPath = stElement.strWeightPath;
    oParam.m_strNamePath   = stElement.strNamePath;

    return 1;
}

// **************************************************************************************
//          CDeformBloodReg Class Define
// **************************************************************************************

CDeformBloodReg::CDeformBloodReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CDeformBloodReg::~CDeformBloodReg()
{}

int CDeformBloodReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CDeformBloodReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CDeformBloodRegParam *pP = dynamic_cast<CDeformBloodRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CDeformBloodReg -- CDeformBloodRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CDeformBloodReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CDeformBloodReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CDeformBloodReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        CDeformBloodRegColorDet oMethod;

        int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformBloodReg -- CDeformBloodRegColorDet initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CDeformBloodReg -- CDeformBloodReg initialization successful", m_nTaskID);
    return 1;
}

int CDeformBloodReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CDeformBloodReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CDeformBloodReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: CDeformBloodReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CDeformBloodRegResult *pR = dynamic_cast<CDeformBloodRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CDeformBloodReg -- CDeformBloodRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagDeformBloodRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformBloodReg -- CDeformBloodRegColorDet predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CDeformBloodReg::Release()
{
    // release recognizers
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformBloodReg -- CDeformBloodRegColorDet release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGD("task ID %d: CDeformBloodReg -- CDeformBloodReg release successful", m_nTaskID);
    return 1;
}
