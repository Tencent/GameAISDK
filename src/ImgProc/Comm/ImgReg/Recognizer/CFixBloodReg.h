/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXBLOODREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXBLOODREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorDet.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          CFixBloodReg Structure Define
// **************************************************************************************

struct tagFixBloodRegParam {
    int         nBloodLength;
    int         nFilterSize;
    int         nMaxPointNum;
    std::string strCondition;
    cv::Rect    oROI;

    tagFixBloodRegParam() {
        nBloodLength = 100;
        nMaxPointNum = 512;
        nFilterSize = 1;
        strCondition = "";
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

struct tagFixBloodRegResult {
    int      nState;
    float    fPercent;  // blood percent
    cv::Rect oRect;  // blood rectangle
    cv::Rect oROI;

    tagFixBloodRegResult() {
        nState = 0;
        fPercent = 0.0f;
        oRect = cv::Rect(-1, -1, -1, -1);
        oROI = cv::Rect(-1, -1, -1, -1);
    }
};

// **************************************************************************************
//          CFixBloodRegColorDet Class Define
// **************************************************************************************

class CFixBloodRegColorDet {
  public:
    CFixBloodRegColorDet();
    ~CFixBloodRegColorDet();

    int Initialize(const int nTaskID, const tagFixBloodRegParam &stParam);
    int Predict(const cv::Mat &oSrcImg, tagFixBloodRegResult &stResult);
    int Release();

    int FillColorDetParam(const tagFixBloodRegParam &stParam, CColorDetParam &oParam);

  private:
    int       m_nTaskID;
    int       m_nBloodLength;
    cv::Rect  m_oROI;
    CColorDet m_oMethod;
};

// **************************************************************************************
//          CFixBloodRegParam Class Define
// **************************************************************************************

class CFixBloodRegParam : public IComnBaseRegParam {
  public:
    CFixBloodRegParam() {
        m_oVecElements.clear();
    }

    virtual ~CFixBloodRegParam() {}

  public:
    std::vector<tagFixBloodRegParam> m_oVecElements;
};

// **************************************************************************************
//          CFixBloodRegResult Class Define
// **************************************************************************************

class CFixBloodRegResult : public IComnBaseRegResult {
  public:
    CFixBloodRegResult() {
        m_nResultNum = 0;
    }

    virtual ~CFixBloodRegResult() {}

    void SetResult(tagFixBloodRegResult szResults[], int *pResultNum) {
        m_nResultNum = *pResultNum;

        for (int i = 0; i < *pResultNum; i++) {
            m_szResults[i] = szResults[i];
        }
    }

    tagFixBloodRegResult* GetResult(int *pResultNum) {
        *pResultNum = m_nResultNum;
        return m_szResults;
    }

  private:
    int                  m_nResultNum;
    tagFixBloodRegResult m_szResults[MAX_ELEMENT_SIZE];
};

// **************************************************************************************
//          CFixBloodReg Class Define
// **************************************************************************************

class CFixBloodReg : public IComnBaseReg {
  public:
    CFixBloodReg();
    ~CFixBloodReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    std::vector<tagFixBloodRegParam>  m_oVecParams;   // vector of parameters
    std::vector<CFixBloodRegColorDet> m_oVecMethods;  // vector of methods
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CFIXBLOODREG_H_
