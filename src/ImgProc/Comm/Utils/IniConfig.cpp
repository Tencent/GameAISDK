/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <stdlib.h>
#include <string.h>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/IniConfig.h"
#include "Comm/Utils/TqcCommon.h"


CIniConfig::CIniConfig()
{}

CIniConfig::~CIniConfig()
{}

int CIniConfig::loadFile(const char *pszConfFileName)
{
    int iRet = 0;

    if (NULL == pszConfFileName)
    {
        iRet = -1;         // 配置文件名为NULL
    }
    else
    {
        m_ifStream.open(pszConfFileName, std::ios::in);
        if (m_ifStream.is_open())        // open success
        {
            m_strConfFileName.assign(pszConfFileName);
        }
        else         // open fail
        {
            iRet = -2;
        }
    }

    return iRet;
}

void CIniConfig::closeFile()
{
    if (m_ifStream.is_open())    // 文件已打开
    {
        m_ifStream.close();
    }
}

int CIniConfig::getPrivateStr(const char *pszSectionName, const char *pszKeyName,
                              const char *pszDefaultStr, char *pszRetValue, const int nRetLen)
{
    int iRet = 0;

    iRet = getPrivateProfileString(pszSectionName, pszKeyName, pszDefaultStr, pszRetValue, nRetLen);

    return iRet;
}

int CIniConfig::getPrivateAllSection(char *pszRetValue, const int nRetLen)
{
    int iRet = 0;

    iRet = getPrivateProfileString(NULL, NULL, NULL, pszRetValue, nRetLen);

    return iRet;
}

int CIniConfig::getPrivateAllKey(const char *pszSectionName, char *pszRetValue, const int nRetLen)
{
    int iRet = 0;

    iRet = getPrivateProfileString(pszSectionName, NULL, NULL, pszRetValue, nRetLen);

    return iRet;
}

int CIniConfig::getPrivateInt(const char *pszSectionName, const char *pszKeyName, const int nDefaultInt)
{
    int iRet = 0;

    const int TMP_BUFFER_LEN = 64;
    char      szDefaultVal[TMP_BUFFER_LEN], szReturnVal[TMP_BUFFER_LEN];

    SNPRINTF(szDefaultVal, sizeof(szDefaultVal), "%d", nDefaultInt);
    getPrivateProfileString(pszSectionName, pszKeyName, szDefaultVal, szReturnVal, TMP_BUFFER_LEN);

    iRet = atoi(szReturnVal);

    return iRet;
}

bool CIniConfig::getPrivateBool(const char *pszSectionName, const char *pszKeyName, const int nDefaultInt)
{
    bool bRet = true;

    const int TMP_BUFFER_LEN = 64;
    char      szDefaultVal[TMP_BUFFER_LEN], szReturnVal[TMP_BUFFER_LEN];

    if (nDefaultInt)
    {
        SNPRINTF(szDefaultVal, sizeof(szDefaultVal), "%s", "TRUE");
    }
    else
    {
        SNPRINTF(szDefaultVal, sizeof(szDefaultVal), "%s", "FALSE");
    }

    getPrivateProfileString(pszSectionName, pszKeyName, szDefaultVal, szReturnVal, TMP_BUFFER_LEN);

    if (StrCaseIgnoreCmp(szReturnVal, "TRUE"))
    {
        bRet = false;
    }
    else
    {
        bRet = true;
    }

    return bRet;
}

int PostProcess(const char *pszDefaultStr, char *pszRetValue, const int nRetLen, char *pstrtmp, int ntmp)
{
    if (*pszRetValue != '\0')
    {
        *pstrtmp = '\0';
        return nRetLen - ntmp - 2;
    }
    else
    {
        // 返回默认值
        if (pszDefaultStr == NULL)
        {
            pszRetValue[0] = '\0';
            return 0;
        }
        else
        {
            strncpy(pszRetValue, pszDefaultStr, nRetLen - 2);
            *(pszRetValue + strlen(pszRetValue))     = '\0';
            *(pszRetValue + strlen(pszRetValue) + 1) = '\0';
            return static_cast<int>(strlen(pszRetValue));
        }
    }
}

int GetOperateNum(const char *pszSectionName, const char *pszKeyName)
{
    int operate = 0;

    // 如果App和Key全部为空，则返回所有的Section，用'\0'分隔，最后一个用两个'\0'标识
    if (pszSectionName == NULL && pszKeyName == NULL)
    {
        operate = 1;
    }

    // 如果Key为空，App不空，则返回所有的Section下的Key值，用'\0'分隔，最后一个用两个'\0'标识
    if (pszSectionName != NULL && pszKeyName == NULL)
    {
        operate = 2;
    }

    // App为空，Key不为空,则检查所有的Key，将第一个匹配的键值返回
    if (pszSectionName == NULL && pszKeyName != NULL)
    {
        operate = 3;
    }

    // App，Key部不为空，这返回App，Key都匹配的键值
    if (pszSectionName != NULL && pszKeyName != NULL)
    {
        operate = 4;
    }

    return operate;
}

// 处理App和Key全部为空的情况
int CIniConfig::ProcessOperateOne(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
                                  char *pstrtmp, int ntmp, char  *pszOneLine, const int nBufLen)
{
    while (m_ifStream)
    {
        m_ifStream.getline(pszOneLine, nBufLen);
        StrTrim(pszOneLine);

        // 注释行
        if (pszOneLine[0] == ';' || pszOneLine[0] == '#')
        {
            continue;
        }

        if (pszOneLine[0] == '[' && pszOneLine[strlen(pszOneLine) - 1] == ']')
        {
            // 去掉'[',']'
            memmove(pszOneLine, pszOneLine + 1, strlen(pszOneLine) - 1);
            pszOneLine[strlen(pszOneLine) - 2] = '\0';

            strncpy(pstrtmp, pszOneLine, ntmp - 1);
            *(pstrtmp + ntmp - 1) = '\0';

            ntmp = ntmp - static_cast<int>(strlen(pstrtmp)) - 1;

            // 同时考虑结束字符用两个'\0'
            if (ntmp > 1)
            {
                // 跳到下一个写的地方、长度包括一个'\0',
                pstrtmp += strlen(pstrtmp) + 1;
            }
            //
            else
            {
                *(pstrtmp + strlen(pstrtmp)) = '\0';
                // 结束的字符要用双'\0'
                *(pszRetValue + strlen(pstrtmp) + 1) = '\0';
                return nRetLen - ntmp - 2;
            }
        }
    }

    // 后处理
    return PostProcess(pszDefaultStr, pszRetValue, nRetLen, pstrtmp, ntmp);
}

// 如果Key为空，App不空的情况
int CIniConfig::ProcessOperateTwo(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
                                  char *pstrtmp, int ntmp, char  *pszOneLine, const int nBufLen, bool bApp, const char *pszSectionName)
{
    while (m_ifStream)
    {
        m_ifStream.getline(pszOneLine, nBufLen);
        // 整理，
        StrTrim(pszOneLine);

        // 注释行
        if (pszOneLine[0] == ';' || pszOneLine[0] == '#')
        {
            continue;
        }

        // 找匹配的Section
        if (pszOneLine[0] == '[' && pszOneLine[strlen(pszOneLine) - 1] == ']')
        {
            // 已经找到下一个Section,没有发现相关的Key，返回查询的所有Key值
            if (bApp == true)
            {
                *pstrtmp = '\0';
                return nRetLen - ntmp - 2;
            }

            // 去掉'[',']'
            memmove(pszOneLine, pszOneLine + 1, strlen(pszOneLine) - 1);
            pszOneLine[strlen(pszOneLine) - 2] = '\0';
            // 整理，
            StrTrim(pszOneLine);

            if (StrCaseIgnoreCmp(pszOneLine, pszSectionName) == 0)
            {
                bApp    = true;
                pstrtmp = pszRetValue;
                ntmp    = nRetLen - 1;
                continue;
            }
        }

        // 找key
        if (bApp == true)
        {
            char *str = strstr(pszOneLine, "=");

            if (str != NULL)
            {
                strncpy(pstrtmp, pszOneLine, ntmp - 1);
                // 添加结束符
                *(pstrtmp + strlen(pstrtmp)) = '\0';
                // 长度包括一个'\0'，
                ntmp = ntmp - static_cast<int>(strlen(pstrtmp)) - 1;

                // 同时考虑结束字符用两个'\0'
                if (ntmp > 1)
                {
                    // 跳到下一个写的地方、长度包括一个'\0',
                    pstrtmp += strlen(pstrtmp) + 1;
                }
                //
                else
                {
                    *(pstrtmp + strlen(pstrtmp)) = '\0';
                    // 结束的字符要用双'\0'
                    *(pszRetValue + strlen(pstrtmp) + 1) = '\0';
                    return nRetLen - ntmp - 2;
                }
            }
        }
    }

    // 后处理
    return PostProcess(pszDefaultStr, pszRetValue, nRetLen, pstrtmp, ntmp);
}

// 处理App为空，Key不为空的情况
int CIniConfig::ProcessOperateThree(const char *pszDefaultStr, char *pszRetValue, const int nRetLen,
                                    char *pstrtmp, int ntmp, char  *pszOneLine, const int nBufLen)
{
    char *pszKey    = new char[nBufLen];
    char *pszString = new char[nBufLen];
    if (NULL == pszKey || NULL == pszString)
    {
        return 0;
    }

    memset(pszKey, 0, nBufLen);
    memset(pszKey, 0, nBufLen);

    while (m_ifStream)
    {
        m_ifStream.getline(pszOneLine, nBufLen);
        // 整理
        StrTrim(pszOneLine);

        // 注释行
        if (pszOneLine[0] == ';' || pszOneLine[0] == '#')
        {
            continue;
        }

        char *str = strstr(pszOneLine, "=");

        if (str != NULL)
        {
            char *snext = str + 1;
            *str = '\0';
            strncpy(pszKey, pszOneLine, nBufLen);
            strncpy(pszString, snext, nBufLen);

            // 找到返回。
            if (StrCaseIgnoreCmp(pszKey, pszOneLine) == 0)
            {
                strncpy(pszRetValue, pszString, nRetLen - 1);
                *(pszRetValue + nRetLen - 1) = '\0';
                delete[]pszKey;
                delete[]pszString;
                return static_cast<int>(strlen(pszRetValue));
            }
        }
    }

    delete[]pszKey;
    delete[]pszString;

    // 返回默认值
    if (pszDefaultStr == NULL)
    {
        *pszRetValue = '\0';
        return 0;
    }
    else
    {
        strncpy(pszRetValue, pszDefaultStr, nRetLen - 1);
        *(pszRetValue + nRetLen - 1) = '\0';
        return static_cast<int>(strlen(pszRetValue));
    }
}

// 处理App，Key都不为空的情况
int CIniConfig::ProcessOperateFour(const char *pszSectionName, const char *pszKeyName, const char *pszDefaultStr,
                                   char *pszRetValue, const int nRetLen, char *pstrtmp, int ntmp, char  *pszOneLine, const int nBufLen)
{
    char *pszKey    = new char[nBufLen];
    char *pszString = new char[nBufLen];

    if (NULL == pszKey || NULL == pszString)
    {
        return 0;
    }

    memset(pszKey, 0, nBufLen);
    memset(pszString, 0, nBufLen);
    bool bApp = false;

    while (m_ifStream)
    {
        m_ifStream.getline(pszOneLine, nBufLen);
        // 整理
        StrTrim(pszOneLine);

        // 注释行
        if (pszOneLine[0] == ';' || pszOneLine[0] == '#')
        {
            continue;
        }

        if (pszOneLine[0] == '[' && pszOneLine[strlen(pszOneLine) - 1] == ']')
        {
            // 已经找到下一个Section,没有发现相关的Key，返回默认值
            if (bApp == true)
            {
                // 返回默认值
                if (pszDefaultStr == NULL)
                {
                    *pszRetValue = '\0';
                    delete[]pszKey;
                    delete[]pszString;
                    return 0;
                }
                else
                {
                    strncpy(pszRetValue, pszDefaultStr, nRetLen - 1);
                    *(pszRetValue + nRetLen - 1) = '\0';
                    delete[]pszKey;
                    delete[]pszString;
                    return static_cast<int>(strlen(pszRetValue));
                }
            }

            // 去掉'[',']'
            memmove(pszOneLine, pszOneLine + 1, strlen(pszOneLine) - 1);
            pszOneLine[strlen(pszOneLine) - 2] = '\0';
            //
            StrTrim(pszOneLine);

            //
            if (StrCaseIgnoreCmp(pszOneLine, pszSectionName) == 0)
            {
                bApp = true;
                continue;
            }
        }

        if (bApp == true)
        {
            char *str = strstr(pszOneLine, "=");

            if (str != NULL)
            {
                char *snext = str + 1;
                *str = '\0';
                strncpy(pszKey, pszOneLine, nBufLen);
                strncpy(pszString, snext, nBufLen);
                StrTrim(pszKey);
                StrTrim(pszString);

                // 找到返回。
                if (StrCaseIgnoreCmp(pszKey, pszKeyName) == 0)
                {
                    strncpy(pszRetValue, pszString, nRetLen - 1);
                    *(pszRetValue + nRetLen - 1) = '\0';
                    delete[]pszKey;
                    delete[]pszString;
                    return static_cast<int>(strlen(pszRetValue));
                }
            }
        }
    }

    delete[]pszKey;
    delete[]pszString;
    //
    if (pszDefaultStr == NULL)
    {
        *pszRetValue = '\0';
        return 0;
    }
    else
    {
        strncpy(pszRetValue, pszDefaultStr, nRetLen - 1);
        *(pszRetValue + nRetLen - 1) = '\0';
        return static_cast<int>(strlen(pszRetValue));
    }
}
int CIniConfig::getPrivateProfileString(const char *pszSectionName, const char *pszKeyName,
                                        const char *pszDefaultStr, char *pszRetValue, const int nRetLen)
{
    int iRet = 0;

    if (NULL == pszRetValue || nRetLen < 1)
    {
        iRet = -1;
        return iRet;
    }

    int operate = GetOperateNum(pszSectionName, pszKeyName);     // 操作方式
    // 文件指针定位到文件起始位置
    m_ifStream.seekg(0, std::ios::beg);

    // 8*1024,1行的最大值
    const int LINE_BUFFER_LEN = 8192;
    char      szOneLine[LINE_BUFFER_LEN + 1], szKey[LINE_BUFFER_LEN + 1], szString[LINE_BUFFER_LEN + 1];
    szOneLine[LINE_BUFFER_LEN] = '\0';
    szKey[LINE_BUFFER_LEN]     = '\0';
    szString[LINE_BUFFER_LEN]  = '\0';

    char *pstrtmp = NULL;
    int  ntmp;
    bool bApp;
    if (operate == 1 || operate == 2)
    {
        // 如果返回字符串长度小于2,全部返回空字符
        if (nRetLen <= 2)
        {
            *pszRetValue       = '\0';
            *(pszRetValue + 1) = '\0';
            return nRetLen;
        }

        bApp    = false;
        pstrtmp = pszRetValue;
        ntmp    = nRetLen - 1;
    }

    // 如果App和Key全部为空，则返回所有的Section，用'\0'分隔，最后一个用两个'\0'标识
    if (operate == 1)
    {
        // 如果返回字符串长度小于2,全部返回空字符
        return ProcessOperateOne(pszDefaultStr, pszRetValue, nRetLen, pstrtmp, ntmp, szOneLine, LINE_BUFFER_LEN);
    }

    // 如果Key为空，App不空，则返回所有的Section下的Key值，用'\0'分隔，最后一个用两个'\0'标识
    if (operate == 2)
    {
        // 如果返回字符串长度小于2,全部返回空字符
        return ProcessOperateTwo(pszDefaultStr, pszRetValue, nRetLen, pstrtmp, ntmp, szOneLine,
                                 LINE_BUFFER_LEN, bApp, pszSectionName);
    }

    // App为空，Key不为空,则检查所有的Key，将第一个匹配的键值返回
    if (operate == 3)
    {
        return ProcessOperateThree(pszDefaultStr, pszRetValue, nRetLen,
                                   pstrtmp, ntmp, szOneLine, LINE_BUFFER_LEN);
    }

    // App，Key部不为空，这返回App，Key都匹配的键值
    if (operate == 4)
    {
        //
        return ProcessOperateFour(pszSectionName, pszKeyName, pszDefaultStr,
                                  pszRetValue, nRetLen, pstrtmp, ntmp, szOneLine, LINE_BUFFER_LEN);
    }

    return iRet;
}
