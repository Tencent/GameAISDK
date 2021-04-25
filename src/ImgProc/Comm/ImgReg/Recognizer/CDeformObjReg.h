/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CDEFORMOBJREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CDEFORMOBJREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CYOLOAPI.h"
#include "Comm/ImgReg/Recognizer/IObjReg.h"

// **************************************************************************************
//          CDeformObjReg Structure Define
// **************************************************************************************

struct tagDeformObjRegElement {
    int         nMaskValue;
    float       fThreshold;
    cv::Rect    oROI;
    std::string strCfgPath;
    std::string strWeightPath;
    std::string strNamePath;
    std::string strMaskPath;

    tagDeformObjRegElement() {
        nMaskValue = 127;
        fThreshold = 0.50f;
        oROI = cv::Rect(-1, -1, -1, -1);
        strCfgPath = "";
        strWeightPath = "";
        strNamePath = "";
        strMaskPath = "";
    }
};

struct tagDeformObjRegResult {
    int     nState;
    int     nBBoxNum;
    tagBBox szBBoxes[MAX_BBOX_SIZE];

    tagDeformObjRegResult() {
        nState = 0;
        nBBoxNum = 0;
    }
};

// **************************************************************************************
//          CDeformObjRegParam Class Define
// **************************************************************************************

class CDeformObjRegParam : public IObjRegParam {
  public:
    CDeformObjRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CDeformObjRegParam() {}

  public:
    std::vector<tagDeformObjRegElement> m_oVecElements;
};

// **************************************************************************************
//          CDeformObjRegResult Class Define
// **************************************************************************************

class CDeformObjRegResult : public IObjRegResult {
  public:
    CDeformObjRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CDeformObjRegResult() {}

    void SetResult(tagDeformObjRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagDeformObjRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int                   m_nResultNum;
    tagDeformObjRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CDeformObjReg Class Define
// **************************************************************************************

class CDeformObjReg : public IObjReg {
  public:
    CDeformObjReg();
    ~CDeformObjReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    int FillYOLOAPIParam(const tagDeformObjRegElement &stParam, CYOLOAPIParam &oParam);

  private:
    std::vector<tagDeformObjRegElement> m_oVecParams;  // vector of parameters
    std::vector<CYOLOAPI>               m_oVecYOLOAPIs;  // vector of methods
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CDEFORMOBJREG_H_
