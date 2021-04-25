/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_I_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_I_H_

#include "Comm/Os/TqcOs.h"

#include "Comm/Utils/TSingleton.h"

typedef struct timeval  TIME_VAL;
typedef unsigned int        UINT;

class IGameTime {
  public:
    virtual ~IGameTime() {}

    virtual int GetCurMSecond() = 0;

    virtual int     GetCurSecond() = 0;

    virtual UINT    GetCurUSecond() = 0;

    virtual UINT    GetCurMaxID() = 0;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_I_H_
