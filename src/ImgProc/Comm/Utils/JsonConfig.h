/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef JSON_CONFIG_H_
#define JSON_CONFIG_H_

#include "Comm/Utils/Config.h"
#include "Comm/Utils/TSingleton.h"
#include "json/json.h"


class CJsonConfig : public CConfig
{
public:
    CJsonConfig()
    {}
    ~CJsonConfig()
    {}
    bool loadFile(const char *pstrConfName);
    bool GetConfValue(const char *pszSrcPath, char *pszDst, int *pnDstLen, const ConfigDataType eDataType);
    bool GetArrayValue(const char *pArrayPath, const int nIndex, const char *pszElement,
                       char *pszRst, int *pnLen, const ConfigDataType eDataType);
    Json::Value  GetJosnValue(const char *pszValuePath);

    int  GetArraySize(const char *pData);

private:
    Json::Value m_root;

private:
    bool GetData(const char *strKey, const Json::Value &JsonRoot, Json::Value *val);
};

#endif // JSON_CONFIG_H_
