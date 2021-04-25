/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORDET_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORDET_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/IPixDet.h"

#define PIX_DET_STRIDE 4

// **************************************************************************************
//          CColorDetParam Class Define
// **************************************************************************************

class CColorDetParam : public IPixDetParam {
  public:
    CColorDetParam() {
        m_nFilterSize = 1;
        m_nMaxPointNum = 512;
        m_nRedLower = 0;
        m_nRedUpper = 255;
        m_nGreenLower = 0;
        m_nGreenUpper = 255;
        m_nBlueLower = 0;
        m_nBlueUpper = 255;
    }
    virtual ~CColorDetParam() {}

  public:
    int m_nFilterSize;  // filter size of erode and dilate operation
    int m_nMaxPointNum;  // the number of max points
    int m_nRedLower;  // lower red value
    int m_nRedUpper;  // upper red value
    int m_nGreenLower;  // lower green value
    int m_nGreenUpper;  // upper green value
    int m_nBlueLower;  // lower blue value
    int m_nBlueUpper;  // upper blue value
};

// **************************************************************************************
//          CColorDetFactory Class Define
// **************************************************************************************

class CColorDetFactory : public IPixDetFactory {
  public:
    CColorDetFactory();
    ~CColorDetFactory();

    virtual IImgProc* CreateImgProc();
};

// **************************************************************************************
//          CColorMatch Class Define
// **************************************************************************************

class CColorDet : public IPixDet {
  public:
    CColorDet();
    ~CColorDet();

    // interface
    virtual int Initialize(IImgProcParam *pParam);
    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult);
    virtual int Release();

  private:
    int ParseParam(const CColorDetParam *pParam);
    int Detect(const cv::Mat &oSrcImg, cv::Mat &oDstImg, std::vector<cv::Point> &oVecPoints);
    bool CompareValue(uchar uValue, int nLower, int nUpper);

  private:
    int m_nFilterSize;  // filter size of erode and dilate operation
    int m_nMaxPointNum;  // the number of max points
    int m_nRedLower;  // lower red value
    int m_nRedUpper;  // upper red value
    int m_nGreenLower;  // lower green value
    int m_nGreenUpper;  // upper green value
    int m_nBlueLower;  // lower blue value
    int m_nBlueUpper;  // upper blue value
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_CCOLORDET_H_
