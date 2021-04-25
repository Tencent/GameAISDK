/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_GAMESTATE_UISTATE_H_
#define GAME_AI_SDK_IMGPROC_UI_GAMESTATE_UISTATE_H_

#include "UI/Src/Action/Action.h"
class CContext;
class CUIState {
  public:
    CUIState() {}
    virtual ~CUIState() {}
    virtual void Handle(const tagFrameContext &stFrameCtx, CContext *pContext) = 0;
};


// CContext类要维护一个具体state类的实例，这个实例定义当前的状态
class CContext {
  public:
    CContext() {}
    explicit CContext(CUIState *pState) {
        m_pState = pState;
    }
    ~CContext() {}

    /*!
      * @brief 处理每帧图像
      * @param[in] stFrameCtx　当前帧信息
    */
    void Process(const tagFrameContext &stFrameCtx) {
        m_pState->Handle(stFrameCtx, this);
    }

    /*!
      * @brief 改变游戏状态
      * @param[in] stFrameCtx　当前帧信息
    */
    void ChangeState(CUIState *pState) {
        this->m_pState = pState;
    }

  private:
    CUIState *m_pState;
};

#endif  // GAME_AI_SDK_IMGPROC_UI_GAMESTATE_UISTATE_H_
