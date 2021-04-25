/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_H_

#include "Comm/Utils/GameTime_i.h"

/*!
@class CGameTime
@brief 系统时间模块类
*/

class CGameTime : public IGameTime, public TSingleton<CGameTime> {
  public:
    CGameTime();

    virtual ~CGameTime() {}

    /*!
    @brief 更新当前时间值
    @return 无
    */
    virtual void Update();

    virtual int GetCurMSecond() { return m_nCurMicroSecond / 1000; }

    virtual int GetCurSecond() { return m_nCurMicroSecond / 1000000; }

    virtual UINT GetCurUSecond() { return m_nCurMicroSecond; }

    virtual UINT GetCurMaxID();

  private:
    int m_nCurMicroSecond;

    UINT m_uiCurMaxID;       // 当前秒内的最大ID(主要用于同一秒内的标识)
    int m_iLastMaxIDSec;     // 上次取最大ID时的秒时间
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_GAMETIME_H_

