/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CSHOOTGAMEHURTREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CSHOOTGAMEHURTREG_H_

#include <vector>

#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CShootGameHurtReg Structure Define
// **************************************************************************************

struct tagShootGameHurtRegParam {
    float    fThreshold;
    cv::Rect oROI;

    tagShootGameHurtRegParam() {
        fThreshold = 0.75f;
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

struct tagShootGameHurtRegResult {
    int      nState;
    cv::Rect oROI;

    tagShootGameHurtRegResult() {
        nState = 0;
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CShootGameHurtRegMethod Class Define
// **************************************************************************************

class CShootGameHurtRegMethod {
  public:
    CShootGameHurtRegMethod();
    ~CShootGameHurtRegMethod();

    int Initialize(const int nTaskID, const tagShootGameHurtRegParam &stParam);
    int Predict(const cv::Mat &oSrcImg, tagShootGameHurtRegResult &stResult);
    int Release();

  private:
    int      m_nTaskID;
    float    m_fThreshold;
    cv::Rect m_oROI;
};

// **************************************************************************************
//          CShootGameHurtRegParam Class Define
// **************************************************************************************

class CShootGameHurtRegParam : public IComnBaseRegParam {
  public:
    CShootGameHurtRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CShootGameHurtRegParam() {}

  public:
    std::vector<tagShootGameHurtRegParam> m_oVecElements;
};

// **************************************************************************************
//          CShootGameHurtRegResult Class Define
// **************************************************************************************

class CShootGameHurtRegResult : public IComnBaseRegResult {
  public:
    CShootGameHurtRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CShootGameHurtRegResult() {}

    void SetResult(tagShootGameHurtRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagShootGameHurtRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int                       m_nResultNum;
    tagShootGameHurtRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CShootGameHurtReg Class Define
// **************************************************************************************

class CShootGameHurtReg : public IComnBaseReg {
  public:
    CShootGameHurtReg();
    ~CShootGameHurtReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    std::vector<tagShootGameHurtRegParam> m_oVecParams;  // vector of parameters
    std::vector<CShootGameHurtRegMethod>  m_oVecMethods;  // vector of methods
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CSHOOTGAMEHURTREG_H_
