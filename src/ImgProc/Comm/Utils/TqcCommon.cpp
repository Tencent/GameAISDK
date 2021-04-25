/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <ctype.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <string>
#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcCommon.h"

// Level of log output.
int g_logLevel = FACE_INFO;

#ifdef _WINDOWS
#include <Windows.h>
#endif

#ifdef LINUX
#include <unistd.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#endif

/*!
  @brief 左规整字符串，去掉字符串左边的空格，换行，回车，Tab
  @param[in] pszStr
  @return char*
*/
char* StrTrimLeft(char *pszStr) {
    char *pszIter = pszStr;

    for (; *pszIter != '\0'; pszIter++) {
        if (::isspace(static_cast<unsigned char>(*pszIter)) != 0) {
            continue;
        } else {
            break;
        }
    }

    if (pszIter != pszStr) {
        memmove(pszStr, pszIter, strlen(pszIter) + 1);
    }

    return pszStr;
}

/*!
  @brief 右规整字符串，去掉字符串右边的空格，换行，回车，Tab
  @param[in] pszStr
  @return char*
*/
char* StrTrimRight(char *pszStr) {
    char *pszIter = pszStr + strlen(pszStr) - 1;

    for (; pszIter >= pszStr; pszIter--) {
        if (::isspace(static_cast<unsigned char>(*pszIter)) != 0) {
            continue;
        } else {
            break;
        }
    }

    if (pszIter != pszStr + strlen(pszStr) - 1) {
        *++pszIter = '\0';
    }

    return pszStr;
}

/*!
  @brief 规整字符串，去掉字符串两边的空格，换行，回车，Tab
  @param[in] pszStr
  @return char*
*/
char* StrTrim(char *pszStr) {
    StrTrimLeft(pszStr);
    StrTrimRight(pszStr);

    return pszStr;
}

/*!
  @brief 将字符串全部转换为大写字符
  @param[in] pszStr
  @return char*
*/
char* StrUpper(char *pszStr) {
    char *pszIter = pszStr;

    while (*pszIter != '\0') {
        *pszIter = static_cast<char>(::toupper(*pszIter));
        ++pszIter;
    }

    return pszStr;
}

/*!
  @brief 将字符串全部转换为小写字符
  @param[in] pszStr
  @return char*
*/
char* StrLower(char *pszStr) {
    char *pszIter = pszStr;

    while (*pszIter != '\0') {
        *pszIter = static_cast<char>(::tolower(*pszIter));
    }

    return pszStr;
}

/*!
  @brief 字符串比较，忽视大小写
  @param[in] pszStr1
  @param[in] pszStr2
  @param[in] nCmpLen 字符串比较长度，默认全比较
  @return int 其值含义参见strcasecmp返回值
*/
int StrCaseIgnoreCmp(const char *pszStr1, const char *pszStr2, size_t nCmpLen) {
#ifdef _WINDOWS
    if (0 < nCmpLen) {
        return strnicmp(pszStr1, pszStr2, nCmpLen);
    } else {
        return stricmp(pszStr1, pszStr2);
    }
#else
    if (0 < nCmpLen) {
        return ::strncasecmp(pszStr1, pszStr2, nCmpLen);
    } else {
        return ::strcasecmp(pszStr1, pszStr2);
    }
#endif
}

/*!
  @brief 字符串定长比较，敏感大小写
  @param[in] pszStr1
  @param[in] pszStr2
  @param[in] nCmpLen 字符串比较长度，默认全比较
  @return char*
*/
int StrCaseSensorCmp(const char *pszStr1, const char *pszStr2, size_t nCmpLen) {
    if (0 < nCmpLen) {
        return ::strncmp(pszStr1, pszStr2, nCmpLen);
    } else {
        return ::strcmp(pszStr1, pszStr2);
    }
}

void CreateDigitResultDir(const char *strSavedPath) {
    char cmd[256];

    memset(cmd, 0, 256);

#if WINDOWS
    SNPRINTF(cmd, sizeof(cmd), "md %s", strSavedPath);
    size_t nLen = strlen(cmd);

    for (int i = 0; i < nLen; i++) {
        if (cmd[i] == '/')
            cmd[i] = '\\';
    }

    system(cmd);

    for (int i = 0; i < TQC_DIGIT_CHAR_NUM; i++) {
        cmd[nLen] = '\\';
        cmd[nLen + 1] = '0' + i;
        cmd[nLen + 2] = '\0';
        system(cmd);
    }
#endif /* WINDOWS */
}

void CreateDir(const char *strSavedPath) {
    char cmd[256];

    memset(cmd, 0, 256);

#if WINDOWS
    SNPRINTF(cmd, sizeof(cmd), "md %s", strSavedPath);
    size_t nLen = strlen(cmd);

    for (int i = 0; i < nLen; i++) {
        if (cmd[i] == '/')
            cmd[i] = '\\';
    }

    system(cmd);
#endif
    /* WINDOWS */

#ifdef LINUX
    if (0 != access(strSavedPath, 0)) {
        if (-1 == mkdir(strSavedPath, S_IRWXU)) {
            printf("mkdir %s failed \n", strSavedPath);
        }
    }
#endif
}

//
// Split full path of file name to path and file name.
//
void SplitFullName(const std::string &str, std::string &path, std::string &fileName) {
    size_t found = str.find_last_of("/\\");  // Point

    path = str.substr(0, found);
    fileName = str.substr(found + 1);
}

//
// Parse csv file.
//
void ReadCsvFile(FILE *pFile, const char cSplitter, char *output, int nLen) {
    int  nIndex = 0;
    int  nRead = 0;
    char c;

    if (output == NULL || nLen == 0) {
        return;
    }

    if (pFile == NULL) {
        return;
    }

    memset(output, 0, nLen);

    do {
        // c = fgetc(pFile);
        int m = fgetc(pFile);
        // 是否到达文件末尾
        if (EOF == m) {
            break;
        } else {
            c = m;
        }

        if (c != '\n' && c != cSplitter) {
            output[nRead++] = c;
            continue;
        }

        if (c == '\n' || c == cSplitter)
            break;

        if (nRead >= nLen) {
            break;
        }

        if (feof(pFile))
            break;
    } while (1);

    return;
}

#ifdef _WINDOWS
// Windows does not have this function, we define a fake one.
int gettimeofday(struct timeval *tp, void *tzp) {
    time_t     clock;
    struct tm  tm;
    SYSTEMTIME wtm;

    GetLocalTime(&wtm);
    tm.tm_year = wtm.wYear - 1900;
    tm.tm_mon = wtm.wMonth - 1;
    tm.tm_mday = wtm.wDay;
    tm.tm_hour = wtm.wHour;
    tm.tm_min = wtm.wMinute;
    tm.tm_sec = wtm.wSecond;
    tm.tm_isdst = -1;
    clock = mktime(&tm);
    tp->tv_sec = clock;
    tp->tv_usec = wtm.wMilliseconds * 1000;

    return (0);
}
#endif

bool CheckTimeParamInvalid(const int nTimeBuffLen, const TIME_STRING_FORMAT eFormat) {
    if (TSF_YYYY_MM_DD_HH_MM_SS_UUUU == eFormat
        && TSF_YYYY_MM_DD_HH_MM_SS_UUUU_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    if (TSF_YYYY_MM_DD_HH_MM_SS == eFormat && TSF_YYYY_MM_DD_HH_MM_SS_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    if (TSF_YYYY_MM_DD == eFormat && TSF_YYYY_MM_DD_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    if (TSF_YYYYMMDDHHMMSS == eFormat && TSF_YYYYMMDDHHMMSS_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    if (TSF_YYYYMMDD == eFormat && TSF_YYYYMMDD_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    if (TSF_YYYYMMDD_HHMMSS == eFormat && TSF_YYYYMMDD_HHMMSS_MIN_LEN > nTimeBuffLen) {
        return false;
    }

    return true;
}
/*!
  @brief 获取当前系统时间戳（非线程安全）
  @param[in] pszTimeBuff 缓存buff
  @param[in] nTimeBuffLen 缓存buff长度
  @param[in] eFormat 输出时间戳格式，默认格式为TSF_YYYY_MM_DD_HH_MM_SS_UUUUUU
  @return 时间戳格式化输出
*/
char* CurTimeStamp(char *pszTimeBuff, int nTimeBuffLen, TIME_STRING_FORMAT eFormat) {
    if (!CheckTimeParamInvalid(nTimeBuffLen, eFormat)) {
        return NULL;
    }
    struct timeval stCurTime;
    if (0 != gettimeofday(&stCurTime, NULL)) {
        return NULL;
    }

#ifdef _WINDOWS
    SYSTEMTIME wtm;

    GetLocalTime(&wtm);

    struct tm stTm;
    struct tm *pstTm = NULL;

    stTm.tm_year = wtm.wYear - 1900;
    stTm.tm_mon = wtm.wMonth - 1;
    stTm.tm_mday = wtm.wDay;
    stTm.tm_hour = wtm.wHour;
    stTm.tm_min = wtm.wMinute;
    stTm.tm_sec = wtm.wSecond;
    pstTm = &stTm;
#else
    struct tm stTm;
    struct tm *pstTm = localtime_r(&stCurTime.tv_sec, &stTm);
    if (NULL == pstTm) {
        return NULL;
    }
#endif

    switch (eFormat) {
    case TSF_YYYY_MM_DD_HH_MM_SS_UUUU:
#ifdef __APPLE__
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d-%02d-%02d %02d:%02d:%02d.%04d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday,
            pstTm->tm_hour,
            pstTm->tm_min,
            pstTm->tm_sec,
            stCurTime.tv_usec / 100);
#else
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d-%02d-%02d %02d:%02d:%02d.%04ld",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday,
            pstTm->tm_hour,
            pstTm->tm_min,
            pstTm->tm_sec,
            stCurTime.tv_usec / 100);
#endif
        break;

    case TSF_YYYY_MM_DD_HH_MM_SS:
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d-%02d-%02d %02d:%02d:%02d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday,
            pstTm->tm_hour,
            pstTm->tm_min,
            pstTm->tm_sec);
        break;

    case TSF_YYYY_MM_DD:
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d-%02d-%02d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday);
        break;

    case TSF_YYYYMMDDHHMMSS:
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d%02d%02d%02d%02d%02d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday,
            pstTm->tm_hour,
            pstTm->tm_min,
            pstTm->tm_sec);
        break;

    case TSF_YYYYMMDD:
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d%02d%02d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday);
        break;

    case TSF_YYYYMMDD_HHMMSS:
        SNPRINTF(pszTimeBuff, nTimeBuffLen, "%4d%02d%02d_%02d%02d%02d",
            pstTm->tm_year + 1900,
            pstTm->tm_mon + 1,
            pstTm->tm_mday,
            pstTm->tm_hour,
            pstTm->tm_min,
            pstTm->tm_sec);
        break;

    default:
        return NULL;
    }

    return pszTimeBuff;
}

void GetPathDir(const char *path, char *dir) {
    if (NULL == path) {
        dir[0] = '\0';
        return;
    }

    if ('/' == path[strlen(path)]) {
        strcpy(dir, path);
        return;
    }

    std::string sPath(path);
    std::size_t idx1 = -1, idx2 = -1;
    idx1 = sPath.rfind('\\');
    if (idx1 != std::string::npos) {
        strcpy(dir, sPath.substr(0, idx1).c_str());
    }
    idx2 = sPath.rfind('/');
    if (idx2 != std::string::npos) {
        strcpy(dir, sPath.substr(0, idx2).c_str());
    }
}
