/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_UI_UICFG_GAMEOVERCFG_H_
#define GAME_AI_SDK_IMGPROC_UI_UICFG_GAMEOVERCFG_H_

#include "Comm/Utils/JsonConfig.h"
#include "Comm/Utils/TSingleton.h"
#include "UI/Src/UICfg/UICfg.h"
#include "UI/Src/UITypes.h"


class CGameOverCfg : public TSingleton<CGameOverCfg>, public CUICfg {
  public:
    CGameOverCfg();
    virtual ~CGameOverCfg();

    /*!
      * @brief 初始化
      * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
      * @param[in] pszCftPath: UI配置所在的相对路径
      * @return true表示成功，false表示失败
    */
    virtual bool Initialize(const char *pszRootDir, const char *pszCftPath);

    /*!
      * @brief 获取结束UI的配置数据
      * @return UIStateArray
    */
    UIStateArray GetState();

    void SetState(const UIStateArray &oVecStateArr);

    /*!
      * @brief 获取间隔多少帧检测一次结束状态的配置数据
      * @return UIStateArray
    */
    int GetCheckInterval();

  private:
    /*!
      * @brief 读取GameOver的配置
      * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
      * @param[in] pConfig: Json 配置文件
      * @return true表示成功，false表示失败
    */
    bool ReadGameOverCfg(const char *pszRootDir, CJsonConfig *pConfig);

  private:
    UIStateArray m_stateArr;
    int          m_nCheckInterval;
};
#endif  // GAME_AI_SDK_IMGPROC_UI_UICFG_GAMEOVERCFG_H_
