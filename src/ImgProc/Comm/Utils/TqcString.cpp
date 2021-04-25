/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

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
void StrCpy(char *pszDest, const char *pszSrc, int iLen) {
    strncpy(pszDest, pszSrc, iLen - 1);
    pszDest[iLen - 1] = '\0';
}

//
// Change string to ip address.
//
void ChgStrToIP(char *szIpStr, int *iIpID) {
#if defined(LINUX) || defined(__APPLE__)
    inet_aton(szIpStr, (struct in_addr*)iIpID);
#else
    // iIpID = inet_addr(szIpStr);
#endif
}

//
// Generate random string.
//
char* randstr(char *buffer, int len) {
    // char *chars="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890";
    // 为减少误判， 去掉0、1、O、o、L、l
    const char *chars = "ABCDEFGHIJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
    int        i, chars_len;

    chars_len = strlen(chars);

    for (i = 0; i < len; i++) {
        unsigned int nSeed = TqcOsGetMicroSeconds();
#if defined(LINUX) || defined(__APPLE__)
        buffer[i] = chars[static_cast<int>(static_cast<float>(chars_len) * \
            rand_r(&nSeed) / (RAND_MAX + 1.0))];
#elif defined(WINDOWS)
        buffer[i] = chars[static_cast<int>(static_cast<float>(chars_len) * \
            rand_s(&nSeed) / (RAND_MAX + 1.0))];
#endif
    }

    buffer[len] = '\0';
    return buffer;
}

//
// 把字符串str按照seq分隔，以字符串的格式保存到outVct
//
void token(const char *pszSource, const char *seq, std::vector<std::string> *poutVct) {
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

    while (token != NULL) {
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
void token(const char *str, const char *seq, std::vector<int> *poutVct) {
    if (poutVct == NULL) {
        return;
    }

    std::vector<std::string> vctStrout;

    token(str, seq, &vctStrout);

    for (size_t i = 0; i < vctStrout.size(); i++) {
        poutVct->push_back(atoi(vctStrout[i].c_str()));
    }
}
