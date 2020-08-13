/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef COMM_UI_CFG_H_
#define COMM_UI_CFG_H_

#include <vector>
#include "Comm/Utils/JsonConfig.h"
#include "Comm/Utils/TSingleton.h"
#include "UI/Src/UITypes.h"

class CCommUICfg
{
public:
    CCommUICfg();
    virtual ~CCommUICfg();

    /*!
     * @brief 初始化
     * @param[in] pszRootPath: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pszCftPath: UI配置所在的相对路径
     * @return true表示成功，false表示失败
     */
    virtual bool Initialize(const char *pszRootPath, const char *pszCftPath, CJsonConfig *pConfig);

    /*!
     * @brief 获取普通UI的配置数据
     * @return UIStateArray
     */
    UIStateArray  GetState();

    /*!
     * @brief 获取开始UI的配置数据
     * @param[in] pConfig: Json配置文件
     * @param[out]] nVecStartID: 开始的UID
     * @return true表示成功，false表示失败
     */
    bool ReadStartState(std::vector<int> *pnVecStartID, CJsonConfig *pConfig);

private:
    /*!
     * @brief 读取普通的配置
     * @param[in] pszRootPath: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pConfig: Json 配置文件
     * @return true表示成功，false表示失败
     */
    bool ReadCfg(const char *pszRootPath, CJsonConfig *pConfig);

    /*!
     * @brief 读取模板的配置
     * @param[in] pConfig: Json 配置文件
     * @param[in] nIndex: UI的索引
     * @param[in] nTemplate: template的数量
     * @param[out] stUIState
     * @return true表示成功，false表示失败
     */
    bool ReadTemplateFromJson(const int nIndex, const int nTemplate, tagUIState *pstUIState, CJsonConfig *pConfig);

    /*!
     * @brief 读取点击项的配置
     * @param[in] pConfig: Json 配置文件
     * @param[in]　nIndex: UI的索引
     * @param[out] pstUIState
     * @return true表示成功，false表示失败
     */
    bool ReadClickItem(const int nIndex, tagUIState *pstUIState, CJsonConfig *pConfig);

    /*!
     * @brief 读取DragCheck项的配置
     * @param[in] pszRootDir:游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pConfig: Json 配置文件
     * @param[in] nIndex: UI的索引
     * @param[out] stUIState
     * @return true表示成功，false表示失败
     */
    bool ReadDragCheckItem(const char *pszRootDir, const int nIndex, tagUIState *pstUIState, CJsonConfig *pConfig);

    /*!
     * @brief 读取Drag项的配置
     * @param[in] pConfig: Json 配置文件
     * @param[in] nIndex: UI的索引
     * @param[out] stUIState
     * @return true表示成功，false表示失败
     */
    bool ReadDragItem(const int nIndex, tagUIState *pstUIState, CJsonConfig *pConfig);

    /*!
     * @brief 读取Script项的配置
     * @param[in] pConfig: Json 配置文件
     * @param[in] nIndex: UI的索引
     * @param[out] stUIState
     * @return true表示成功，false表示失败
     */
    bool ReadScriptItem(const int nIndex, tagUIState *pstUIState, CJsonConfig *pConfig);

    /*!
     * @brief 读取通用项项的配置
     * @param[in] pConfig: Json 配置文件
     * @param[in] pszRootPath: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] nIndex: UI的索引
     * @param[out] stUIState
     * @return true表示成功，false表示失败
     */
    bool ReadCommItem(const char *pszRootPath, const int nIndex, tagUIState *pstUIState, CJsonConfig *pConfig);

private:
    UIStateArray m_oVecState;
    bool         m_bOldCfg;
};

#endif // COMM_UI_CFG_H_
