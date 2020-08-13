/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CMapReg.h"

// **************************************************************************************
//          CMapRegColorDet Class Define
// **************************************************************************************

CMapRegColorDet::CMapRegColorDet()
{
    m_nTaskID = -1;
    m_oROI    = cv::Rect(-1, -1, -1, -1);
}

CMapRegColorDet::~CMapRegColorDet()
{}

// **************************************************************************************
//          CMapRegColorDet Initialize Define
// **************************************************************************************
int CMapRegColorDet::Initialize(const int nTaskID, tagMapRegParam *pParam)
{
    if (nTaskID < 0)
    {
        LOGE("task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    m_nTaskID = nTaskID;

    tagMapRegParam stParam = *pParam;

    int nState;

    CColorDetParam oColorDetParam;

    // init color threshold of agent
    stParam.strCondition = stParam.strMyLocCondition;
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: MyLoc CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // detect location of agent according to color threshold
    nState = m_oMyLocDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: MyLoc CColorDet initialization failed, please check", m_nTaskID);
        m_oMyLocDet.Release();
        return nState;
    }

    // load RGB threshold for friends
    stParam.strCondition = stParam.strFriendsLocCondition;
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: FriendsLoc CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initial detector for friends
    nState = m_oFriendsLocDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: FriendsLoc CColorDet initialization failed, please check", m_nTaskID);
        m_oFriendsLocDet.Release();
        return nState;
    }

    // initial RGB threshold for detecting view
    stParam.strCondition = stParam.strViewLocCondition;
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: ViewLoc CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // detect location of view
    nState = m_oViewLocDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: ViewLoc CColorDet initialization failed, please check", m_nTaskID);
        m_oViewLocDet.Release();
        return nState;
    }

    m_oROI = stParam.oROI;

    // load image of template
    m_oMapTemp = cv::imread(stParam.strMapTempPath);

    // initial foreground mask.
    m_oMapMask = cv::Mat::ones(m_oMapTemp.size(), CV_8UC1) * 255;
    // cv::imshow("oMapMask", oMapMask);
    // cv::waitKey();
    if (stParam.strMapMaskPath != "")
    {
        cv::Mat oMapMask;
        oMapMask = cv::imread(stParam.strMapMaskPath, 0);
        cv::threshold(oMapMask, m_oMapMask, 100, 255, CV_THRESH_BINARY);
    }

    return 1;
}

// **************************************************************************************
//          CMapRegColorDet Predict Define
// **************************************************************************************

// detect location of the agent, the center of view and view vector
int CMapRegColorDet::Predict(const cv::Mat &oSrcImg, tagMapRegResult &stResult)
{
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    CPixDetData   oPixDetData;
    CPixDetResult oMyLocPixDetResult;
    CPixDetResult oFriendsLocPixDetResult;
    CPixDetResult oViewLocPixDetResult;

    // clone mask and extract roi region
    cv::Mat oSrcImgMask = oSrcImg.clone();
    cv::Mat oSrcImgROI  = oSrcImgMask(m_oROI);

    // resize mask to make it same size with the roi region
    cv::Mat oMapMask;
    cv::resize(m_oMapMask, oMapMask, m_oROI.size());

    cv::Mat oSrcImgROIMask;
    oSrcImgROI.copyTo(oSrcImgROIMask, oMapMask);

    // obtain the image region under foreground mask
    cv::addWeighted(oSrcImgROI, 0, oSrcImgROIMask, 1, 0, oSrcImgROI);

    oPixDetData.m_oSrcImg = oSrcImgMask;
    oPixDetData.m_oROI    = m_oROI;

    // obtain the location of agent
    nState = m_oMyLocDet.Predict(&oPixDetData, &oMyLocPixDetResult);

    if (1 != nState)
    {
        LOGE("task ID %d: MyLoc CColorDet predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        return nState;
    }
    // obtain the location of friends
    nState = m_oFriendsLocDet.Predict(&oPixDetData, &oFriendsLocPixDetResult);

    if (1 != nState)
    {
        LOGE("task ID %d: FreindsLoc CColorDet predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        return nState;
    }

    cv::Mat oMapTemp;

    cv::resize(m_oMapTemp, oMapTemp, m_oROI.size());

    cv::Mat oMapTempMask;
    oMapTemp.copyTo(oMapTempMask, oMapMask);

    cv::Mat oSubImageROIMask;
    cv::subtract(oSrcImgROIMask, oMapTempMask, oSubImageROIMask);


    cv::Mat oSubImgViewMask    = oSrcImgMask.clone();
    cv::Mat oSubImgViewMaskROI = oSubImgViewMask(m_oROI);

    // obtain image region
    cv::addWeighted(oSubImgViewMaskROI, 0, oSubImageROIMask, 1, 0, oSubImgViewMaskROI);


    oPixDetData.m_oSrcImg = oSubImgViewMask;
    oPixDetData.m_oROI    = m_oROI;

    nState = m_oViewLocDet.Predict(&oPixDetData, &oViewLocPixDetResult);

    cv::Mat structureElement = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(3, 3));

    cv::erode(oViewLocPixDetResult.m_oDstImg, oViewLocPixDetResult.m_oDstImg, structureElement);

    // dilate result to get larger region
    structureElement = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(5, 5));
    cv::dilate(oViewLocPixDetResult.m_oDstImg, oViewLocPixDetResult.m_oDstImg, structureElement);


    stResult.oROI = m_oROI;

    if (1 != nState)
    {
        LOGE("task ID %d: ViewLoc CColorDet predict failed, please check", m_nTaskID);
        stResult.nState = 0;
        return nState;
    }

    // detect location of agent
    int             nLocPixelThresh = 2;
    cv::RotatedRect oMyLocRect;
    int             nMyLocState = 0;
    if (oMyLocPixDetResult.m_oVecPoints.empty())
    {
        nMyLocState            = 0;
        stResult.oMyLocPoint.x = -1;
        stResult.oMyLocPoint.y = -1;
    }
    else
    {
        std::vector<std::vector<cv::Point> > oVecContours;
        std::vector<cv::Vec4i>               oVecHierarchies;
        findContours(oMyLocPixDetResult.m_oDstImg, oVecContours,
                     oVecHierarchies, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

        if (oVecContours.empty())
        {
            nMyLocState            = 0;
            stResult.oMyLocPoint.x = -1;
            stResult.oMyLocPoint.y = -1;
        }
        else
        {
            nMyLocState = 1;
            int nMaxSize = 0;

            for (int i = 0; i < static_cast<int>(oVecContours.size()); i++)
            {
                if (static_cast<int>(oVecContours[i].size()) >= nMaxSize && static_cast<int>(oVecContours[i].size()) >= nLocPixelThresh)
                {
                    nMaxSize             = static_cast<int>(oVecContours[i].size());
                    oMyLocRect           = cv::minAreaRect(oVecContours[i]);
                    stResult.oMyLocPoint = oMyLocRect.center;
                }
            }
        }
    }

    // detect location of friends
    cv::RotatedRect oFriendsLocRect;
    int             nFriendsLocState = 0;
    if (oFriendsLocPixDetResult.m_oVecPoints.empty())
    {
        nFriendsLocState          = 0;
        stResult.nFreindsPointNum = 0;
    }
    else
    {
        std::vector<std::vector<cv::Point> > oVecContours;
        std::vector<cv::Vec4i>               oVecHierarchies;
        findContours(oFriendsLocPixDetResult.m_oDstImg, oVecContours,
                     oVecHierarchies, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

        if (oVecContours.empty())
        {
            nFriendsLocState          = 0;
            stResult.nFreindsPointNum = 0;
        }
        else
        {
            nFriendsLocState = 1;
            int nMaxSize = 0;
            stResult.nFreindsPointNum = MIN(MAX_POINT_SIZE, static_cast<int>(oVecContours.size()));

            for (int i = 0; i < stResult.nFreindsPointNum; i++)
            {
                nMaxSize                       = static_cast<int>(oVecContours[i].size());
                oFriendsLocRect                = cv::minAreaRect(oVecContours[i]);
                stResult.szFriendsLocPoints[i] = oFriendsLocRect.center;
            }
        }
    }

    // detect location of view center
    int             nViewPixelThresh = 20;
    cv::RotatedRect oViewLocRect;
    int             nViewLocState = 0;
    if (oViewLocPixDetResult.m_oVecPoints.empty())
    {
        nViewLocState            = 0;
        stResult.oViewLocPoint.x = -1;
        stResult.oViewLocPoint.y = -1;
    }
    else
    {
        std::vector<std::vector<cv::Point> > oVecContours;
        std::vector<cv::Vec4i>               oVecHierarchies;
        findContours(oViewLocPixDetResult.m_oDstImg, oVecContours, oVecHierarchies,
                     cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

        if (oVecContours.empty())
        {
            nViewLocState            = 0;
            stResult.oViewLocPoint.x = -1;
            stResult.oViewLocPoint.y = -1;
        }
        else
        {
            nViewLocState = 1;
            int nMaxSize = 0;

            for (int i = 0; i < static_cast<int>(oVecContours.size()); i++)
            {
                if (static_cast<int>(oVecContours[i].size()) >= nMaxSize && oVecContours[i].size() > nViewPixelThresh)
                {
                    nMaxSize               = static_cast<int>(oVecContours[i].size());
                    oViewLocRect           = cv::minAreaRect(oVecContours[i]);
                    stResult.oViewLocPoint = oViewLocRect.center;
                }
            }
        }
    }

    if (nMyLocState == 1 || nFriendsLocState == 1 || nViewLocState == 1)
    {
        stResult.nState = 1;
    }
    else
    {
        stResult.nState = 0;
    }

    // obtain the view direction based on the location of agent and view center
    if (nMyLocState == 1 && nViewLocState == 1)
    {
        stResult.oViewAnglePoint = stResult.oViewLocPoint - stResult.oMyLocPoint;
    }
    else
    {
        stResult.oViewAnglePoint.x = -1;
        stResult.oViewAnglePoint.y = -1;
    }

    return 1;
}

// **************************************************************************************
//          CMapRegColorDet Release Define
// **************************************************************************************
int CMapRegColorDet::Release()
{
    m_oMyLocDet.Release();
    m_oFriendsLocDet.Release();
    m_oViewLocDet.Release();

    return 1;
}

// **************************************************************************************
//          CMapReg FillColorDetParam Define
// **************************************************************************************
int CMapRegColorDet::FillColorDetParam(const tagMapRegParam &stParam, CColorDetParam &oParam)
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
        LOGE("task ID %d: get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CMapReg Class Define
// **************************************************************************************

CMapReg::CMapReg()
{
    m_oVecParams.clear();
    m_oVecMethods.clear();
}

CMapReg::~CMapReg()
{}

// **************************************************************************************
//          CMapReg Initialize Define
// **************************************************************************************
int CMapReg::Initialize(IRegParam *pParam)
{
    if (NULL == pParam)
    {
        LOGE("IRegParam pointer is NULL, please check");
        return -1;
    }

    CMapRegParam *pP = dynamic_cast<CMapRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CMapRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    m_nTaskID = pP->m_nTaskID;

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: param vector is empty, please check", m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: element number is more than max element size %d", m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    m_oVecParams = pP->m_oVecElements;

    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        CMapRegColorDet oMethod;

        int nState = oMethod.Initialize(m_nTaskID, &m_oVecParams[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CMapRegColorDet initialization failed, please check", m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGI("task ID %d: CMapReg initialization successful", m_nTaskID);
    return 1;
}

// **************************************************************************************
//          CMapReg Predict Define
// **************************************************************************************
int CMapReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CMapRegResult *pR = dynamic_cast<CMapRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CDeformBloodRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagMapRegResult szResults[MAX_ELEMENT_SIZE];

    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CMapRegColorDet predict failed, please check", m_nTaskID);
            return nState;
        }
    }

    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

// **************************************************************************************
//          CMapReg Release Define
// **************************************************************************************
int CMapReg::Release()
{
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CMapRegColorDet release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear();
    m_oVecMethods.clear();

    LOGI("task ID %d: CMapReg release successful", m_nTaskID);
    return 1;
}
