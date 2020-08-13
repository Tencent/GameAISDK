/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "UI/Src/Action/Action.h"
#include "UI/Src/GameState/GameOverState.h"
#include "UI/Src/GameState/GameRunState.h"
#include "UI/Src/GameState/GameStartState.h"
#include "UI/Src/UICfg/GameOverCfg.h"
#include "UI/Src/UICfg/GameStartCfg.h"
#include "UI/Src/UIReg/GameOverReg.h"
#include "UI/Src/UIReg/GameStartReg.h"
#include "UI/Src/UIReg/POPUIReg.h"


CGameStartState::CGameStartState(/* args */)
{}

CGameStartState::~CGameStartState()
{}

void CGameStartState::Handle(const tagFrameContext &stFrameCtx, CContext *pContext)
{
    tagUIRegResult stUIRegRst;
    UIStateArray   uiState;

    // check game start, if matched, result nIndex is the UID of Game Start
    int nIndex = CGameStartReg::getInstance()->Predict(stFrameCtx, stUIRegRst);

    LOGD("start state: game start predict result %d", nIndex);
    if (nIndex > -1)
    {
        // detect game start, not change state
        uiState = CGameStartCfg::getInstance()->GetState();
        // send  action with game start state
        CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiState, GAME_REG_STATE_START);
        CGameStartCfg::getInstance()->SetState(uiState);
        return;
    }

    // check game over, if matched, result nIndex is the UID of Game Start
    nIndex = CGameOverReg::getInstance()->Predict(stFrameCtx, stUIRegRst);
    LOGD("start state: game over predict result %d", nIndex);
    if (nIndex > -1)
    {
        // detect game over, change state from "Game Start"to "Game over"
        uiState = CGameOverCfg::getInstance()->GetState();
        // send action message
        bool bRst = CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiState, GAME_REG_STATE_OVER);
        if (bRst)
        {
            // if send action success, change state
            pContext->ChangeState(CGameOverState::getInstance());
            LOGI("change state:  Game Start---->Game Over");
            CGameOverCfg::getInstance()->SetState(uiState);
        }

        return;
    }
    else
    {
        // if not detect start,  change state from "Game Start"to "Game Run"
        pContext->ChangeState(CGameRunState::getInstance());
        LOGI("change state:  Game Start---->Game Run");
    }

    // send  none action
    CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiState, GAME_REG_STATE_START);
    return;
}
