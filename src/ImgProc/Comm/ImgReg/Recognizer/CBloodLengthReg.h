/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CBLOODLENGTHREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CBLOODLENGTHREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorBinMatch.h"
#include "Comm/ImgReg/Recognizer/CPixReg.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          BloodLengthReg Structure Define
// **************************************************************************************

struct tagBloodLengthRegElement {
    int                      nScaleLevel;
    float                    fMinScale;
    float                    fMaxScale;
    float                    fExpandWidth;
    float                    fExpandHeight;
    std::vector<std::string> oVecConditions;
    std::string              oAlgorithm;
    std::vector<tagTmpl>     oVecTmpls;
    cv::Rect                 oROI;
    int                      nMatchCount;

    tagBloodLengthRegElement() {
        nScaleLevel = 1;
        fMinScale = 1.0;
        fMaxScale = 1.0;
        fExpandWidth = 0.10;
        fExpandHeight = 0.10;
        oVecConditions.clear();
        oAlgorithm = "TemplateMatch";
        oVecTmpls.clear();
        nMatchCount = 1;
    }
};

struct tagBloodLengthRegResult {
    int      nState;
    float    fScore;
    float    fScale;
    cv::Rect oROI;

    tagBloodLengthRegResult() {
        nState = 0;
        fScore = -1.0f;
        fScale = -1.0f;
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          BloodLength Recognizer Template Match Class Define
// **************************************************************************************

class CBloodLengthRegTmplMatch {
  public:
    CBloodLengthRegTmplMatch();
    ~CBloodLengthRegTmplMatch();

    int Initialize(const int nTaskID, const tagBloodLengthRegElement &stElement);
    int Predict(const cv::Mat &oSrcImg, tagBloodLengthRegResult &stResult);
    int Release();

  private:
    int            m_nTaskID;
    float          m_fExpandWidth;
    float          m_fExpandHeight;
    cv::Rect       m_oROI;
    CColorBinMatch m_oMethod;
};

// **************************************************************************************
//          BloodLength Recognizer Parameter Class Define
// **************************************************************************************

class CBloodLengthRegParam : public IComnBaseRegParam {
  public:
    CBloodLengthRegParam() {
    }

    virtual ~CBloodLengthRegParam() {}

  public:
    tagBloodLengthRegElement m_oElement;
};

// **************************************************************************************
//          BloodLength Recognizer Result Class Define
// **************************************************************************************

class CBloodLengthRegResult : public IComnBaseRegResult {
  public:
    CBloodLengthRegResult() {
    }

    void SetResult(tagBloodLengthRegResult szResult) {
        m_szResult = szResult;
    }

    tagBloodLengthRegResult GetResult() {
        return m_szResult;
    }
    virtual ~CBloodLengthRegResult() {}

  private:
    tagBloodLengthRegResult m_szResult;
};

// **************************************************************************************
//          CBloodLengthReg Class
// **************************************************************************************

class CBloodLengthReg : public IComnBaseReg {
  public:
    CBloodLengthReg();
    ~CBloodLengthReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    CBloodLengthRegTmplMatch m_oMethod;
    tagBloodLengthRegElement m_oElement;
    int                      m_oMatchCountCurrent = 0;
    tagBloodLengthRegResult  m_szResultTmp;
    tagBloodLengthRegElement m_stElement;

    LockerHandle m_hResultTmpLock;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CBLOODLENGTHREG_H_

