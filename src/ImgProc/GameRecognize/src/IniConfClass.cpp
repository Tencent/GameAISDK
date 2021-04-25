/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "GameRecognize/src/IniConfClass.h"

CIniConf::CIniConf() {
}

CIniConf::~CIniConf() {
}

int CIniConf::loadFile(const char *pszConfFilename) {
    int nRet = 0;
    // 读取配置文件
    nRet = m_oInitConfig.loadFile(pszConfFilename);

    return nRet;
}

int CIniConf::getPrivateStr(const char *pszSectionName, const char *pszKeyName,
    const char *pszDefaultStr, char *pszRetValue, const int nRetLen) {
    int nRet = 0;
    // 获取键值
    nRet = m_oInitConfig.getPrivateStr(pszSectionName, pszKeyName, pszDefaultStr,
        pszRetValue, nRetLen);

    return nRet;
}

int CIniConf::getPrivateAllKey(const char *pszSectionName, char *pszRetValue, const int nRetLen) {
    int nRet = 0;

    nRet = m_oInitConfig.getPrivateAllKey(pszSectionName, pszRetValue, nRetLen);

    return nRet;
}

int CIniConf::getPrivateInt(const char *pszSectionName, const char *pszKeyName,
    const int nDefaultInt) {
    int nRet = 0;

    nRet = m_oInitConfig.getPrivateInt(pszSectionName, pszKeyName, nDefaultInt);

    return nRet;
}


bool CIniConf::getPrivateBool(const char *pszSectionName, const char *pszKeyName,
    const int nDefaultInt) {
    bool bRet = false;

    bRet = m_oInitConfig.getPrivateBool(pszSectionName, pszKeyName, nDefaultInt);

    return bRet;
}

void CIniConf::closeFile() {
    m_oInitConfig.closeFile();
}
/*!@}*/
