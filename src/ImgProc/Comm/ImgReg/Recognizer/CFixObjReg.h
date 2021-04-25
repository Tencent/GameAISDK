/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXOBJREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXOBJREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/ImgReg/ImgProcess/CEdgeMatch.h"
#include "Comm/ImgReg/ImgProcess/CGradMatch.h"
#include "Comm/ImgReg/ImgProcess/CORBMatch.h"
#include "Comm/ImgReg/Recognizer/IObjReg.h"

// **************************************************************************************
//          CFixObjReg Structure Define
// **************************************************************************************

// parameter of each element
struct tagFixObjRegElement {
    int                  nMaxBBoxNum;
    int                  nScaleLevel;
    float                fMinScale;
    float                fMaxScale;
    cv::Rect             oROI;
    std::string          strAlgorithm;
    std::vector<tagTmpl> oVecTmpls;

    std::string strMethod;
    std::string strOpt;

    tagFixObjRegElement() {
        nMaxBBoxNum = 1;
        nScaleLevel = 1;
        fMinScale = 1.0;
        fMaxScale = 1.0;
        oROI = cv::Rect(-1, -1, -1, -1);
        strAlgorithm = "ColorMatch";
        oVecTmpls.clear();

        strMethod = "";
        strOpt = "";
    }
};

// result of each element
struct tagFixObjRegResult {
    int      nState;
    int      nBBoxNum;
    cv::Rect oROI;
    tagBBox  szBBoxes[MAX_BBOX_SIZE];

    tagFixObjRegResult() {
        nState = 0;
        nBBoxNum = 0;
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CFixObjReg Parameter Class Define
// **************************************************************************************

class CFixObjRegParam : public IObjRegParam {
  public:
    CFixObjRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CFixObjRegParam() {}

  public:
    std::vector<tagFixObjRegElement> m_oVecElements;
};

// **************************************************************************************
//          CFixObjReg Result Class Define
// **************************************************************************************

class CFixObjRegResult : public IObjRegResult {
  public:
    CFixObjRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CFixObjRegResult() {}

    void SetResult(tagFixObjRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagFixObjRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int                m_nResultNum;
    tagFixObjRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CFixObjReg Class Define
// **************************************************************************************

class CFixObjReg : public IObjReg {
  public:
    CFixObjReg();
    ~CFixObjReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    int InitColorMatch(const tagFixObjRegElement &stParam);
    int InitGradMatch(const tagFixObjRegElement &stParam);
    int InitEdgeMatch(const tagFixObjRegElement &stParam);
    int InitORBMatch(const tagFixObjRegElement &stParam);
    int FillColorMatchParam(const tagFixObjRegElement &stParam, CColorMatchParam &oParam);
    int FillGradMatchParam(const tagFixObjRegElement &stParam, CGradMatchParam &oParam);
    int FillEdgeMatchParam(const tagFixObjRegElement &stParam, CEdgeMatchParam &oParam);
    int FillORBMatchParam(const tagFixObjRegElement &stParam, CORBMatchParam &oParam);
    int AnalyzeCMD(const std::string &strCMD, std::string &strMethod, std::string &strOpt);

  private:
    std::vector<tagFixObjRegElement> m_oVecParams;  // vector of parameters
    std::vector<IImgProc*>           m_pVecMethods;  // vector of methods
    std::vector<int>                 m_oVecMaxBBoxNum;  // vector of max bbox number
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXOBJREG_H_
