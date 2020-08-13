/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef UI_REG_H_
#define UI_REG_H_

#include "UI/Src/UICfg/UICfg.h"
#include "UI/Src/UITypes.h"


class CUIReg
{
public:
    CUIReg() {};
    ~CUIReg(){};

    /*!
     * @brief 初始化
     * @param[in] pUICfg: 配置项
     * @return true表示成功，false表示失败
     */
    virtual bool Initialize(CUICfg *pUICfg) = 0;

    /*!
     * @brief　检测处理输入图像数据
     * @param[in] stFrameCtx: 输入帧信息
     * @param[out] stUIRegRst:　输出结果
     * @return -1 表示失败，否则返回匹配到的UI的ID
     */
    virtual int Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst) = 0;
};

#endif // UI_REG_H_
