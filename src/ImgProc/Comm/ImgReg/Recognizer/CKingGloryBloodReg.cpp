/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CKingGloryBloodReg.h"

// **************************************************************************************
//          CKingGloryBloodRegColorDet Class Define
// **************************************************************************************

CKingGloryBloodRegColorDet::CKingGloryBloodRegColorDet()
{
    m_nTaskID      = -1; // task id
    m_nBloodLength = 123; // blood length
    m_oROI         = cv::Rect(-1, -1, -1, -1); // detection ROI
}

CKingGloryBloodRegColorDet::~CKingGloryBloodRegColorDet()
{}

int CKingGloryBloodRegColorDet::Initialize(const int nTaskID, tagKingGloryBloodRegParam *pParam)
{
    // check task id
    if (nTaskID < 0)
    {
        LOGE("CKingGloryBloodRegColorDet -- task ID %d is invalid, please check", nTaskID);
        return -1;
    }

    // copy task id
    m_nTaskID = nTaskID;

    // check blood length
    if (pParam->nBloodLength <= 0)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- blood length %d is invalid, please check",
            m_nTaskID, pParam->nBloodLength);
        return -1;
    }

    tagKingGloryBloodRegParam stParam = *pParam;

    int nState;

    // fill yolo parameters
    CYOLOAPIParam oYOLOAPIParam;
    nState = FillYOLOAPIParam(stParam, oYOLOAPIParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- CYOLOAPI fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize yolo
    nState = m_oYOLOAPI.Initialize(oYOLOAPIParam);
    if (1 != nState)
    {
        m_oYOLOAPI.Release();
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- CYOLOAPI initialization failed, please check", m_nTaskID);
        return nState;
    }

    CColorDetParam oColorDetParam;

    // fill red parameters
    stParam.strCondition = "135 < R < 245, 25 < G < 90, 25 < B < 85";
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Red CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize red ColorDet
    nState = m_oRedDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Red CColorDet initialization failed, please check",
            m_nTaskID);
        m_oRedDet.Release();
        return nState;
    }

    // fill green parameters
    stParam.strCondition = "55 < R < 125, 165 < G < 255, 0 < B < 100";
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Green CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize green ColorDet
    nState = m_oGreenDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Green CColorDet initialization failed, please check",
            m_nTaskID);
        m_oGreenDet.Release();
        return nState;
    }

    // fill blue parameters
    stParam.strCondition = "20 < R < 70, 100 < G < 160, 190 < B < 240";
    nState               = FillColorDetParam(stParam, oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Blue CColorDet fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize blue ColorDet
    nState = m_oBlueDet.Initialize(&oColorDetParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- Blue CColorDet initialization failed, please check",
            m_nTaskID);
        m_oBlueDet.Release();
        return nState;
    }

    // fill ColorMatch parameters
    CColorMatchParam oColorMatchParam;
    nState = FillColorMatchParam(stParam, oColorMatchParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- CColorMatch fill param failed, please check", m_nTaskID);
        return nState;
    }

    // initialize ColorMatch
    nState = m_oColorMatch.Initialize(&oColorMatchParam);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- CColorMatch initialization failed, please check", m_nTaskID);
        m_oColorMatch.Release();
        return nState;
    }

    // copy parameters
    m_nBloodLength = stParam.nBloodLength;
    m_oROI         = stParam.oROI;

    return 1;
}

int CKingGloryBloodRegColorDet::Predict(const cv::Mat &oSrcImg, tagKingGloryBloodRegResult &stResult)
{
    // check source image
    if (oSrcImg.empty())
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    int nState;

    // set YOLOAPI input
    CYOLOAPIData   oYOLOAPIData;
    CYOLOAPIResult oYOLOAPIResult;
    oYOLOAPIData.m_oSrcImg = oSrcImg;

    // detect bloods
    nState = m_oYOLOAPI.Predict(oYOLOAPIData, oYOLOAPIResult);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- CYOLOAPI predict failed, please check", m_nTaskID);
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
        return nState;
    }

    std::vector<tagBlood> oVecBloods;
    for (int i = 0; i < static_cast<int>(oYOLOAPIResult.m_oVecBBoxes.size()); i++)
    {
        // set PixDet input
        CPixDetData   oPixDetData;
        CPixDetResult oPixDetResult;
        oPixDetData.m_oSrcImg = oSrcImg;
        oPixDetData.m_oROI    = oYOLOAPIResult.m_oVecBBoxes[i].oRect;

        // detect color in blood
        if (strcmp(oYOLOAPIResult.m_oVecBBoxes[i].szTmplName, "RedBlood") == 0)
        {
            // detect red
            nState = m_oRedDet.Predict(&oPixDetData, &oPixDetResult);
        }
        else if (strcmp(oYOLOAPIResult.m_oVecBBoxes[i].szTmplName, "GreenBlood") == 0)
        {
            // detect green
            nState = m_oGreenDet.Predict(&oPixDetData, &oPixDetResult);
        }
        else if (strcmp(oYOLOAPIResult.m_oVecBBoxes[i].szTmplName, "BlueBlood") == 0)
        {
            // detect blue
            nState = m_oBlueDet.Predict(&oPixDetData, &oPixDetResult);
        }
        else
        {
            LOGE("task ID %d: CKingGloryBloodRegColorDet -- YOLO class name %s is invalid, please check",
                 m_nTaskID, oYOLOAPIResult.m_oVecBBoxes[i].szTmplName);
            continue;
        }

        if (1 != nState)
        {
            LOGE("task ID %d: CKingGloryBloodRegColorDet -- CColorDet predict failed, please check", m_nTaskID);
            stResult.nState    = 0;
            stResult.nBloodNum = 0;
            stResult.oROI      = m_oROI;
            return nState;
        }

        cv::RotatedRect oRect;
        if (oPixDetResult.m_oVecPoints.empty())
        {
            oRect.size.width = 0;
        }
        else
        {
            // find blood contours
            std::vector<std::vector<cv::Point> > oVecContours;
            std::vector<cv::Vec4i>               oVecHierarchies;
            findContours(oPixDetResult.m_oDstImg, oVecContours, oVecHierarchies,
                         cv::RETR_EXTERNAL, cv::CHAIN_APPROX_NONE, cv::Point());

            if (oVecContours.empty())
            {
                oRect.size.width = 0;
            }
            else
            {
                // compute blood rectangles
                int nMaxSize = 0;
                for (int i = 0; i < static_cast<int>(oVecContours.size()); i++)
                {
                    if (static_cast<int>(oVecContours[i].size()) >= nMaxSize)
                    {
                        nMaxSize = static_cast<int>(oVecContours[i].size());
                        oRect    = cv::minAreaRect(oVecContours[i]);
                    }
                }
            }
        }

        // set ObjDet input
        CObjDetData   oObjDetData;
        CObjDetResult oObjDetResult;
        oObjDetData.m_oSrcImg = oSrcImg;

        // expand ROI
        ExpandRect(oYOLOAPIResult.m_oVecBBoxes[i].oRect, 60, 5, oObjDetData.m_oROI);
        oObjDetData.m_oROI.width = oObjDetData.m_oROI.width * 0.3f;

        // detect hero level
        nState = m_oColorMatch.Predict(&oObjDetData, &oObjDetResult);
        if (1 != nState)
        {
            LOGE("task ID %d: CKingGloryBloodRegColorDet -- CColorMatch predict failed, please check", m_nTaskID);
            stResult.nState    = 0;
            stResult.nBloodNum = 0;
            stResult.oROI      = m_oROI;
            return nState;
        }

        // get blood percent and other infomation
        tagBlood stBlood;
        stBlood.nClassID = oYOLOAPIResult.m_oVecBBoxes[i].nClassID;
        stBlood.fPercent = round(((MAX(oRect.size.width, oRect.size.height) / m_nBloodLength) * 100.0) / 20.0) * 20.0;
        stBlood.oRect    = oYOLOAPIResult.m_oVecBBoxes[i].oRect;
        stBlood.fScore   = oYOLOAPIResult.m_oVecBBoxes[i].fScore;
        snprintf(stBlood.szName, sizeof(stBlood.szName), "%s", oYOLOAPIResult.m_oVecBBoxes[i].szTmplName);

        if (oObjDetResult.m_oVecBBoxes.empty())
        {
            stBlood.nLevel = 0;
        }
        else
        {
            stBlood.nLevel = oObjDetResult.m_oVecBBoxes[0].nClassID;
        }

        oVecBloods.push_back(stBlood);
    }

    // set results
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
            LOGI("task ID %d: CKingGloryBloodRegColorDet -- blood number is more than max blood size %d",
                m_nTaskID, MAX_BLOOD_SIZE);
        }
    }

    return 1;
}

int CKingGloryBloodRegColorDet::Release()
{
    // release methods
    m_oYOLOAPI.Release();
    m_oRedDet.Release();
    m_oGreenDet.Release();
    m_oBlueDet.Release();
    m_oColorMatch.Release();

    return 1;
}

int CKingGloryBloodRegColorDet::FillYOLOAPIParam(const tagKingGloryBloodRegParam &stElement, CYOLOAPIParam &oParam)
{
    oParam.m_nTaskID       = m_nTaskID;
    oParam.m_fThreshold    = stElement.fThreshold;
    oParam.m_oROI          = stElement.oROI;
    oParam.m_strCfgPath    = stElement.strCfgPath;
    oParam.m_strWeightPath = stElement.strWeightPath;
    oParam.m_strNamePath   = stElement.strNamePath;
    oParam.m_strMaskPath   = stElement.strMaskPath;

    return 1;
}

int CKingGloryBloodRegColorDet::FillColorDetParam(const tagKingGloryBloodRegParam &stParam, CColorDetParam &oParam)
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
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- get RGB failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CKingGloryBloodRegColorDet::FillColorMatchParam(const tagKingGloryBloodRegParam &stParam, CColorMatchParam &oParam)
{
    oParam.m_nTaskID     = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale   = stParam.fMinScale;
    oParam.m_fMaxScale   = stParam.fMaxScale;
    oParam.m_oROI        = stParam.oROI;
    oParam.m_strOpt      = "-matchMethod SQDIFF_NORMED";

    // analyze tmplate path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState)
    {
        LOGE("task ID %d: CKingGloryBloodRegColorDet -- analyze template path failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

// **************************************************************************************
//          CKingGloryBloodReg Class Define
// **************************************************************************************

CKingGloryBloodReg::CKingGloryBloodReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods
}

CKingGloryBloodReg::~CKingGloryBloodReg()
{}

int CKingGloryBloodReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CKingGloryBloodReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CKingGloryBloodRegParam *pP = dynamic_cast<CKingGloryBloodRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CKingGloryBloodReg -- CKingGloryBloodRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CKingGloryBloodReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CKingGloryBloodReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CKingGloryBloodReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++)
    {
        CKingGloryBloodRegColorDet oMethod;

        int nState = oMethod.Initialize(m_nTaskID, &m_oVecParams[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CKingGloryBloodReg -- CKingGloryBloodRegColorDet initialization failed, please check",
                m_nTaskID);
            oMethod.Release();
            return nState;
        }

        m_oVecMethods.push_back(oMethod);
    }

    LOGI("task ID %d: CKingGloryBloodReg -- CKingGloryBloodReg initialization successful", m_nTaskID);
    return 1;
}

int CKingGloryBloodReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CKingGloryBloodReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CKingGloryBloodReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: CKingGloryBloodReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CKingGloryBloodRegResult *pR = dynamic_cast<CKingGloryBloodRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CKingGloryBloodReg -- CDeformBloodRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagKingGloryBloodRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Predict(stData.oSrcImg, szResults[i]);
        if (1 != nState)
        {
            LOGE("task ID %d: CKingGloryBloodReg -- CKingGloryBloodRegColorDet predict failed, please check",
                m_nTaskID);
            return nState;
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CKingGloryBloodReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecMethods.size()); i++)
    {
        int nState = m_oVecMethods[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CKingGloryBloodReg -- CKingGloryBloodRegColorDet release failed, please check",
                m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecMethods.clear(); // clear vector of methods

    LOGI("task ID %d: CKingGloryBloodReg -- CKingGloryBloodReg release successful", m_nTaskID);
    return 1;
}
