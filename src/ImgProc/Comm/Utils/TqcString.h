/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCSTRING_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCSTRING_H_

#include <string>
#include <vector>

/*!
  @brief 字符串拷贝
  @param[in]  pszDest :目地字符串
  @param[in]  pszSrc:源字符串
  @param[in]  iLen:  拷贝长度
  @return void
*/
void StrCpy(char *pszDest, const char *pszSrc, int iLen);

/*!
  @brief 转变IP字符串为ID值
  @param[in]  szIpStr: 源IP字符串
  @param[in|out]  iIpID: 目标IP数值
  @return
*/
void ChgStrToIP(char *szIpStr, int *iIpID);

char* randstr(char *buffer, int len);

/*!
  @brief 把字符串str按照seq分隔，以字符串的格式保存到outVct
  @param[in]  str: 待分析的字符串(长度不能超过4k)
  @param[in]  seq: 分割符
  @param[out] outVct: 输出保存分割后的字符串
  @return
*/

void token(const char *str, const char *seq, std::vector<std::string> *poutVct);

/*!
  @brief 把字符串str按照seq分隔，以int的格式保存到outVct
  @param[in]  str: 待分析的字符串(长度不能超过4k)
  @param[in]  seq: 分割符
  @param[out] outVct: 输出保存分割后的整数
  @return
*/
void token(const char *str, const char *seq, std::vector<int> *poutVct);


/* bool IsStringEndWith(const char * sStr, const char * sSubStr, int iSubStrLen);
  bool IsStringBeginWith(const char * sStr, const char * sSubStr, int iSubStrLen);
  void HashStrToInt(const char * pszString, int *pnHashValue);
  int  HexPrintfBuff(void * pszBuff, int nBuffLen,  std::string *pstrOut);
  char* StrToLower(const char* pszStr);

  // find 'substr' from a fixed-length buffer
  // ('full_data' will be treated as binary data buffer)
  // return NULL if not found
  char* memstr(char* full_data, int full_data_len, const char* substr);
*/
#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCSTRING_H_
