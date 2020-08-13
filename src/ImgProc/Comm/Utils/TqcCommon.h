/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TQC_COMMON_H_
#define TQC_COMMON_H_

#include <stdint.h>
#include <stdio.h>
#include <string>
#include "Comm/Utils/TqcLog.h"

#define TQC_PATH_STR_LEN   256
#define TQC_DIGIT_CHAR_NUM 10               // number of digitals.
#define TQC_CHARACTER_SIZE 28

// 时间字符的各种格式，
enum TIME_STRING_FORMAT
{
    // 格式：只有年月日的紧缩格式 20150825
    TSF_YYYYMMDD,
    // 格式：年月日时分秒的格式，没有分隔符,20150825200145
    TSF_YYYYMMDDHHMMSS,
    // 格式：年月日，有分隔符，如2015-08-25
    TSF_YYYY_MM_DD,
    // 格式：如2015-08-25 20:01:45
    TSF_YYYY_MM_DD_HH_MM_SS,
    // 格式：标准的ISO时间格式，如2015-08-25 20:01:45.123456
    TSF_YYYY_MM_DD_HH_MM_SS_UUUU,
    // 格式：如YYYYMMDD_HHMMSS
    TSF_YYYYMMDD_HHMMSS,
};

// 时间转换缓存最小长度
enum TIME_STRING_FORMAT_MIN_LEN
{
    // 格式：只有年月日的紧缩格式 20150825
    TSF_YYYYMMDD_MIN_LEN = 10,
    // 格式：年月日时分秒的格式，没有分隔符,20150825200145
    TSF_YYYYMMDDHHMMSS_MIN_LEN = 16,
    // 格式：年月日，有分隔符，如2015-08-25
    TSF_YYYY_MM_DD_MIN_LEN = 12,
    // 格式：如2015-08-25 20:01:45
    TSF_YYYY_MM_DD_HH_MM_SS_MIN_LEN = 20,
    // 格式：标准的ISO时间格式，如2015-08-25 20:01:45.123456
    TSF_YYYY_MM_DD_HH_MM_SS_UUUU_MIN_LEN = 26,
    // 格式：如YYYYMMDD_HHMMSS
    TSF_YYYYMMDD_HHMMSS_MIN_LEN = 16,
};

/*!
   @brief 左规整字符串，去掉字符串左边的空格，换行，回车，Tab
   @param[in] pszStr
   @return char*
 */
char* StrTrimLeft(char *pszStr);

/*!
   @brief 右规整字符串，去掉字符串右边的空格，换行，回车，Tab
   @param[in] pszStr
   @return char*
 */
char* StrTrimRight(char *pszStr);

/*!
   @brief 规整字符串，去掉字符串两边的空格，换行，回车，Tab
   @param[in] pszStr
   @return char*
 */
char* StrTrim(char *pszStr);

/*!
   @brief 将字符串全部转换为大写字符
   @param[in] pszStr
   @return char*
 */
char* StrUpper(char *pszStr);

/*!
   @brief 将字符串全部转换为小写字符
   @param[in] pszStr
   @return char*
 */
char* StrLower(char *pszStr);

/*!
   @brief 字符串定长比较，敏感大小写
   @param[in] pszStr1
   @param[in] pszStr2
   @param[in] nCmpLen 字符串比较长度，默认全比较
   @return char*
 */
int StrCaseSensorCmp(const char *pszStr1, const char *pszStr2, size_t nCmpLen = 0);

/*!
   @brief 获取当前系统时间戳（非线程安全）
   @param[in] pszTimeBuff 缓存buff
   @param[in] nTimeBuffLen 缓存buff长度
   @param[in] eFormat 输出时间戳格式，默认格式为TSF_YYYY_MM_DD_HH_MM_SS_UUUUUU
   @return 时间戳格式化输出
 */
char* CurTimeStamp(char *pszTimeBuff, int nTimeBuffLen, TIME_STRING_FORMAT eFormat = TSF_YYYY_MM_DD_HH_MM_SS_UUUU);

/*!
   @brief 字符串比较，忽视大小写
   @param[in] pszStr1
   @param[in] pszStr2
   @param[in] nCmpLen 字符串比较长度，默认全比较
   @return int 其值含义参见strcasecmp返回值
 */
int StrCaseIgnoreCmp(const char *pszStr1, const char *pszStr2, size_t nCmpLen = 0);

void CreateDir(const char *strSavedPath);
// Create folders of digitals in the specified path.
void CreateDigitResultDir(const char *strSavedPath);

// Read one item from csv file.
void ReadCsvFile(FILE *pFile, const char cSplitter, char *output, int nLen);

void SplitFullName(const std::string &str, std::string &path, std::string &fileName);

#ifdef _WINDOWS
int gettimeofday(struct timeval *tp, void *tzp);
#endif

#endif // TQC_COMMON_H_
