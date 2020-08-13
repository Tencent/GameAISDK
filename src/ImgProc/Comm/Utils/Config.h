/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef COMMON_CONFIG_H_
#define COMMON_CONFIG_H_

#define MAX_CHAR_LEN 256

// need to add more type
enum ConfigDataType
{
    DATA_INT,
    DATA_UINT,
    DATA_BOOL,
    DATA_STR,
    DATA_FLOAT,
    DATA_DOUBLE,
    DATA_MAX,
};

class CConfig
{
public:
    CConfig()
    {}
    ~CConfig()
    {}
    virtual bool loadFile(const char *pstrConfName)
    {
        return false;
    }

    virtual bool GetConfValue(const char *pData, char *pszRst, int *nLen, const ConfigDataType eDataType)
    {
        return false;
    }
};

#endif // COMMON_CONFIG_H_
