/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CDeformObjReg.h"

CDeformObjReg::CDeformObjReg()
{
    m_oVecParams.clear(); // clear vector of parameters
    m_oVecYOLOAPIs.clear(); // clear vector of methods
}

CDeformObjReg::~CDeformObjReg()
{}

int CDeformObjReg::Initialize(IRegParam *pParam)
{
    // check parameters
    if (NULL == pParam)
    {
        LOGE("CDeformObjReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    CDeformObjRegParam *pP = dynamic_cast<CDeformObjRegParam*>(pParam);
    if (NULL == pP)
    {
        LOGE("CDeformObjReg -- CDeformObjRegParam pointer is NULL, please check");
        return -1;
    }

    if (pP->m_nTaskID < 0)
    {
        LOGE("CDeformObjReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    if (pP->m_oVecElements.empty())
    {
        LOGE("task ID %d: CDeformObjReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE)
    {
        LOGE("task ID %d: CDeformObjReg -- element number is more than max element size %d",
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
        CYOLOAPIParam oParam;
        nState = FillYOLOAPIParam(m_oVecParams[i], oParam);
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformObjReg -- CYOLOAPI fill param failed, please check", m_nTaskID);
            return nState;
        }

        // initialize method
        CYOLOAPI oYOLOAPI;
        nState = oYOLOAPI.Initialize(oParam);
        if (1 != nState)
        {
            oYOLOAPI.Release();
            LOGE("task ID %d: CDeformObjReg -- CYOLOAPI initialization failed, please check", m_nTaskID);
            return nState;
        }

        m_oVecYOLOAPIs.push_back(oYOLOAPI);
    }

    LOGD("task ID %d: CDeformObjReg -- CDeformObjReg initialization successful", m_nTaskID);
    return 1;
}

int CDeformObjReg::Predict(const tagRegData &stData, IRegResult *pResult)
{
    // check parameters
    if (stData.nFrameIdx < 0)
    {
        LOGE("task ID %d: CDeformObjReg -- frame index %d is invalid, please check", m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty())
    {
        LOGE("task ID %d: CDeformObjReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult)
    {
        LOGE("task ID %d: CDeformObjReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CDeformObjRegResult *pR = dynamic_cast<CDeformObjRegResult*>(pResult);
    if (NULL == pR)
    {
        LOGE("task ID %d: CDeformObjReg -- CDeformObjRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagDeformObjRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_oVecYOLOAPIs.size()); i++)
    {
        CYOLOAPIData   oData;
        CYOLOAPIResult oResult;
        oData.m_oSrcImg = stData.oSrcImg;

        int nState = m_oVecYOLOAPIs[i].Predict(oData, oResult);
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformObjReg -- CYOLOAPI predict failed, please check", m_nTaskID);
            return nState;
        }

        if (oResult.m_oVecBBoxes.empty())
        {
            szResults[i].nState   = 0;
            szResults[i].nBBoxNum = 0;
        }
        else
        {
            szResults[i].nState   = 1;
            szResults[i].nBBoxNum = MIN(static_cast<int>(oResult.m_oVecBBoxes.size()), MAX_BBOX_SIZE);

            for (int j = 0; j < szResults[i].nBBoxNum; j++)
            {
                if (j < MAX_BBOX_SIZE)
                {
                    szResults[i].szBBoxes[j] = oResult.m_oVecBBoxes[j];
                }
                else
                {
                    LOGD("task ID %d: CDeformObjReg -- bbox number is more than max bbox size %d",
                        m_nTaskID, MAX_BBOX_SIZE);
                }
            }
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_oVecYOLOAPIs.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CDeformObjReg::Release()
{
    // release methods
    for (int i = 0; i < static_cast<int>(m_oVecYOLOAPIs.size()); i++)
    {
        int nState = m_oVecYOLOAPIs[i].Release();
        if (1 != nState)
        {
            LOGE("task ID %d: CDeformObjReg -- CYOLOAPI release failed, please check", m_nTaskID);
            return nState;
        }
    }

    m_oVecParams.clear(); // clear vector of parameters
    m_oVecYOLOAPIs.clear(); // clear vector of methods

    LOGD("task ID %d: CDeformObjReg -- CDeformObjReg release successful", m_nTaskID);
    return 1;
}

int CDeformObjReg::FillYOLOAPIParam(const tagDeformObjRegElement &stElement, CYOLOAPIParam &oParam)
{
    oParam.m_nTaskID       = m_nTaskID;
    oParam.m_nMaskValue    = stElement.nMaskValue;
    oParam.m_fThreshold    = stElement.fThreshold;
    oParam.m_oROI          = stElement.oROI;
    oParam.m_strCfgPath    = stElement.strCfgPath;
    oParam.m_strWeightPath = stElement.strWeightPath;
    oParam.m_strNamePath   = stElement.strNamePath;
    oParam.m_strMaskPath   = stElement.strMaskPath;

    return 1;
}
