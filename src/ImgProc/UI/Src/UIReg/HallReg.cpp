/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/ImgReg/Recognizer/CLocationReg.h"
#include "UI/Src/UICfg/HallCfg.h"
#include "UI/Src/UIReg/HallReg.h"

CHallReg::CHallReg() {
}

CHallReg::~CHallReg() {
}

bool CHallReg::Initialize(CUICfg *pUICfg) {
    // check parameters
    if (NULL == pUICfg) {
        LOGE("input pUIReg is NULL");
        return false;
    }

    // get hall configure
    CHallCfg     *pCfg = dynamic_cast<CHallCfg*>(pUICfg);
    UIStateArray uiArray = pCfg->GetState();
    // initialize with CommUIReg
    return m_oCommUIReg.Initialize(uiArray);
}

int CHallReg::Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst) {
    // check parameters
    if (stFrameCtx.oFrame.empty()) {
        LOGE("hall reg: input frame is empty, please check");
        return -1;
    }

    // return CommUIReg predict result
    return m_oCommUIReg.Predict(stFrameCtx, stUIRegRst);
}
