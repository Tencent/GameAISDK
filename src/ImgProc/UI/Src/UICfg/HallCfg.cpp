/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "UI/Src/UICfg/HallCfg.h"

CHallCfg::CHallCfg() {
}


CHallCfg::~CHallCfg() {
}

UIStateArray CHallCfg::GetState() {
    return m_oVecState;
}

void CHallCfg::SetState(const UIStateArray &oVecState) {
    m_oVecState = oVecState;
}

bool CHallCfg::Initialize(const char *pszRootDir, const char *pszCftPath) {
    CJsonConfig *pConfig = new CJsonConfig();
    // 初始化普通UI
    bool bRst = m_oCommCfg.Initialize(pszRootDir, pszCftPath, pConfig);

    // 初始化失败，直接返回
    if (!bRst) {
        LOGE("load hall config failed");
        if (pConfig != NULL) {
            delete pConfig;
            pConfig = NULL;
        }

        return false;
    }

    // 获取所有的普通UI的配置
    m_oVecState = m_oCommCfg.GetState();
    // 获取开始UI的配置
    std::vector<int> nVecStartID;
    bRst = m_oCommCfg.ReadStartState(&nVecStartID, pConfig);
    if (!bRst) {
        LOGI("read start state failed");
        delete pConfig;
        return false;
    }

    // 从普通UI中剔除开始UI，剩下的即为大厅UI
    std::vector<tagUIState>::iterator itr = m_oVecState.begin();

    // 迭代查找普通UI
    while (itr != m_oVecState.end()) {
        int nID = itr->nId;

        std::vector<int>::iterator result = std::find(nVecStartID.begin(), nVecStartID.end(), nID);

        // 在开始UI的ID列表中，找到对应的UI，则此UI为开始UI，剔除。
        if (result != nVecStartID.end()) {
            LOGI("start state is %d", itr->nId);
            itr = m_oVecState.erase(itr);
        } else {
            itr++;
        }
    }

    delete pConfig;
    return true;
}
