/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IPIXDET_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IPIXDET_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/IImgProc.h"

// **************************************************************************************
//          IPixDetParam Class Define
// **************************************************************************************

class IPixDetParam : public IImgProcParam {
  public:
    IPixDetParam() {}
    virtual ~IPixDetParam() {}
};

// **************************************************************************************
//          CPixDetData Class Define
// **************************************************************************************

class CPixDetData : public IImgProcData {
  public:
    CPixDetData() {}
    virtual ~CPixDetData() {}
};

// **************************************************************************************
//          CPixDetResult Class Define
// **************************************************************************************

class CPixDetResult : public IImgProcResult {
  public:
    CPixDetResult() {}
    virtual ~CPixDetResult() {}

  public:
    cv::Mat m_oDstImg;
    std::vector<cv::Point> m_oVecPoints;
};

// **************************************************************************************
//          IPixDetFactory Class Define
// **************************************************************************************

class IPixDetFactory : public IImgProcFactory {
  public:
    IPixDetFactory() {}
    virtual ~IPixDetFactory() {}

    virtual IImgProc* CreateImgProc() = 0;
};

// **************************************************************************************
//          CPixDet Class Define
// **************************************************************************************

class IPixDet : public IImgProc {
  public:
    IPixDet() {}
    virtual ~IPixDet() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IPIXDET_H_
