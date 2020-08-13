/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "UI/Src/GameState/GameOverState.h"
#include "UI/Src/GameState/GameStartState.h"
#include "UI/Src/GameState/HallState.h"
#include "UI/Src/UICfg/GameStartCfg.h"
#include "UI/Src/UICfg/HallCfg.h"
#include "UI/Src/UIReg/GameOverReg.h"
#include "UI/Src/UIReg/GameStartReg.h"
#include "UI/Src/UIReg/HallReg.h"
#include "UI/Src/UIReg/POPUIReg.h"

CGameOverState::CGameOverState()
{}

CGameOverState::~CGameOverState()
{}

void CGameOverState::Handle(const tagFrameContext &stFrameCtx, CContext *pContext)
{
    tagUIRegResult stRst;
    UIStateArray   uiState;
    bool           bRst = false;
    // detect game over UIs
    int nIndex = CGameOverReg::getInstance()->Predict(stFrameCtx, stRst);

    LOGD("over state: match over predict result is %d", nIndex);
    if (nIndex > -1)
    {
        uiState = CGameOverCfg::getInstance()->GetState();
        // send game over state
        CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_OVER);
        // update Uitate
        CGameOverCfg::getInstance()->SetState(uiState);
        return;
    }

    // detect hall UIs
    CUIReg *pReg = CHallReg::getInstance();
    uiState = CHallCfg::getInstance()->GetState();
    enGameState eGameState = GAME_REG_STATE_HALL;
    std::string strState   = "Hall";
    bool        bHall      = true;
    // if no hall configure, next game state is Game Start
    if (uiState.empty())
    {
        pReg       = CGameStartReg::getInstance();
        uiState    = CGameStartCfg::getInstance()->GetState();
        eGameState = GAME_REG_STATE_START;
        strState   = "Game Start";
        bHall      = false;
    }

    nIndex = pReg->Predict(stFrameCtx, stRst);
    LOGD("over state: hall / start predict result is %d", nIndex);
    // if hall detect failed, detect game start
    if (-1 == nIndex && bHall)
    {
        pReg       = CGameStartReg::getInstance();
        uiState    = CGameStartCfg::getInstance()->GetState();
        eGameState = GAME_REG_STATE_START;
        strState   = "Game Start";
        bHall      = false;
        nIndex     = pReg->Predict(stFrameCtx, stRst);
    }

    LOGD("over state: hall / start predict result is %d", nIndex);
    if (nIndex > -1)
    {
        // send "hall" or "game start" action
        bRst = CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, eGameState);
        if (bRst)
        {
            // change state
            // if config of hall is not empty, next state is "Hall State"
            // else next state is "Game Start"
            if (bHall)
            {
                pContext->ChangeState(CHallState::getInstance());
                // update hall config
                CHallCfg::getInstance()->SetState(uiState);
            }
            else
            {
                pContext->ChangeState(CGameStartState::getInstance());
                // update game start config
                CGameStartCfg::getInstance()->SetState(uiState);
            }
            LOGI("change state:  Game Over---->%s", strState.c_str());
        }

        return;
    }

    // detect pop UI,
    int nFrameCount = stFrameCtx.nFrameCount;
    int nInterval   = CPOPUICfg::getInstance()->GetUICounterMax();
    // set nInterval >=0 , valid the mod(%) valid
    nInterval = std::max(1, nInterval);

    // detect pop UI onc interval n images
    if (nFrameCount % nInterval != 0)
    {
        LOGD("GameOver State: frame count is %d, interval is %d, skip frame", nFrameCount, nInterval);
        CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_OVER);
        return;
    }

    // detect pop UI,if matched, result nIndex is the UID of POPUI
    nIndex = CPOPUIReg::getInstance()->Predict(stFrameCtx, stRst);
    LOGD("game over state:detect POPUI, result index is %d", nIndex);
    if (nIndex > -1)
    {
        // not change state
        if (CPOPUIReg::getInstance()->IsGamePOPUI())
        {
            uiState = CPOPUICfg::getInstance()->GetGameCloseIcons();
        }
        else
        {
            uiState = CPOPUICfg::getInstance()->GetDeviceCloseIcons();
        }
        tagUIState stSrcUIState;
        stSrcUIState = uiState.at(nIndex);
        tagActionState stDstActionState;
        stDstActionState.nActionX = stRst.oVecActions.at(0).stClickPt.nActionX;
        stDstActionState.nActionY = stRst.oVecActions.at(0).stClickPt.nActionY;
        CAction::getInstance()->SendAction()->SendClickAction(stFrameCtx, stSrcUIState, stDstActionState);
        uiState[nIndex] = stSrcUIState;
        return;
    }
    // send none action
    CAction::getInstance()->DoAction(stFrameCtx, stRst, uiState, GAME_REG_STATE_OVER);
    return;
}
