/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Os/TqcOs.h"
#include "UI/Src/GameState/GameOverState.h"
#include "UI/Src/GameState/GameRunState.h"
#include "UI/Src/UICfg/POPUICfg.h"
#include "UI/Src/UIReg/GameOverReg.h"
#include "UI/Src/UIReg/POPUIReg.h"

CGameRunState::CGameRunState() {
}

CGameRunState::~CGameRunState() {
}

void CGameRunState::Handle(const tagFrameContext &stFrameCtx, CContext *pContext) {
    // get "CheckInterval" value from game over config
    int nOverCheckInterval = CGameOverCfg::getInstance()->GetCheckInterval();
    int nFrameCnt = stFrameCtx.nFrameCount;

    // check wether update frame count
    if (0 == nFrameCnt) {
        LOGE("run state: not update frame count, please check");
        return;
    }

    // detect "game over"  per nInterval frame
    nOverCheckInterval = std::max(nOverCheckInterval, 1);
    if (nFrameCnt % nOverCheckInterval != 0) {
        LOGD("match run state: framecnt %d, over check interval is %d, skip frame",
            nFrameCnt, nOverCheckInterval);
        return;
    }

    tagUIRegResult stRst;
    UIStateArray   uiState;

    // detect game over
    int nIndex = CGameOverReg::getInstance()->Predict(stFrameCtx, stRst);
    LOGD("run state: match over predict result is %d", nIndex);
    if (nIndex > -1) {
        // change state from "Game Run" to "Game Over"
        uiState = CGameOverCfg::getInstance()->GetState();
        // send game over action
        bool bRst = CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState,
            GAME_REG_STATE_OVER);
        if (bRst) {
            pContext->ChangeState(CGameOverState::getInstance());
            LOGI("change state:  Game Run---->Game Over");
            // update uiState
            CGameOverCfg::getInstance()->SetState(uiState);
        }

        return;
    }

    // if check playing when playing
    bool bCheck = CPOPUICfg::getInstance()->CheckWhenPlaying();
    if (!bCheck) {
        LOGD("run state: no check pop UI when playing, send none action");
        // send none action
        CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_RUN);
        return;
    }

    int nPOPCheckInterval = CPOPUICfg::getInstance()->GetRunCounterMax();
    // set nInterval >=0 , valid the mod(%) valid
    nPOPCheckInterval = std::max(1, nPOPCheckInterval);

    // detect "POP UI" once per nPOPCheckInterval frame
    if (nFrameCnt % nPOPCheckInterval != 0) {
        // send none action
        LOGD("run state: frame count is %d, interval is %d, skip frame",
            nFrameCnt, nPOPCheckInterval);
        CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_RUN);
        return;
    }

    nIndex = CPOPUIReg::getInstance()->Predict(stFrameCtx, stRst);
    LOGD("run state:detect POPUI, result index is %d", nIndex);
    if (nIndex > -1) {
        // uiState from GamePOPUI or DevPOPUI
        if (CPOPUIReg::getInstance()->IsGamePOPUI()) {
            uiState = CPOPUICfg::getInstance()->GetGameCloseIcons();
        } else {
            uiState = CPOPUICfg::getInstance()->GetDeviceCloseIcons();
        }

        // send pop ui action
        tagUIState stPOPUIState;
        stPOPUIState = uiState.at(nIndex);
        tagActionState stPOPUIActionState;
        stPOPUIActionState.nActionX = stRst.oVecActions.at(0).stClickPt.nActionX;
        stPOPUIActionState.nActionY = stRst.oVecActions.at(0).stClickPt.nActionY;
        // stDstActionState.fActionThreshold = stUIRegRst.oVecActions.at(0).
        CAction::getInstance()->SendAction()->SendClickAction(stFrameCtx,
            stPOPUIState, stPOPUIActionState);
        return;
    }

    // send none action
    CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_RUN);
    return;
}
