/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_LOG_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_LOG_H_

#include <stdio.h>
#include <string>

#include "Comm/Utils/TqcCommon.h"
#include "Comm/Utils/TqcLock.h"
#include "Comm/Utils/TSingleton.h"

class CLog : public TSingleton<CLog> {
  public:
    DECLARE_SINGLETON_CLASS(CLog);

    enum LogPriority {
        LOG_PRIORITY_ERROR = 0x1,
        LOG_PRIORITY_WARN = 0x2,
        LOG_PRIORITY_RUN = 0x4,
    };
    CLog();

  public:
    /*!
      @brief 初始化日志系???
      @param[in] pszLogFileName 日志文件基础???
      @param[in] eLogLevel 日志级别，可过滤日志输出
      @param[in] nLogFileSize 单个日志文件大小，默认为10M
      @param[in] nLogRollNum 日志文件个数
      @return 0 成功, -1失败
    */
    int init(const char *pszLogFileName,
        int eLogLevel = LOG_PRIORITY_ERROR | LOG_PRIORITY_WARN | LOG_PRIORITY_RUN,
        int nLogFileSize = 10 * 1024 * 1024, int nLogRollNum = 5);

    /*!
      @brief 输出日志
      @param[in] eLogLevel 日志级别
      @param[in] pszLogContent 输出日志内容
      @param[in] uLogContentLen 输出日志内容长度
      @return
    */
    // int logWrite(int eLogLevel, const char* pszFormat, ...);
    int logWrite(int eLogLevel, const char *pszLogContent, size_t uLogContentLen);

    /*!
      @brief 关闭日志文件
    */
    void closeLog();

    int getLogLevel(char *arg);

  private:
    /*!
      @brief 向日志文件输出错误级别日志内???
      @param[in] pszLogContent 输出日志内容
      @param[in] uLogContentLen 输出日志内容长度
    */
    void logError(const char *pszLogContent, size_t uLogContentLen);

    /*!
      @brief 向日志文件输出错误级别日志内???
      @param[in] pszLogContent 输出日志内容
      @param[in] uLogContentLen 输出日志内容长度
    */
    void logWarn(const char *pszLogContent, size_t uLogContentLen);

    /*!
      @brief 向日志文件输出错误级别日志内???
      @param[in] pszLogContent 输出日志内容
      @param[in] uLogContentLen 输出日志内容长度
    */
    void logRun(const char *pszLogContent, size_t uLogContentLen);
    /*!
      @brief 打开日志文件，若文件存在不清???
      @param[in] pszLogFileName 日志文件路径
      @return 0 成功???< 0 失败
    */
    int openLogFile(const char *pszLogFileName);

    /*!
    */
    int openResetLogFile(const char *pszLogFileName);

  private:
    FILE        *m_pfLogfile;
    int         m_nFileSize;
    int         m_nLogPriotify;
    int         m_nMaxRollNum;
    int         m_nCurRollNum;
    int         m_nCurPosition;
    std::string m_strLogBaseName;
    CLock       m_oLock;
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_LOG_H_
