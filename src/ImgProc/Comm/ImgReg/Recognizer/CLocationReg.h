/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CLOCATIONREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CLOCATIONREG_H_

#include <string>
#include <vector>

#include "Comm/ImgReg/ImgProcess/CColorMatch.h"
#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"
#include "Comm/Utils/GameUtils.h"

// **************************************************************************************
//          CLocationReg Structure Define
// **************************************************************************************

struct tagLocationRegParam {
    int                   nMatchCount;
    int                   nScaleLevel;
    float                 fMinScale;
    float                 fMaxScale;
    float                 fExpandWidth;
    float                 fExpandHeight;
    std::string           strAlgorithm;
    cv::Rect              oLocation;
    cv::Rect              oInferROI;
    std::vector<cv::Rect> oVecInferLocations;
    std::vector<tagTmpl>  oVecTmpls;


    tagLocationRegParam() {
        nMatchCount = 5;
        nScaleLevel = 9;
        fMinScale = 0.80f;
        fMaxScale = 1.20f;
        fExpandWidth = 0.10f;
        fExpandHeight = 0.10f;
        strAlgorithm = "Detect";
        oLocation = cv::Rect(-1, -1, -1, -1);
        oInferROI = cv::Rect(-1, -1, -1, -1);
        oVecInferLocations.clear();
        oVecTmpls.clear();
    }
};

struct tagLocationRegResult {
    int      nState;
    int      nRectNum;
    float    fScale;
    float    fScore;
    cv::Rect szRects[MAX_ELEMENT_SIZE];

    tagLocationRegResult() {
        nState = 0;
        nRectNum = 0;
        fScale = 0.0f;
        fScore = 0.0f;
    }
};

// **************************************************************************************
//          CLocationRegTmplMatch Class Define
// **************************************************************************************

class CLocationRegTmplMatch {
  public:
    CLocationRegTmplMatch();
    ~CLocationRegTmplMatch();

    int Initialize(const int nTaskID, const tagLocationRegParam &stParam);
    int Predict(const cv::Mat &oSrcImg, tagLocationRegResult &stResult);
    int Release();

  private:
    int FillColorMatchParam(const tagLocationRegParam &stParam, CColorMatchParam &oParam);
    int SetPoint(const cv::Rect &oRect, std::vector<cv::Point> &oVecPoints);
    int SetROI(const cv::Rect &oRect, int nImgWidth, int nImgHeight, cv::Rect &oROI);
    int InferROI(const cv::Rect &oRect, float fScale, cv::Rect &oROILoc);
    int InferLocation(const cv::Rect &oROILoc, float fScale, std::vector<cv::Rect> &oVecRects);
    int ComputeOffset(const int nLocIdx, const cv::Rect &oLocation,
        const cv::Rect &oRect, cv::Point &oOffset);

  private:
    int                   m_nTaskID;
    int                   m_nMatchCount;
    float                 m_fExpandWidth;
    float                 m_fExpandHeight;
    std::string           m_strAlgorithm;
    cv::Rect              m_oLocation;
    cv::Rect              m_oInferROI;
    std::vector<cv::Rect> m_oVecInferLocations;

    std::vector<cv::Point> m_oVecLocationPoints;
    std::vector<cv::Point> m_oVecROIPoints;
    std::vector<cv::Rect>  m_oVecDetRects;

    CColorMatch m_oMethod;

    LockerHandle m_hDetRectLock;
};

// **************************************************************************************
//          CLocationRegParam Class Define
// **************************************************************************************

class CLocationRegParam : public IComnBaseRegParam {
  public:
    CLocationRegParam() {}
    virtual ~CLocationRegParam() {}

  public:
    tagLocationRegParam m_stParam;
};

// **************************************************************************************
//          CLocationRegResult Class Define
// **************************************************************************************

class CLocationRegResult : public IComnBaseRegResult {
  public:
    CLocationRegResult() {}
    virtual ~CLocationRegResult() {}

    void SetResult(tagLocationRegResult *pstResult) {
        m_stResult = *pstResult;
    }

    void GetResult(tagLocationRegResult *pstResult) {
        *pstResult = m_stResult;
    }

  private:
    tagLocationRegResult m_stResult;
};

// **************************************************************************************
//          CLocationReg Class Define
// **************************************************************************************

class CLocationReg : public IComnBaseReg {
  public:
    CLocationReg();
    ~CLocationReg();

    // interface
    virtual int Initialize(IRegParam *pParam);
    virtual int Predict(const tagRegData &stData, IRegResult *pResult);
    virtual int Release();

  private:
    tagLocationRegParam   m_stParam;  // parameter
    CLocationRegTmplMatch m_oMethod;  // method
};

// **************************************************************************************
//          Interface for UI
// **************************************************************************************
int DetectPoint(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg,
    const tagActionState &oSrcPoint, cv::Point *pDstPoint);
int DetectRect(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg, const cv::Rect &oSrcRect,
    const float fThreshold, cv::Rect *pDstRect, float *pScore);
int DetectCloseIcon(int nID, const cv::Mat &oSrcImg, const cv::Mat &oTmplImg,
    const cv::Rect &oSrcRect, const float fThreshold, cv::Rect *pDstRect, float *pScore);

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_CLOCATIONREG_H_
