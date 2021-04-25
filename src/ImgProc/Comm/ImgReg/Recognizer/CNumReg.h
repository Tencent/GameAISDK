/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CNUMREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CNUMREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CNumReg Structure Define
// **************************************************************************************

struct tagNumRegElement {
    int                  nScaleLevel;
    float                fMinScale;
    float                fMaxScale;
    std::string          oAlgorithm;
    cv::Rect             oROI;
    std::vector<tagTmpl> oVecTmpls;

    tagNumRegElement() {
        nScaleLevel = 1;
        fMinScale = 1.0;
        fMaxScale = 1.0;
        oROI = cv::Rect(-1, -1, -1, -1);
        oAlgorithm = "TemplateMatch";
        oVecTmpls.clear();
    }
};

struct tagNumRegResult {
    int      nState;
    float    fNum;
    cv::Rect oROI;

    tagNumRegResult() {
        nState = 0;
        fNum = -1.0;
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CNumRegTmplMatch Class Define
// **************************************************************************************

class CNumRegTmplMatch {
  public:
    CNumRegTmplMatch();
    ~CNumRegTmplMatch();

    int Initialize(const int nTaskID, const tagNumRegElement &stElement);
    int Predict(const cv::Mat &oSrcImg, tagNumRegResult &stResult);
    int Release();

  private:
    int         m_nTaskID;
    cv::Rect    m_oROI;
    CColorMatch m_oMatchMethod;
};

// **************************************************************************************
//          CNumRegParam Class Define
// **************************************************************************************

class CNumRegParam : public IComnBaseRegParam {
  public:
    CNumRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CNumRegParam() {}

  public:
    std::vector<tagNumRegElement> m_oVecElements;
};

// **************************************************************************************
//          CNumRegResult Class Define
// **************************************************************************************

class CNumRegResult : public IComnBaseRegResult {
  public:
    CNumRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CNumRegResult() {}

    void SetResult(tagNumRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagNumRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int             m_nResultNum;
    tagNumRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CNumReg Class Define
// **************************************************************************************

class CNumReg : public IComnBaseReg {
  public:
    CNumReg();
    ~CNumReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    std::vector<tagNumRegElement> m_oVecParams;  // vector of parameters
    std::vector<CNumRegTmplMatch> m_oVecMethods;  // vector of methods
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CNUMREG_H_
