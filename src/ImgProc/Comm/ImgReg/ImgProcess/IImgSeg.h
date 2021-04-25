/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGSEG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGSEG_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/IImgProc.h"

// **************************************************************************************
//          IImgSegParam Class Define
// **************************************************************************************

class IImgSegParam : public IImgProcParam {
  public:
    IImgSegParam() {}
    virtual ~IImgSegParam() {}
};

// **************************************************************************************
//          CImgSegData Class Define
// **************************************************************************************

class CImgSegData : public IImgProcData {
  public:
    CImgSegData() {}
    virtual ~CImgSegData() {}
};

// **************************************************************************************
//          CImgSegResult Class Define
// **************************************************************************************

class CImgSegResult : public IImgProcResult {
  public:
    CImgSegResult() {}
    virtual ~CImgSegResult() {}

  public:
    std::vector<cv::Rect> m_oVecRects;
};

// **************************************************************************************
//          IImgSegFactory Class Define
// **************************************************************************************

class IImgSegFactory : public IImgProcFactory {
  public:
    IImgSegFactory() {}
    virtual ~IImgSegFactory() {}

    virtual IImgProc* CreateImgProc() = 0;
};

// **************************************************************************************
//          IImgSeg Class Define
// **************************************************************************************

class IImgSeg : public IImgProc {
  public:
    IImgSeg() {}
    virtual ~IImgSeg() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGSEG_H_
