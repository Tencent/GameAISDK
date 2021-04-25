/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_ICOMNBASEREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_ICOMNBASEREG_H_

#include "Comm/ImgReg/Recognizer/IRecognizer.h"

// **************************************************************************************
//          IComnBaseRegParam Class Define
// **************************************************************************************

class IComnBaseRegParam : public IRegParam {
  public:
    IComnBaseRegParam() {}
    virtual ~IComnBaseRegParam() {}
};

// **************************************************************************************
//          IComnBaseRegResult Class Define
// **************************************************************************************

class IComnBaseRegResult : public IRegResult {
  public:
    IComnBaseRegResult() {}
    virtual ~IComnBaseRegResult() {}
};

// **************************************************************************************
//          IComnBaseReg Class Define
// **************************************************************************************

class IComnBaseReg : public IRecognizer {
  public:
    IComnBaseReg() {}
    virtual ~IComnBaseReg() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_ICOMNBASEREG_H_
