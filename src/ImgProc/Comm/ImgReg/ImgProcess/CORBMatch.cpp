/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/ImgProcess/CORBMatch.h"

// **************************************************************************************
//          CORBMatch Factory Class Define
// **************************************************************************************

CORBMatchFactory::CORBMatchFactory()
{}

CORBMatchFactory::~CORBMatchFactory()
{}

IImgProc* CORBMatchFactory::CreateImgProc()
{
    return new CORBMatch();
}

// **************************************************************************************
//          CORBMatch Class Define
// **************************************************************************************

CORBMatch::CORBMatch()
{
    m_oVecTmpls.clear(); // clear vector of matching templates
}

CORBMatch::~CORBMatch()
{}

int CORBMatch::Initialize(IImgProcParam *pParam)
{
    // check parameter pointer
    if (NULL == pParam)
    {
        LOGE("CORBMatch -- IImgProcParam pointer is NULL, please check");
        return -1;
    }

    CORBMatchParam *pP = dynamic_cast<CORBMatchParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CORBMatch -- CORBMatchParam pointer is NULL, please check");
        return -1;
    }

    // parse parameters
    int nState = ParseParam(pP);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- parse parameters failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CORBMatch::Predict(IImgProcData *pData, IImgProcResult *pResult)
{
    int nState = 0;

    // convert pointer
    nState = CheckPointer(pData, pResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- check pointer failed, please check", m_nTaskID);
        return nState;
    }

    // convert data pointer
    CObjDetData *pD = dynamic_cast<CObjDetData*>(pData);
    if (NULL == pD)
    {
        LOGE("task ID %d: CORBMatch -- CObjDetData pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // convert result pointer
    CObjDetResult *pR = dynamic_cast<CObjDetResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CORBMatch -- CObjDetResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    // clear result
    pR->m_oVecBBoxes.clear();

    // set ROI
    cv::Rect oROI;
    nState = SetROI(pD, &oROI);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- set ROI failed, please check", m_nTaskID);
        return nState;
    }

    // detect in ROI
    std::vector<tagBBox> oVecBBoxes;
    nState = MatchTemplate(pD->m_oSrcImg(oROI), m_oVecTmpls, oVecBBoxes);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- match template failed, please check", m_nTaskID);
        return nState;
    }

    // set result
    nState = SetResult(oROI, oVecBBoxes, pR);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- set result failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CORBMatch::Release()
{
    m_oVecTmpls.clear(); // clear vector of matching templates

    return 1;
}

int CORBMatch::ParseParam(const CORBMatchParam *pParam)
{
    int nState = 0;

    // check task ID
    if (pParam->m_nTaskID < 0)
    {
        LOGE("CORBMatch -- task ID %d is invalid, please check", pParam->m_nTaskID);
        return -1;
    }

    // set task ID
    m_nTaskID = pParam->m_nTaskID;

    // set ROI
    m_oROI = pParam->m_oROI;

    // check ORB parameters
    if (pParam->m_nFeatureNum <= 0)
    {
        LOGE("task ID %d: CORBMatch -- feature number is invalid, please check", m_nTaskID);
        return -1;
    }

    if (pParam->m_nLevel <= 0)
    {
        LOGE("task ID %d: CORBMatch -- level is invalid, please check", m_nTaskID);
        return -1;
    }

    if (pParam->m_nEdgeThreshold <= 0)
    {
        LOGE("task ID %d: CORBMatch -- edge threshold is invalid, please check", m_nTaskID);
        return -1;
    }

    if (pParam->m_fScaleFactor <= 0)
    {
        LOGE("task ID %d: CORBMatch -- scale factor is invalid, please check", m_nTaskID);
        return -1;
    }

    // set ORB
    m_oORB = cv::ORB::create(pParam->m_nFeatureNum, pParam->m_fScaleFactor, pParam->m_nLevel, pParam->m_nEdgeThreshold);

    // compute scales for multi-scale matching
    std::vector<float> oVecScales;
    nState = ComputeScale(m_nTaskID, pParam->m_fMinScale, pParam->m_fMaxScale, pParam->m_nScaleLevel, &oVecScales);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- compute scale failed, please check", m_nTaskID);
        return nState;
    }

    // load matching templates
    nState = LoadTemplate(m_nTaskID, pParam->m_oVecTmpls, oVecScales, m_oVecTmpls);
    if (1 != nState)
    {
        LOGE("task ID %d: CORBMatch -- load template failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CORBMatch::MatchTemplate(const cv::Mat &oSrcImg, const std::vector<tagTmpl> &oVecTmpls,
    std::vector<tagBBox> &oVecBBoxes)
{
    oVecBBoxes.clear();

    // set matcher
    float fKNNMatchRatio = 0.70f;
    cv::BFMatcher oMatcher(cv::NORM_HAMMING);

    // match source image with each template
    for (int i = 0; i < static_cast<int>(oVecTmpls.size()); i++)
    {
        tagTmpl stTmpl = oVecTmpls.at(i);

        float fScale = (static_cast<float>(stTmpl.oTmplImg.rows) / static_cast<float>(stTmpl.oRect.height) +
            static_cast<float>(stTmpl.oTmplImg.cols) / static_cast<float>(stTmpl.oRect.width)) / 2.0f;

        // if source image is smaller than template image, skip template matching
        // if (oSrcImg.rows < stTmpl.oTmplImg.rows || oSrcImg.cols < stTmpl.oTmplImg.cols)
        // {
        //    LOGD("task ID %d: CORBMatch -- source image is smaller than template image in scale %f", m_nTaskID, fScale);
        //    continue;
        // }

        // extract ORB feature
        cv::Mat oSrcFeature;
        cv::Mat oTmplFeature;
        std::vector<cv::KeyPoint> oVecSrcPoints;
        std::vector<cv::KeyPoint> oVecTmplPoints;
        m_oORB->detectAndCompute(oSrcImg, cv::Mat(), oVecSrcPoints, oSrcFeature);
        m_oORB->detectAndCompute(stTmpl.oTmplImg, cv::Mat(), oVecTmplPoints, oTmplFeature);

        if (oVecSrcPoints.empty())
        {
            LOGI("task ID %d: CORBMatch -- cannot extract ORB feature in source image", m_nTaskID);
            continue;
        }

        if (oVecTmplPoints.empty())
        {
            LOGI("task ID %d: CORBMatch -- cannot extract ORB feature in template image", m_nTaskID);
            continue;
        }

        // match ORB features
        std::vector<std::vector<cv::DMatch> > oVecMatches;
        oMatcher.knnMatch(oSrcFeature, oTmplFeature, oVecMatches, 2);

        // select matching features
        int nMatchNum = 0;
        for (int j = 0; j < static_cast<int>(oVecMatches.size()); j++)
        {
            if (oVecMatches[j][0].distance <= fKNNMatchRatio * oVecMatches[j][1].distance)
                nMatchNum++;
        }

        // compute matching score
        float fScore = nMatchNum / MIN(static_cast<float>(oSrcFeature.rows), static_cast<float>(oTmplFeature.rows));
        if (fScore > 1.0)
        {
            fScore = 1.0f;
        }

        if (fScore >= stTmpl.fThreshold)
        {
            tagBBox stBBox = tagBBox(stTmpl.nClassID, fScore, fScale, stTmpl.strTmplName,
                cv::Rect(0, 0, oSrcImg.cols, oSrcImg.rows));
            oVecBBoxes.push_back(stBBox);
        }
    }

    return 1;
}
