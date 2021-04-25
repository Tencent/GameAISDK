/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CMULTCOLORVARREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CMULTCOLORVARREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

#define DIRECTION_SIZE 12

// **************************************************************************************
//          CMultColorVarReg Structure Define
// **************************************************************************************

struct tagMultColorVarRegElement {
    std::string strImageFilePath;
    std::string szDirectionNames[DIRECTION_SIZE] = { "HurtDown", "HurtDownLeft", "HurtDownRight",
                                                     "HurtUp", "HurtUpLeft", "HurtUpRight",
                                                     "HurtLeft", "HurtLeftDown", "HurtLeftUp",
                                                     "HurtRight", "HurtRightDown", "HurtRightUp" };

    tagMultColorVarRegElement() {
        strImageFilePath = "";
    }
};

struct tagMultColorVarRegResult {
    int   nState;
    float colorMeanVar[DIRECTION_SIZE];

    tagMultColorVarRegResult() {
        nState = 0;
    }
};

// **************************************************************************************
//          CMultColorVarRegCalculate Class Define
// **************************************************************************************

class CMultColorVarRegCalculate {
  public:
    CMultColorVarRegCalculate();
    ~CMultColorVarRegCalculate();

    int Initialize(const int nTaskID, const tagMultColorVarRegElement &stParam);
    int Predict(const cv::Mat &oSrcImg, const int nFrameIdx, tagMultColorVarRegResult &stResult);
    int Release();

  private:
    int      m_nTaskID;
    cv::Rect m_oROI;
    cv::Mat  m_oTmplImg[DIRECTION_SIZE];
    cv::Mat  m_oTmplMask[DIRECTION_SIZE];
    double   m_szColorMean[DIRECTION_SIZE][3];
};

// **************************************************************************************
//          CMultColorVarRegParam Class Define
// **************************************************************************************

class CMultColorVarRegParam : public IComnBaseRegParam {
  public:
    CMultColorVarRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CMultColorVarRegParam() {}

  public:
    std::vector<tagMultColorVarRegElement> m_oVecElements;
};

// **************************************************************************************
//          CMultColorVarRegResult Class Define
// **************************************************************************************

class CMultColorVarRegResult : public IComnBaseRegResult {
  public:
    CMultColorVarRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CMultColorVarRegResult() {}

    void SetResult(tagMultColorVarRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagMultColorVarRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int                      m_nResultNum;
    tagMultColorVarRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CMultColorVarReg Class Define
// **************************************************************************************

class CMultColorVarReg : public IComnBaseReg {
  public:
    CMultColorVarReg();
    ~CMultColorVarReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    std::vector<tagMultColorVarRegElement> m_oVecParams;
    std::vector<CMultColorVarRegCalculate> m_oVecMethods;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CMULTCOLORVARREG_H_

