/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_GAMESTATE_GAMESTARTSTATE_H_
#define GAME_AI_SDK_IMGPROC_UI_GAMESTATE_GAMESTARTSTATE_H_

#include "Comm/Utils/TSingleton.h"
#include "UI/Src/GameState/UIState.h"


class CGameStartState : public TSingleton<CGameStartState>, public CUIState {
  public:
    CGameStartState();
    virtual ~CGameStartState();

    /*!
      * @brief 游戏开始（即将进入局内）状态处理图像帧
      * @param[in] stFrameCtx　当前帧信息
      * @param[in] pContext
    */
    virtual void Handle(const tagFrameContext &stFrameCtx, CContext *pContext);
};

#endif  // GAME_AI_SDK_IMGPROC_UI_GAMESTATE_GAMESTARTSTATE_H_
