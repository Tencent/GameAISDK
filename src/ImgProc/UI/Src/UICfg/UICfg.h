/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef UI_CFG_H_
#define UI_CFG_H_

class CUICfg
{
public:
    CUICfg() {};
    virtual ~CUICfg() {};

    /*!
     * @brief 初始化
     * @param[in] pszRootDir: 游戏配置(cfg|data)所在的目录绝对路径
     * @param[in] pszCftPath: UI配置所在的相对路径
     * @return true表示成功，false表示失败
     */
    virtual bool Initialize(const char *pszRootPath, const char *pszCftPath) = 0;
};
#endif // UI_CFG_H_
