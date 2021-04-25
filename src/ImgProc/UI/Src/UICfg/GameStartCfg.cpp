/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Os/TqcOs.h"
#include "UI/Src/UICfg/GameStartCfg.h"


CGameStartCfg::CGameStartCfg(/* args */) {
    m_oVecState.clear();
}

CGameStartCfg::~CGameStartCfg() {
}

bool CGameStartCfg::Initialize(const char *pszRootDir, const char *pszCftPath) {
    CJsonConfig *pConfig = new CJsonConfig();
    // 初始化普通UI
    bool bRst = m_oCommCfg.Initialize(pszRootDir, pszCftPath, pConfig);
    // 初始化失败，直接返回
    if (!bRst) {
        LOGE("load game start config failed");
        if (pConfig != NULL) {
            delete pConfig;
            pConfig = NULL;
        }

        return false;
    }
    // 获取所有的普通UI的配置
    UIStateArray oVecState;
    oVecState = m_oCommCfg.GetState();
    // 获取开始UI的配置
    std::vector<int> nVecStartID;
    bRst = m_oCommCfg.ReadStartState(&nVecStartID, pConfig);
    if (!bRst) {
        LOGI("read start state failed");
        delete pConfig;
        return false;
    }
    // 从普通UI中挑出开始UI
    std::vector<tagUIState>::iterator iter;
    // 迭代查找普通UI
    for (iter = oVecState.begin(); iter != oVecState.end(); iter++) {
        int nID = iter->nId;;

        // 在开始UI的ID列表中，找到对应的UI，则此UI为开始UI
        for (size_t i = 0; i < nVecStartID.size(); i++) {
            if (nID == nVecStartID[i]) {
                m_oVecState.push_back(*iter);
                break;
            }
        }
    }

    return true;
}

UIStateArray CGameStartCfg::GetState() {
    return m_oVecState;
}

void CGameStartCfg::SetState(const UIStateArray &oVecState) {
    m_oVecState = oVecState;
}
