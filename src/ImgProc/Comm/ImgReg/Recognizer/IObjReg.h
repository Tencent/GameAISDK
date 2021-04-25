/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IOBJREG_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IOBJREG_H_

#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          IObjRegParam Class Define
// **************************************************************************************

class IObjRegParam : public IComnBaseRegParam {
  public:
    IObjRegParam() {}
    virtual ~IObjRegParam() {}
};

// **************************************************************************************
//          IObjRegResult Class Define
// **************************************************************************************

class IObjRegResult : public IComnBaseRegResult {
  public:
    IObjRegResult() {}
    virtual ~IObjRegResult() {}
};

// **************************************************************************************
//          IObjReg Class Define
// **************************************************************************************

class IObjReg : public IComnBaseReg {
  public:
    IObjReg() {}
    virtual ~IObjReg() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IOBJREG_H_
