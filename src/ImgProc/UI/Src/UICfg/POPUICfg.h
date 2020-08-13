/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef POP_UI_CFG_H_
#define POP_UI_CFG_H_

#include "Comm/Utils/JsonConfig.h"
#include "Comm/Utils/TSingleton.h"
#include "UI/Src/UICfg/UICfg.h"
#include "UI/Src/UITypes.h"


class CPOPUICfg : public TSingleton<CPOPUICfg>, public CUICfg
{
public:
    CPOPUICfg();
    virtual ~CPOPUICfg();

    /*!
     * @brief 初始化
     * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pszCftPath: UI配置所在的相对路径
     * @return true表示成功，false表示失败
     */
    virtual bool Initialize(const char *pszRootPath, const char *pszCftPath);

    /*!
     * @brief 获取游戏弹框UI的配置数据
     * @return UIStateArray
     */
    UIStateArray  GetGameCloseIcons();

    /*!
     * @brief 获取设备弹框UI的配置数据
     * @return UIStateArray
     */
    UIStateArray GetDeviceCloseIcons();

    /*!
     * @brief 获取游戏在局内是否检测弹框的标志
     * @return true表示需要检测，false表示不需要
     */
    bool CheckWhenPlaying();

    /*!
     * @brief 获取检测在局外检测需要间隔的图像帧
     * @return 间隔数量
     */
    int GetUICounterMax();

    /*!
     * @brief 获取在局内检测需要间隔的图像帧
     * @return 间隔数量
     */
    int GetRunCounterMax();

private:

    /*!
     * @brief 读取游戏弹框的配置
     * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pConfig: Json配置文件
     * @return true表示成功，false表示失败
     */
    bool ReadGameCloseIcons(const char *pszRootDir, CJsonConfig *pConfig);
    /*!
     * @brief 读取设备弹框的配置
     * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pConfig: Json配置文件
     * @return true表示成功，false表示失败
     */
    bool ReadDeviceCloseIcons(const char *pszRootDir, CJsonConfig *pConfig);

private:
    bool         m_bCheckCloseWhenPlaying;
    int          m_nCloseIconCounterMax;
    int          m_nCloseIconUICounterMax;
    UIStateArray m_uiCloseIcons;
    UIStateArray m_uiDeviceIcons;
};

#endif // POP_UI_CFG_H_
