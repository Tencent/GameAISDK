/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IIMGBASEREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IIMGBASEREG_H_

#include "Comm/ImgReg/Recognizer/IRecognizer.h"

// **************************************************************************************
//          IImgBaseRegParam Class Define
// **************************************************************************************

class IImgBaseRegParam : public IRegParam {
  public:
    IImgBaseRegParam() {}
    virtual ~IImgBaseRegParam() {}
};

// **************************************************************************************
//          IImgBaseRegResult Class Define
// **************************************************************************************

class IImgBaseRegResult : public IRegResult {
  public:
    IImgBaseRegResult() {}
    virtual ~IImgBaseRegResult() {}
};

// **************************************************************************************
//          CImgBaseReg Class
// **************************************************************************************

class CImgBaseReg : public IRecognizer {
  public:
    CImgBaseReg() {}
    virtual ~CImgBaseReg() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IIMGBASEREG_H_
