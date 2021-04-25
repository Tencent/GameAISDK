/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CFixObjReg.h"

CFixObjReg::CFixObjReg() {
    m_oVecParams.clear();  // clear vector of parameters
    m_pVecMethods.clear();  // clear vector of methods
    m_oVecMaxBBoxNum.clear();  // clear vector of max bbox number
}

CFixObjReg::~CFixObjReg() {
}

int CFixObjReg::Initialize(IRegParam *pParam) {
    // check input pointer
    if (NULL == pParam) {
        LOGE("CFixObjReg -- IRegParam pointer is NULL, please check");
        return -1;
    }

    // convert IRegParam pointer to CFixObjRegParam pointer
    CFixObjRegParam *pP = dynamic_cast<CFixObjRegParam*>(pParam);
    if (NULL == pP) {
        LOGE("CFixObjReg -- CFixObjRegParam pointer is NULL, please check");
        return -1;
    }

    // check task ID
    if (pP->m_nTaskID < 0) {
        LOGE("CFixObjReg -- task ID %d is invalid, please check", pP->m_nTaskID);
        return -1;
    }

    // check element size
    if (pP->m_oVecElements.empty()) {
        LOGE("task ID %d: CFixObjReg -- param vector is empty, please check", pP->m_nTaskID);
        return -1;
    }

    // check element size
    if (static_cast<int>(pP->m_oVecElements.size()) > MAX_ELEMENT_SIZE) {
        LOGE("task ID %d: CFixObjReg -- element number is more than max element size %d",
            pP->m_nTaskID, MAX_ELEMENT_SIZE);
        return -1;
    }

    // copy parameters
    m_nTaskID = pP->m_nTaskID;
    m_oVecParams = pP->m_oVecElements;

    // initialize methods
    for (int i = 0; i < static_cast<int>(m_oVecParams.size()); i++) {
        if (m_oVecParams[i].nMaxBBoxNum > MAX_BBOX_SIZE || m_oVecParams[i].nMaxBBoxNum < 1) {
            LOGE("task ID %d: CFixObjReg -- max bbox number %d is invalid, please check",
                m_nTaskID, m_oVecParams[i].nMaxBBoxNum);
            return -1;
        } else {
            m_oVecMaxBBoxNum.push_back(m_oVecParams[i].nMaxBBoxNum);
        }

        // analyze method optional
        AnalyzeCMD(m_oVecParams[i].strAlgorithm, m_oVecParams[i].strMethod, m_oVecParams[i].strOpt);

        if ("ColorMatch" == m_oVecParams[i].strMethod) {
            // initialize color match
            int nState = InitColorMatch(m_oVecParams[i]);
            if (1 != nState) {
                LOGE("task ID %d: CFixObjReg -- CColorMatch initialization failed, please check",
                    m_nTaskID);
                return nState;
            }
        } else if ("GradMatch" == m_oVecParams[i].strMethod) {
            // initialize gradient match
            int nState = InitGradMatch(m_oVecParams[i]);
            if (1 != nState) {
                LOGE("task ID %d: CFixObjReg -- CGradMatch initialization failed, please check",
                    m_nTaskID);
                return nState;
            }
        } else if ("EdgeMatch" == m_oVecParams[i].strMethod) {
            // initialize edge match
            int nState = InitEdgeMatch(m_oVecParams[i]);
            if (1 != nState) {
                LOGE("task ID %d: CFixObjReg -- CEdgeMatch initialization failed, please check",
                    m_nTaskID);
                return nState;
            }
        } else if ("ORBMatch" == m_oVecParams[i].strMethod) {
            // initialize ORB match
            int nState = InitORBMatch(m_oVecParams[i]);
            if (1 != nState) {
                LOGE("task ID %d: CFixObjReg -- CORBMatch initialization failed, please check",
                    m_nTaskID);
                return nState;
            }
        } else {
            // unknown method type
            LOGE("task ID %d: CFixObjReg -- algorithm %s is invalid, please check",
                m_nTaskID, m_oVecParams[i].strAlgorithm.c_str());
            return -1;
        }
    }

    LOGD("task ID %d: CFixObjReg -- CFixObjReg initialization successful", m_nTaskID);
    return 1;
}

int CFixObjReg::Predict(const tagRegData &stData, IRegResult *pResult) {
    // check parameters
    if (stData.nFrameIdx < 0) {
        LOGE("task ID %d: CFixObjReg -- frame index %d is invalid, please check",
            m_nTaskID, stData.nFrameIdx);
        return -1;
    }

    if (stData.oSrcImg.empty()) {
        LOGE("task ID %d: CFixObjReg -- source image is invalid, please check", m_nTaskID);
        return -1;
    }

    if (NULL == pResult) {
        LOGE("task ID %d: CFixObjReg -- IRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    CFixObjRegResult *pR = dynamic_cast<CFixObjRegResult*>(pResult);
    if (NULL == pR) {
        LOGE("task ID %d: CFixObjReg -- CFixObjRegResult pointer is NULL, please check", m_nTaskID);
        return -1;
    }

    tagFixObjRegResult szResults[MAX_ELEMENT_SIZE];

    // run methods
    for (int i = 0; i < static_cast<int>(m_pVecMethods.size()); i++) {
        if (NULL == m_pVecMethods[i]) {
            LOGE("task ID %d: CFixObjReg -- method pointer is NULL, please check", m_nTaskID);
            return -1;
        }

        if ("ColorMatch" == m_oVecParams[i].strMethod ||
            "GradMatch" == m_oVecParams[i].strMethod ||
            "EdgeMatch" == m_oVecParams[i].strMethod ||
            "ORBMatch" == m_oVecParams[i].strMethod) {
            // set input
            CObjDetData   oData;
            CObjDetResult oResult;
            oData.m_oSrcImg = stData.oSrcImg;

            // run method
            int nState = m_pVecMethods[i]->Predict(&oData, &oResult);
            if (1 != nState) {
                LOGE("task ID %d: CFixObjReg -- %s predict failed, please check",
                    m_nTaskID, m_oVecParams[i].strMethod.c_str());
                return nState;
            }

            // get result
            if (oResult.m_oVecBBoxes.empty()) {
                szResults[i].nState = 0;
                szResults[i].nBBoxNum = 0;
                szResults[i].oROI = m_oVecParams[i].oROI;
            } else {
                // szResults[i].nState   = 1;
                // szResults[i].nBBoxNum = 1;
                // szResults[i].oROI     = m_oVecParams[i].oROI;
                // szResults[i].szBBoxes[0] = oResult.m_oVecBBoxes[0];

                szResults[i].nState = 1;
                szResults[i].nBBoxNum = MIN(static_cast<int>(oResult.m_oVecBBoxes.size()),
                    m_oVecMaxBBoxNum[i]);
                szResults[i].oROI = m_oVecParams[i].oROI;

                for (int j = 0; j < szResults[i].nBBoxNum; j++) {
                    if (j < MAX_BBOX_SIZE) {
                        szResults[i].szBBoxes[j] = oResult.m_oVecBBoxes[j];
                        LOGI("task ID %d: CFixObjReg, bbox(%d), x:%d,y:%d,w:%d,h:%d", m_nTaskID, j,
                            oResult.m_oVecBBoxes[j].oRect.x,
                            oResult.m_oVecBBoxes[j].oRect.y,
                            oResult.m_oVecBBoxes[j].oRect.width,
                            oResult.m_oVecBBoxes[j].oRect.height);
                    } else {
                        LOGD("task ID %d: CFixObjReg -- bbox number is more than max bbox size %d",
                            m_nTaskID, MAX_BBOX_SIZE);
                    }
                }
            }
        }
    }

    // set results
    int nResultNum = static_cast<int>(m_pVecMethods.size());
    pR->m_nFrameIdx = stData.nFrameIdx;
    pR->SetResult(szResults, &nResultNum);

    return 1;
}

int CFixObjReg::Release() {
    // release methods
    for (int i = 0; i < static_cast<int>(m_pVecMethods.size()); i++) {
        if (NULL == m_pVecMethods[i]) {
            LOGE("task ID %d: CFixObjReg -- %s pointer is NULL, please check",
                m_nTaskID, m_oVecParams[i].strMethod.c_str());
            continue;  // return -1 or continue
        }

        int nState = m_pVecMethods[i]->Release();
        delete m_pVecMethods[i];
        m_pVecMethods[i] = NULL;

        if (1 != nState) {
            LOGE("task ID %d: CFixObjReg -- %s release failed, please check",
                m_nTaskID, m_oVecParams[i].strMethod.c_str());
            return nState;
        }
    }

    m_oVecParams.clear();  // clear vector of parameters
    m_pVecMethods.clear();  // clear vector of methods
    m_oVecMaxBBoxNum.clear();  // clear vector of max bbox number

    LOGD("task ID %d: CFixObjReg -- CFixObjReg release successful", m_nTaskID);
    return 1;
}

int CFixObjReg::InitColorMatch(const tagFixObjRegElement &stParam) {
    int nState;

    CColorMatchFactory oFactory;
    IImgProc           *pMethod = oFactory.CreateImgProc();

    // fill parameters
    CColorMatchParam oParam;
    nState = FillColorMatchParam(stParam, oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CColorMatch fill param failed, please check", m_nTaskID);
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    // initialize method
    nState = pMethod->Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CColorMatch initialization failed, please check",
            m_nTaskID);
        pMethod->Release();
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    m_pVecMethods.push_back(pMethod);

    return 1;
}

int CFixObjReg::InitGradMatch(const tagFixObjRegElement &stParam) {
    int nState;

    CGradMatchFactory oFactory;
    IImgProc          *pMethod = oFactory.CreateImgProc();

    // fill parameters
    CGradMatchParam oParam;
    nState = FillGradMatchParam(stParam, oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CGradMatch fill param failed, please check", m_nTaskID);
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    // initialize method
    nState = pMethod->Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CGradMatch initialization failed, please check", m_nTaskID);
        pMethod->Release();
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    m_pVecMethods.push_back(pMethod);

    return 1;
}

int CFixObjReg::InitEdgeMatch(const tagFixObjRegElement &stParam) {
    int nState;

    CEdgeMatchFactory oFactory;
    IImgProc          *pMethod = oFactory.CreateImgProc();

    // fill parameters
    CEdgeMatchParam oParam;
    nState = FillEdgeMatchParam(stParam, oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CEdgeMatch fill param failed, please check", m_nTaskID);
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    // initialize method
    nState = pMethod->Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CEdgeMatch initialization failed, please check", m_nTaskID);
        pMethod->Release();
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    m_pVecMethods.push_back(pMethod);

    return 1;
}

int CFixObjReg::InitORBMatch(const tagFixObjRegElement &stParam) {
    int nState;

    CORBMatchFactory oFactory;
    IImgProc         *pMethod = oFactory.CreateImgProc();

    // fill parameters
    CORBMatchParam oParam;
    nState = FillORBMatchParam(stParam, oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CORBMatch fill param failed, please check", m_nTaskID);
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    // initialize method
    nState = pMethod->Initialize(&oParam);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- CORBMatch initialization failed, please check", m_nTaskID);
        pMethod->Release();
        delete pMethod;
        pMethod = NULL;
        return nState;
    }

    m_pVecMethods.push_back(pMethod);

    return 1;
}

int CFixObjReg::FillColorMatchParam(const tagFixObjRegElement &stParam, CColorMatchParam &oParam) {
    // copy parameters
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oROI;
    oParam.m_strOpt = stParam.strOpt;

    // analyze template path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- analyze template path failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CFixObjReg::FillGradMatchParam(const tagFixObjRegElement &stParam, CGradMatchParam &oParam) {
    // copy parameters
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oROI;
    oParam.m_strOpt = stParam.strOpt;

    // analyze template path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- analyze template path failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CFixObjReg::FillEdgeMatchParam(const tagFixObjRegElement &stParam, CEdgeMatchParam &oParam) {
    // copy parameters
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oROI;

    // analyze template path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- analyze template path failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CFixObjReg::FillORBMatchParam(const tagFixObjRegElement &stParam, CORBMatchParam &oParam) {
    // copy parameters
    oParam.m_nTaskID = m_nTaskID;
    oParam.m_nScaleLevel = stParam.nScaleLevel;
    oParam.m_fMinScale = stParam.fMinScale;
    oParam.m_fMaxScale = stParam.fMaxScale;
    oParam.m_oROI = stParam.oROI;

    // analyze template path
    int nState = AnalyzeTmplPath(m_nTaskID, stParam.oVecTmpls, oParam.m_oVecTmpls);
    if (1 != nState) {
        LOGE("task ID %d: CFixObjReg -- analyze template path failed, please check", m_nTaskID);
        return nState;
    }

    return 1;
}

int CFixObjReg::AnalyzeCMD(const std::string &strCMD, std::string &strMethod, std::string &strOpt) {
    if ("" == strCMD) {
        LOGE("task ID %d: CFixObjReg -- algorithm is empty, please check", m_nTaskID);
        return -1;
    }

    strMethod = "";
    strOpt = "";

    // find ColorMatch in commond
    if ((-1 != strCMD.find("ColorMatch"))) {
        strMethod = "ColorMatch";
    }

    // find GradMatch in commond
    if ((-1 != strCMD.find("GradMatch"))) {
        strMethod = "GradMatch";
    }

    // find EdgeMatch in commond
    if ((-1 != strCMD.find("EdgeMatch"))) {
        strMethod = "EdgeMatch";
    }

    // find ORBMatch in commond
    if ((-1 != strCMD.find("ORBMatch"))) {
        strMethod = "ORBMatch";
    }

    // find option in commond
    int nLoc = static_cast<int>(strCMD.find("-"));
    if (-1 != nLoc) {
        strOpt = strCMD.substr(nLoc, strCMD.length() - nLoc);
    }

    return 1;
}
