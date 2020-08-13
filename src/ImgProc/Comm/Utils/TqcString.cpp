/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <stdio.h>
#include <string.h>

#define _CRT_RAND_S 1
#include <stdlib.h>

#if defined(LINUX) || defined(__APPLE__)
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#else
#include <winsock.h>
#endif

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcString.h"

#define  HEXVALUE 16

//
// string copy.
//
void StrCpy(char *pszDest, const char *pszSrc, int iLen)
{
    strncpy(pszDest, pszSrc, iLen - 1);
    pszDest[iLen - 1] = '\0';
}

//
// Change string to ip address.
//
void ChgStrToIP(char *szIpStr, int *iIpID)
{
#if defined(LINUX) || defined(__APPLE__)
    inet_aton(szIpStr, (struct in_addr*)iIpID);
#else
    // iIpID = inet_addr(szIpStr);
#endif
}

//
// Generate random string.
//
char* randstr(char *buffer, int len)
{
    // char *chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890";
    const char *chars = "ABCDEFGHIJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"; // 为减少误判， 去掉0、1、O、o、L、l
    int        i, chars_len;

    chars_len = strlen(chars);

    for (i = 0; i < len; i++)
    {
        unsigned int nSeed = TqcOsGetMicroSeconds();
#if defined(LINUX) || defined(__APPLE__)
        buffer[i] = chars[static_cast<int>(static_cast<float>(chars_len) * rand_r(&nSeed) / (RAND_MAX + 1.0))];
#elif defined(WINDOWS)
        buffer[i] = chars[static_cast<int>(static_cast<float>(chars_len) * rand_s(&nSeed) / (RAND_MAX + 1.0))];
#endif
    }

    buffer[len] = '\0';
    return buffer;
}

//
// 把字符串str按照seq分隔，以字符串的格式保存到outVct
//
void token(const char *pszSource, const char *seq, std::vector<std::string> *poutVct)
{
    if (!pszSource || seq == NULL || poutVct == NULL)
        return;

    char str[4096] = { 0 };
    memcpy(str, pszSource, strlen(pszSource));
    char *token = NULL;
    char buf[4096];
    buf[0] = '\0';
    char *p = buf;

#if defined(LINUX) || defined(__APPLE__)
    token = strtok_r(reinterpret_cast<char*>(str), seq, &p);
#else
    token = strtok_s(reinterpret_cast<char*>(str), seq, &p);
#endif

    while (token != NULL)
    {
        poutVct->push_back(token);
#if defined(LINUX) || defined(__APPLE__)
        token = strtok_r(NULL, seq, &p);
#else
        token = strtok_s(NULL, seq, &p);
#endif
    }
}

//
// 把字符串str按照seq分隔，以int的格式保存到outVct
//
void token(const char *str, const char *seq, std::vector<int> *poutVct)
{
    if (poutVct == NULL)
    {
        return;
    }

    std::vector<std::string> vctStrout;

    token(str, seq, &vctStrout);

    for (size_t i = 0; i < vctStrout.size(); i++)
    {
        poutVct->push_back(atoi(vctStrout[i].c_str()));
    }
}

//
// Check the first character of string.
//
/* bool IsStringBeginWith(const char *sStr, const char *sSubStr, int iSubStrLen)
   {
    if (NULL == sStr || NULL == sSubStr)
        return false;

    if (static_cast<int>(strlen(sStr)) < iSubStrLen)
        return false;

    if (strncmp(sStr, sSubStr, iSubStrLen) == 0)
        return true;

    return false;
   }

   {
    if (NULL == sStr || NULL == sSubStr)
        return false;

    int iStrLen = strlen(sStr);
    if (iStrLen < iSubStrLen)
        return false;

    if (strncmp(sStr + iStrLen - iSubStrLen, sSubStr, iSubStrLen) == 0)
        return true;

    return false;
   }

   void HashStrToInt(const char *pszString, int *pnHashValue)
   {
    if (pnHashValue == NULL)
    {
        return;
    }

 * pnHashValue = 0;
    int nLen = strlen(pszString);

    const char   *p    = pszString;
    int          i     = 0;
    int          seed  = 131;
    unsigned int dwRet = 0;

    while (i < nLen)
    {
        dwRet = dwRet * seed + (*p);
        p++;
        i++;
    }

 * pnHashValue = (dwRet & 0x7FFFFFFF);
   }

   //
   // Print hex.
   //
   int HexPrintfBuff(void *pszBuff, int nBuffLen, std::string *pstrOut)
   {
    if (NULL == pszBuff || pstrOut == NULL || nBuffLen <= 0)
    {
        printf("HexPrintBuff Param error \n");
        return -1;
    }

    char          szTemp[32]  = {0};
    unsigned char *pszStrBuff = (unsigned char*) pszBuff;

    for (int i = 0; i < nBuffLen; i++)
    {
        unsigned char onech = pszStrBuff[i];

        if (i % HEXVALUE == 0)
        {
 *#if defined(LINUX) || defined(__APPLE__)
            snprintf(szTemp, sizeof(szTemp), "\n0x%.4x: ", i);
 *#else
            _snprintf(szTemp, sizeof(szTemp), "\n0x%.4x: ", i);
 *#endif
 * pstrOut += szTemp;
        }

        if (i % 2 == 0)
        {
 * pstrOut += " ";
        }

 *#if defined(LINUX) || defined(__APPLE__)
        snprintf(szTemp, sizeof(szTemp), "%.2x", onech);
 *#else
        _snprintf(szTemp, sizeof(szTemp), "%.2x", onech);
 *#endif

 * pstrOut += szTemp;
    }

 * pstrOut += "\n";

    return 0;
   }

   char* StrToLower(const char *pszStr)
   {
    static char szLowerStr[128];

    if (NULL == pszStr)
    {
        return NULL;
    }

    int iLen = strlen(pszStr);

    for (int i = 0; i < iLen; i++)
    {
        szLowerStr[i] = tolower(pszStr[i]);
    }

    szLowerStr[iLen] = '\0';
    // printf("srcStr:%s, dstStr:%s ,Len:%d \n", pszStr, szLowerStr, iLen);
    return szLowerStr;
   }

   char* memstr(char *full_data, int full_data_len, const char *substr)
   {
    if (full_data == NULL || full_data_len <= 0 || substr == NULL)
    {
        return NULL;
    }

    if (*substr == '\0')
    {
        return NULL;
    }

    int sublen = strlen(substr);

    int  i;
    char *cur          = full_data;
    int  last_possible = full_data_len - sublen + 1;

    for (i = 0; i < last_possible; i++)
    {
        if (*cur == *substr)
        {
            // assert(full_data_len - i >= sublen);
            if (memcmp(cur, substr, sublen) == 0)
            {
                // found
                return cur;
            }
        }

        cur++;
    }

    return NULL;
   } */
