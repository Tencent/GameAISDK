/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/ImgReg/Recognizer/CLocationReg.h"
#include "UI/Src/UICfg/GameStartCfg.h"
#include "UI/Src/UIReg/GameStartReg.h"


CGameStartReg::CGameStartReg()
{}

CGameStartReg::~CGameStartReg()
{}
bool CGameStartReg::Initialize(CUICfg *pUICfg)
{
    // check parameters
    if (NULL == pUICfg)
    {
        LOGE("input pUIReg is NULL");
        return false;
    }

    // get start configure
    CGameStartCfg *pCfg   = dynamic_cast<CGameStartCfg*>(pUICfg);
    UIStateArray  uiArray = pCfg->GetState();
    // Initialize with CommUIReg
    return m_oCommUIReg.Initialize(uiArray);
}

int CGameStartReg::Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst)
{
    // check parameters
    if (stFrameCtx.oFrame.empty())
    {
        LOGE("game start reg: input frame is empty, please check");
        return -1;
    }

    UIStateArray uiState = CGameStartCfg::getInstance()->GetState();
    if (0 == uiState.size())
    {
        LOGW("start size is 0");
        return -1;
    }

    // predict with CommUIReg
    return m_oCommUIReg.Predict(stFrameCtx, stUIRegRst);
}
