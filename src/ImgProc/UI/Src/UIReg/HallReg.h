/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef HALL_REG_H_
#define HALL_REG_H_

#include "Comm/Utils/TSingleton.h"
#include "UI/Src/UIReg/CommonUIReg.h"


class CHallReg : public TSingleton<CHallReg>, public CUIReg
{
public:
    CHallReg(/* args */);
    ~CHallReg();

    /*!
     * @brief 初始化
     * @param[in] pUICfg: 配置项
     * @return true表示成功，false表示失败
     */
    virtual bool Initialize(CUICfg *pUIReg);

    /*!
     * @brief　检测处理输入图像数据
     * @param[in] stFrameCtx: 输入帧信息
     * @param[out] stUIRegRst:　输出结果
     * @return -1 表示失败，否则返回匹配到的UI的ID
     */
    virtual int Predict(const tagFrameContext &stFrameCtx, tagUIRegResult &stUIRegRst);

private:
    CCommonUIReg m_oCommUIReg;
};

#endif // HALL_REG_H_
