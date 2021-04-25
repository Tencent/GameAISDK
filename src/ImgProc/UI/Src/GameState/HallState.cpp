/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "UI/Src/Action/Action.h"
#include "UI/Src/GameState/GameStartState.h"
#include "UI/Src/GameState/HallState.h"
#include "UI/Src/UICfg/GameStartCfg.h"
#include "UI/Src/UICfg/HallCfg.h"
#include "UI/Src/UICfg/POPUICfg.h"
#include "UI/Src/UIReg/GameStartReg.h"
#include "UI/Src/UIReg/HallReg.h"
#include "UI/Src/UIReg/POPUIReg.h"

CHallState::CHallState(/* args */) {
}

CHallState::~CHallState() {
}

void CHallState::Handle(const tagFrameContext &stFrameCtx, CContext *pContext) {
    tagUIRegResult stUIRegRst;
    UIStateArray   uiArray;

    bool bDetectHall = true;
    // detect hall
    CUIReg *pReg = CHallReg::getInstance();

    uiArray = CHallCfg::getInstance()->GetState();
    enGameState eGameState = GAME_REG_STATE_HALL;
    std::string strState = "Hall";
    // if no hall configure, next game state is Game Start
    int nIndex = -1;

    // if hall UI states is not empty, detect hall state first.
    if (!uiArray.empty()) {   // detect hall, if matched, result nIndex is the UID of Hall
        nIndex = pReg->Predict(stFrameCtx, stUIRegRst);
        LOGD("hall state: hall predict result %d", nIndex);
        if (nIndex > -1) {
            // change state
            CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiArray, eGameState);
            CHallCfg::getInstance()->SetState(uiArray);
            return;
        }
    }

    // detect game start
    pReg = CGameStartReg::getInstance();
    uiArray = CGameStartCfg::getInstance()->GetState();

    // detect hall, if matched, result nIndex is the UID of Game Start
    nIndex = pReg->Predict(stFrameCtx, stUIRegRst);
    LOGD("hall state: game start predict result %d", nIndex);
    if (nIndex > -1) {
        bool bRst = CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiArray,
            GAME_REG_STATE_START);
        if (bRst) {
            // if send action success, change state from hall to MatchStart
            pContext->ChangeState(CGameStartState::getInstance());
            LOGI("change state:  Match Hall---->MatchStart");
            CGameStartCfg::getInstance()->SetState(uiArray);
            return;
        }
    }

    // detect pop UI,
    int nFrameCount = stFrameCtx.nFrameCount;
    int nInterval = CPOPUICfg::getInstance()->GetUICounterMax();
    // set nInterval >=0 , valid the mod(%) valid
    nInterval = std::max(1, nInterval);

    // detect pop UI onc interval n images
    if (nFrameCount % nInterval != 0) {
        LOGD("hall state: frame count is %d, interval is %d, skip frame", nFrameCount, nInterval);
        CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiArray, GAME_REG_STATE_HALL);
        return;
    }

    // detect pop UI,if matched, result nIndex is the UID of POPUI
    nIndex = CPOPUIReg::getInstance()->Predict(stFrameCtx, stUIRegRst);
    LOGD("hall state:detect POPUI, result index is %d", nIndex);
    if (nIndex > -1) {
        // not change state
        if (CPOPUIReg::getInstance()->IsGamePOPUI()) {
            uiArray = CPOPUICfg::getInstance()->GetGameCloseIcons();
        } else {
            uiArray = CPOPUICfg::getInstance()->GetDeviceCloseIcons();
        }

        // const tagFrameContext &stFramectx, const tagUIState &stSrcUIState,
        //    tagActionState &stDstActionState
        tagUIState stSrcUIState;
        stSrcUIState = uiArray.at(nIndex);
        tagActionState stDstActionState;
        stDstActionState.nActionX = stUIRegRst.oVecActions.at(0).stClickPt.nActionX;
        stDstActionState.nActionY = stUIRegRst.oVecActions.at(0).stClickPt.nActionY;
        // stDstActionState.fActionThreshold = stUIRegRst.oVecActions.at(0).
        CAction::getInstance()->SendAction()->SendClickAction(stFrameCtx, stSrcUIState,
            stDstActionState);
        uiArray[nIndex] = stSrcUIState;
        return;
    }

    // send none action
    CAction::getInstance()->DoAction(stFrameCtx, stUIRegRst, uiArray, GAME_REG_STATE_HALL);
    return;
}
