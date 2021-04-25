/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IRECOGNIZER_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IRECOGNIZER_H_

#include "Comm/ImgReg/ImgProcess/ImgComn.h"

// **************************************************************************************
//          IRegParam Class Define
// **************************************************************************************

class IRegParam {
  public:
    IRegParam() {
        m_nTaskID = -1;
    }

    virtual ~IRegParam() {}

  public:
    int m_nTaskID;
};

// **************************************************************************************
//          IRegResult Class Define
// **************************************************************************************

class IRegResult {
  public:
    IRegResult() {
        m_nFrameIdx = -1;
    }

    virtual ~IRegResult() {}

  public:
    int m_nFrameIdx;
};

// **************************************************************************************
//          IRecognizer Class Define
// **************************************************************************************

class IRecognizer {
  public:
    IRecognizer() {
        m_nTaskID = -1;
    }

    virtual ~IRecognizer() {}

    virtual int Initialize(IRegParam *pParam) = 0;

    virtual int Predict(const tagRegData &stData, IRegResult *pResult) = 0;

    virtual int Release() = 0;

  protected:
    int m_nTaskID;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_RECOGNIZER_IRECOGNIZER_H_
