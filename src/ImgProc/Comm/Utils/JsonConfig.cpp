/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#if defined(__GNUC__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#elif defined(_MSC_VER)
#pragma warning(disable : 4996)
#endif


#include <string.h>
#include <fstream>
#include <iostream>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/JsonConfig.h"
#include "Comm/Utils/TqcLog.h"
#include "Comm/Utils/TqcString.h"


bool CJsonConfig::loadFile(const char *pstrConfName)
{
    if (NULL == pstrConfName)
    {
        LOGE("input config file is null");
        return false;
    }

    Json::Reader reader;

    // read and open file
    std::ifstream in(std::string(pstrConfName), std::ios::binary);

    if (!in.is_open())
    {
        LOGE("Error opening file, format is wrong.");
        return false;
    }

    // if file is exist, parse it by Json rule, and save the result in m_root
    return reader.parse(in, m_root);
}

bool CJsonConfig::GetData(const char *strKey, const Json::Value &JsonRoot, Json::Value *pval)
{
    if (pval == NULL)
    {
        return false;
    }

    *pval = JsonRoot[strKey];
    if (pval->isNull())
    {
        return false;
    }

    return true;
}

int CJsonConfig::GetArraySize(const char *pData)
{
    if (NULL == pData)
    {
        LOGE("input data is null");
        return -1;
    }

    std::vector<std::string> szNameValue;

    // split string by "/" , the previous sub string is the parent of the after string.
    // each sub string is a keyword
    token(pData, "/", &szNameValue);

    int nSize = static_cast<int>(szNameValue.size());
    if (nSize < 1)
    {
        LOGE("input data %s is invalid", pData);
        return -1;
    }

    // get array json value and return the array size
    Json::Value JsonVal;
    Json::Value JsonValRoot;
    bool        bRet = false;
    JsonValRoot = m_root;

    // iteration to obtain value with keywords which get from split source string
    for (int i = 0; i < nSize; i++)
    {
        bRet = GetData(szNameValue[i].c_str(), JsonValRoot, &JsonVal);
        if (!bRet)
        {
            // if one of keywords not exist, return false
            LOGI("get data  %s failed", szNameValue[i].c_str());
            return -1;
        }

        JsonValRoot = JsonVal;
    }

    return JsonVal.size();
}

Json::Value  CJsonConfig::GetJosnValue(const char *pszValuePath)
{
    if (NULL == pszValuePath)
    {
        LOGE("input data is invalid");
        return false;
    }
    std::vector<std::string> szNameValue;

    // split string by "/" , the previous sub string is the parent of the after string.
    // each sub string is a keyword
    token(pszValuePath, "/", &szNameValue);
    int nSize = static_cast<int>(szNameValue.size());
    if (nSize < 1)
    {
        LOGE("input %s is invalid", pszValuePath);
        return false;
    }

    Json::Value JsonVal;
    Json::Value JsonValRoot;
    bool        bRet = false;
    JsonValRoot = m_root;

    // iteration to obtain value with keywords which get from split source string
    for (int i = 0; i < nSize; i++)
    {
        bRet = GetData(szNameValue[i].c_str(), JsonValRoot, &JsonVal);
        if (!bRet)
        {
            // if one of keywords not exist, return false
            LOGI("get data  %s failed", szNameValue[i].c_str());
            return false;
        }

        JsonValRoot = JsonVal;
    }
    return JsonVal;
}


bool CJsonConfig::GetArrayValue(const char *pArrayPath, const int nIndex, const char *psElement,
                                char *pszRst, int *pnLen, const ConfigDataType eDataType)
{
    if (NULL == pArrayPath || NULL == pnLen || NULL == psElement || NULL == pszRst || nIndex < 0 || eDataType > DATA_MAX)
    {
        LOGE("input data is invalid");
        return false;
    }

    std::vector<std::string> szNameValue;

    // split string by "/" , the previous sub string is the parent of the after string.
    // each sub string is a keyword
    token(pArrayPath, "/", &szNameValue);
    int nSize = static_cast<int>(szNameValue.size());
    if (nSize < 1)
    {
        LOGE("input %s is invalid", pArrayPath);
        return false;
    }

    Json::Value JsonVal;
    Json::Value JsonValRoot;
    bool        bRet = false;
    JsonValRoot = m_root;

    // iteration to obtain value with keywords which get from split source string
    for (int i = 0; i < nSize; i++)
    {
        bRet = GetData(szNameValue[i].c_str(), JsonValRoot, &JsonVal);
        if (!bRet)
        {
            // if one of keywords not exist, return false
            LOGI("get data  %s failed", szNameValue[i].c_str());
            return false;
        }

        JsonValRoot = JsonVal;
    }

    // if the index larger than the size of JonValue, the index is invalid
    if (nIndex > static_cast<int>(JsonVal.size()))
    {
        LOGE("input index %d, larger than the max count  %d of array %s", nIndex, JsonVal.size(), pArrayPath);
        return false;
    }

    Json::Value DstValue;

    // if (NULL == psElement)
    // {
    //     DstValue = JsonVal[nIndex];
    // }
    // else
    // {
    if (!JsonVal[nIndex].isMember(psElement))
    {
        // LOGE("%s is not one of %s  %d element ", psElement, pArrayPath, nIndex);
        return false;
    }
    else
    {
        DstValue = JsonVal[nIndex][psElement];
    }
    // }
    // data type may be int, uint, bool, string, float, double,
    // transfer it with JSON API and save the data length
    switch (eDataType)
    {
    case DATA_INT:
    {
        int nData = DstValue.asInt();
        memcpy(pszRst, &nData, sizeof(nData));
        *pnLen = sizeof(nData);
    }
    break;

    case DATA_UINT:
    {
        unsigned int uData = DstValue.asUInt();
        memcpy(pszRst, &uData, sizeof(uData));
        *pnLen = sizeof(uData);
    }
    break;

    case DATA_BOOL:
    {
        bool bData = DstValue.asBool();
        memcpy(pszRst, &bData, sizeof(bData));
        *pnLen = sizeof(bData);
    }
    break;

    case DATA_STR:
    {
        std::string strData = DstValue.asString();
        memcpy(pszRst, strData.c_str(), strData.length());
        *pnLen = strData.length();
    }
    break;

    case DATA_FLOAT:
    {
        float fData = DstValue.asFloat();
        memcpy(pszRst, &fData, sizeof(fData));
        *pnLen = sizeof(fData);
    }
    break;

    case DATA_DOUBLE:
    {
        double dData = DstValue.asDouble();
        memcpy(pszRst, &dData, sizeof(dData));
        *pnLen = sizeof(dData);
    }
    break;

    // if date type is invalid, set pszRst NULL,
    // set length zero or you can add other case process here
    default:
    {
        pszRst = NULL;
        *pnLen   = 0;
    }
    break;
    }

    return true;
}

bool CJsonConfig::GetConfValue(const char *pszSrcPath, char *pszDst, int *pnDstLen, const ConfigDataType eDataType)
{
    if (NULL == pszSrcPath || NULL == pnDstLen || eDataType > DATA_MAX)
    {
        LOGE("input data is is invalid");
        return false;
    }

    std::vector<std::string> szNameValue;

    // split string by "/" , the previous sub string is the parent of the after string.
    // each sub string is a keyword
    token(pszSrcPath, "/", &szNameValue);

    int nSize = static_cast<int>(szNameValue.size());
    if (nSize < 1)
    {
        return false;
    }

    Json::Value JsonVal;
    Json::Value JsonValRoot;
    bool        bRet = false;
    JsonValRoot = m_root;

    // iteration to obtain value with keywords which get from split source string
    for (int i = 0; i < nSize; i++)
    {
        bRet = GetData(szNameValue[i].c_str(), JsonValRoot, &JsonVal);
        if (!bRet)
        {
            // if one of keywords not exist, return false
            LOGI("get data %s failed", szNameValue[i].c_str());
            return false;
        }

        JsonValRoot = JsonVal;
    }

    Json::Value val = JsonVal;

    // data type may be int, uint, bool ,string, float, double,
    // transfer it with JSON API and save the data length
    switch (eDataType)
    {
    case DATA_INT:
    {
        int nData = val.asInt();
        memcpy(pszDst, &nData, sizeof(nData));
        *pnDstLen = sizeof(nData);
    }
    break;

    case DATA_UINT:
    {
        unsigned int uData = val.asUInt();
        memcpy(pszDst, &uData, sizeof(uData));
        *pnDstLen = sizeof(uData);
    }
    break;

    case DATA_BOOL:
    {
        bool bData = val.asBool();
        memcpy(pszDst, &bData, sizeof(bData));
        *pnDstLen = sizeof(bData);
    }
    break;

    case DATA_STR:
    {
        std::string strData = val.asString();
        memcpy(pszDst, strData.c_str(), strData.length());
        *pnDstLen = strData.length();
    }
    break;

    case DATA_FLOAT:
    {
        float fData = val.asFloat();
        memcpy(pszDst, &fData, sizeof(fData));
        *pnDstLen = sizeof(fData);
    }
    break;

    case DATA_DOUBLE:
    {
        double dData = val.asDouble();
        memcpy(pszDst, &dData, sizeof(dData));
        *pnDstLen = sizeof(dData);
    }
    break;
    // if date type is invalid, set pszRst NULL,
    // set length zero or you can add other case process here
    default:
    {
        pszDst  = NULL;
        *pnDstLen = 0;
    }
    break;
    }

    return true;
};
