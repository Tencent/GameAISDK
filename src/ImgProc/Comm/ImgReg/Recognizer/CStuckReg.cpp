/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CStuckReg.h"

// **************************************************************************************
//          CStuckRegTmplMatch Class Define
// **************************************************************************************

CStuckRegTmplMatch::CStuckRegTmplMatch()
{
    m_nTaskID        = -1; // task ID
    m_nPrevState     = 0; // previous state
    m_nMatchHeight   = 64;
    m_nMatchWidth    = 64;
    m_fIntervalTime  = 5.0f; // interval time
    m_fThreshold     = 0.95f; // matching threshold
    m_cTime = clock();
}

CStuckRegTmplMatch::~CStuckRegTmplMatch()
{}

int CStuckRegTmplMatch::Initialize(const int nTaskID, const tagStuckRegElement &stParam)
{
    // check task ID
    if (nTaskID < 0)
    {
        LOGE("CStuckRegTmplMatch -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    // check interval time
    if (stParam.fIntervalTime <= 0)
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- interval time(s) %f is invalid, please check",
            m_nTaskID, stParam.fIntervalTime);
        return -1;
    }

    // check matching threshold
    if (stParam.fThreshold <= 0)
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- threshold %f is invalid, please check",
            m_nTaskID, stParam.fThreshold);
        return -1;
    }

    // check matching height
    if (stParam.nMatchHeight <= 0)
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- match height %d is invalid, please check",
            m_nTaskID, stParam.nMatchHeight);
        return -1;
    }

    // check matching width
    if (stParam.nMatchWidth <= 0)
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- match width %d is invalid, please check",
            m_nTaskID, stParam.nMatchWidth);
        return -1;
    }

    // check mask
    if (!stParam.strMaskPath.empty())
    {
        // load mask
        m_oMaskImg = cv::imread(stParam.strMaskPath);
        if (m_oMaskImg.empty())
        {
            LOGE("task ID %d: CStuckRegTmplMatch -- cannot read mask image : %s, please check",
                m_nTaskID, stParam.strMaskPath.c_str());
            return -1;
        }
    }

    // copy parameters
    m_fIntervalTime = stParam.fIntervalTime;
    m_fThreshold    = stParam.fThreshold;
    m_oROI          = stParam.oROI;
    m_nMatchHeight  = stParam.nMatchHeight;
    m_nMatchWidth   = stParam.nMatchWidth;

    m_hStateLock = TqcOsCreateMutex(); // state locker
    m_hTimeLock = TqcOsCreateMutex(); // time locker

    return 1;
}

int CStuckRegTmplMatch::Predict(const cv::Mat &oSrcImg, const int nFrameIdx, tagStuckRegResult &stResult)
{
    // check source image
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    // check ROI
    int nState = CheckROI(m_nTaskID, oSrcImg, m_oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CStuckRegTmplMatch -- ROI rectangle is invalid, please check", m_nTaskID);
        return nState;
    }

    // use mask or not
    cv::Mat oTmpImg;
    if (m_oMaskImg.empty())
    {
        oSrcImg.copyTo(oTmpImg);
    }
    else
    {
        cv::Mat oMaskImg;
        cv::resize(m_oMaskImg, oMaskImg, cv::Size(oSrcImg.cols, oSrcImg.rows));
        oSrcImg.copyTo(oTmpImg, oMaskImg);
    }

    // copy ROI
    stResult.oROI = m_oROI;

    // resize ROI image
    cv::Mat oROIImg;
    cv::resize(oTmpImg(m_oROI), oROIImg, cv::Size(m_nMatchWidth, m_nMatchHeight));

    // set current image as template image
    if (m_oTmplImg.empty())
    {
        TqcOsAcquireMutex(m_hTimeLock);
        m_cTime = clock();
        TqcOsReleaseMutex(m_hTimeLock);

        TqcOsAcquireMutex(m_hStateLock);
        m_nPrevState = 0;
        TqcOsReleaseMutex(m_hStateLock);

        m_oTmplImg = oROIImg.clone();

        stResult.nState = 0;
        return 1;
    }

    // compute interval time
    TqcOsAcquireMutex(m_hTimeLock);
    float fInterval = static_cast<float>(clock() - m_cTime) / CLOCKS_PER_SEC;
    TqcOsReleaseMutex(m_hTimeLock);

    if (fInterval < m_fIntervalTime)
    {
        TqcOsAcquireMutex(m_hStateLock);
        stResult.nState = m_nPrevState;
        TqcOsReleaseMutex(m_hStateLock);

        return 1;
    }

    // compare current image with template image
    cv::Mat oResult(1, 1, CV_32FC1);
    cv::matchTemplate(oROIImg, m_oTmplImg, oResult, CV_TM_SQDIFF_NORMED);

    double    dMinVal;
    double    dMaxVal;
    cv::Point oMinLoc;
    cv::Point oMaxLoc;
    cv::minMaxLoc(oResult, &dMinVal, &dMaxVal, &oMinLoc, &oMaxLoc);

    float fScore = static_cast<float>(1 - dMinVal);
    if (fScore >= m_fThreshold)
    {
        stResult.nState = 1;
    }
    else
    {
        stResult.nState = 0;
    }

    TqcOsAcquireMutex(m_hTimeLock);
    m_cTime = clock();
    TqcOsReleaseMutex(m_hTimeLock);

    TqcOsAcquireMutex(m_hStateLock);
    m_nPrevState = stResult.nState;
    TqcOsReleaseMutex(m_hStateLock);

    m_oTmplImg = oROIImg.clone();

    return 1;
}

int CStuckRegTmplMatch::Release()
{
    // release lockers
    TqcOsDeleteMutex(m_hStateLock);
    TqcOsDeleteMutex(m_hTimeLock);

    return 1;
}

// **************************************************************************************
//          CStuckReg Class Define
// **************************************************************************************

CStuckReg::CStuckReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CStuckReg::~CStuckReg()
{}

int CStuckReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CStuckReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CStuckRegParam *pP = dynamic_cast<CStuckRegParam*>(pParam);

    if (NULL == pP)
    {
        LOGE("CStuckReg -- CStuckRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CStuckReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CStuckReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CStuckReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        CStuckRegTmplMatch oMethod;

        int nState = oMethod.Initialize(m_nTaskID, m_oVecParams[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CStuckReg -- CStuckRegTmplMatch initialization failed, please check", m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGD("task ID %d: CStuckReg -- CStuckReg initialization successful", m_nTaskID);
    return 1;
}

int CStuckReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (NULL == pResult)
    {
        LOGE("task ID %d: CStuckReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CStuckRegResult *pR = dynamic_cast<CStuckRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CStuckReg -- CStuckRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CStuckReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CStuckReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    tagStuckRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, stData.nFrameIdx, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CStuckReg -- CStuckRegTmplMatch predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CStuckReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CStuckReg -- CStuckRegTmplMatch release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGD("task ID %d: CStuckReg -- CStuckReg release successful", m_nTaskID);
    return 1;
}
