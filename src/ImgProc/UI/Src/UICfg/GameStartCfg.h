/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_UICFG_GAMESTARTCFG_H_
#define GAME_AI_SDK_IMGPROC_UI_UICFG_GAMESTARTCFG_H_

#include "Comm/Utils/TSingleton.h"
#include "UI/Src/UICfg/CommUICfg.h"
#include "UI/Src/UICfg/UICfg.h"

class CGameStartCfg : public TSingleton<CGameStartCfg>, public CUICfg {
  public:
    CGameStartCfg();
    virtual ~CGameStartCfg();
    /*!
      * @brief 初始化
      * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
      * @param[in] pszCftPath: UI配置所在的相对路径
      * @return true表示成功，false表示失败
    */
    virtual bool Initialize(const char *pszRootDir, const char *pszCftPath);

    /*!
      * @brief 获取开始UI的配置数据
      * @return UIStateArray
    */
    UIStateArray GetState();
    void SetState(const  UIStateArray &oVecState);

  private:
    CCommUICfg   m_oCommCfg;
    UIStateArray m_oVecState;
};
#endif  // GAME_AI_SDK_IMGPROC_UI_UICFG_GAMESTARTCFG_H_
