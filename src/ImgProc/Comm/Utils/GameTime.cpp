/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <math.h>
#include <string.h>
#include <time.h>

#include "Comm/Utils/GameTime.h"

 /*!
    @class CGameTime
    @brief 系统时间模块类的实现
  */

CGameTime::CGameTime()
{
    m_nCurMicroSecond = -1;
    m_uiCurMaxID      = 0;
    m_iLastMaxIDSec   = -1;
}

/*!
   @brief 更新当前时间值
   @return 无
 */
void CGameTime::Update()
{
    m_nCurMicroSecond = TqcOsGetMicroSeconds();
}

UINT CGameTime::GetCurMaxID()
{
    UINT uiMaxID = m_uiCurMaxID;

    m_uiCurMaxID++;
    return uiMaxID;
}
