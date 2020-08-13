/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <limits.h>
#include <stdarg.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>

#ifdef _WINDOWS
#include <io.h>
#else
#include <unistd.h>
#include <sys/time.h>
#endif

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/Log.h"
#include "Comm/Utils/TqcCommon.h"
#include "Comm/Utils/TqcLog.h"


CLog::CLog()
{
    m_pfLogfile = NULL;
    m_nFileSize = -1;
    m_nLogPriotify = -1;
    m_nMaxRollNum = -1;
    m_nCurRollNum = -1;
    m_nCurPosition = -1;
}
int CLog::init(const char *pszLogFileName, int eLogLevel, int nLogFileSize, int nLogRollNum)
{
    static bool bInit = true;
    int         iRet  = 0;

    if (bInit)
    {
        std::string path;
        std::string pathLog;
        std::string logFolderName;
        std::string fileName;

        m_pfLogfile      = NULL;
        m_nLogPriotify   = eLogLevel;
        m_nFileSize      = nLogFileSize;
        m_nMaxRollNum    = nLogRollNum;
        m_nCurRollNum    = -1;
        m_strLogBaseName = pszLogFileName;

        SplitFullName(m_strLogBaseName, path, fileName);
        SplitFullName(path, pathLog, logFolderName);

        // 对日志文件进行检??
        char   szLogFileName[256];
        time_t stLastModTime = 0;
        SNPRINTF(szLogFileName, sizeof(szLogFileName), "%s", m_strLogBaseName.c_str());
        m_nCurRollNum  = 0;
        m_nCurPosition = 0;
        // if (0 == _access(szLogFileName, F_OK))    // 文件存在
#ifdef _WINDOWS
        if (0 == _access(szLogFileName, 0))
#else
        if (0 == access(szLogFileName, F_OK))    // 文件存在
#endif
        {
            struct stat stFileAttr;
            stat(szLogFileName, &stFileAttr);
            stLastModTime  = stFileAttr.st_mtime;
            m_nCurPosition = stFileAttr.st_size;

            char szTmpLogFileName[128];         // 临时，循环查找使??

            for (int i = 1; i < m_nMaxRollNum; ++i)
            {
                SNPRINTF(szTmpLogFileName, sizeof(szTmpLogFileName), "%s.log.%d", m_strLogBaseName.c_str(), i);
#ifdef _WINDOWS
                if (0 != _access(szTmpLogFileName, 0))    // 不存
#else
                if (0 != access(szTmpLogFileName, 0))            // 不存
#endif

                {
                    break;
                }
                else             // 存在
                {
                    struct stat stTmpFileAttr;
                    stat(szTmpLogFileName, &stTmpFileAttr);
                    if (stTmpFileAttr.st_mtime > stLastModTime)
                    {
                        strncpy(szLogFileName, szTmpLogFileName, sizeof(szLogFileName));
                        m_nCurRollNum  = i;
                        m_nCurPosition = stTmpFileAttr.st_size;
                        stLastModTime  = stTmpFileAttr.st_mtime;
                    }
                    else if (stTmpFileAttr.st_mtime == stLastModTime)
                    {
                        if (stTmpFileAttr.st_size < m_nCurPosition)                    // 选取文件大小最小的
                        {
                            strncpy(szLogFileName, szTmpLogFileName, sizeof(szLogFileName));
                            m_nCurRollNum  = i;
                            m_nCurPosition = stTmpFileAttr.st_size;
                            stLastModTime  = stTmpFileAttr.st_mtime;
                        }
                    }
                }
            }
        }

        // 打开文件
        int iRet = openLogFile(szLogFileName);
        if (iRet == -1)
        {
            CreateDir(pathLog.c_str());
            CreateDir(path.c_str());
            iRet = openLogFile(szLogFileName);

            if (iRet == -1)
                LOGE("Cannot create log file(%s)", szLogFileName);
        }

        bInit = false;
    }

    return iRet;
};

int CLog::logWrite(int eLogLevel, const char *pszLogContent, size_t uLogContentLen)
{
    int iRet = 0;

    m_oLock.Lock();

    if (LOG_PRIORITY_ERROR == (m_nLogPriotify & eLogLevel))
    {
        logError(pszLogContent, uLogContentLen);
    }

    if (LOG_PRIORITY_WARN == (m_nLogPriotify & eLogLevel))
    {
        logWarn(pszLogContent, uLogContentLen);
    }

    if (LOG_PRIORITY_RUN == (m_nLogPriotify & eLogLevel))
    {
        logRun(pszLogContent, uLogContentLen);
    }

    m_oLock.UnLock();

    return iRet;
}

void CLog::logError(const char *pszLogContent, size_t uLogContentLen)
{
    logRun(pszLogContent, uLogContentLen);
}

void CLog::logWarn(const char *pszLogContent, size_t uLogContentLen)
{
    logRun(pszLogContent, uLogContentLen);
}

void CLog::logRun(const char *pszLogContent, size_t uLogContentLen)
{
    if (NULL != m_pfLogfile)
    {
        // 需要先判断若写入文件单个文件是否会超限
        if (m_nFileSize < m_nCurPosition + static_cast<int>(uLogContentLen))
        {
            // 关闭老的日志文件
            closeLog();

            m_nCurRollNum = (m_nCurRollNum + 1) % m_nMaxRollNum;
            char szNewLogFile[64];
            if (0 == m_nCurRollNum)            // 首文??
            {
                SNPRINTF(szNewLogFile, sizeof(szNewLogFile), "%s.log", m_strLogBaseName.c_str());
            }
            else
            {
                SNPRINTF(szNewLogFile, sizeof(szNewLogFile), "%s.log.%d", m_strLogBaseName.c_str(), m_nCurRollNum);
            }

            // 打开新的日志文件
            openResetLogFile(szNewLogFile);
            m_nCurPosition = 0;
            if (NULL != m_pfLogfile)
            {
                fwrite(pszLogContent, uLogContentLen, 1, m_pfLogfile);
                m_nCurPosition += static_cast<int>(uLogContentLen);
                fflush(m_pfLogfile);
            }
        }
        else
        {
            fwrite(pszLogContent, uLogContentLen, 1, m_pfLogfile);
            m_nCurPosition += static_cast<int>(uLogContentLen);
            fflush(m_pfLogfile);
        }
    }
}

//
// Close log file.
//
void CLog::closeLog()
{
    if (m_pfLogfile)
    {
        fclose(m_pfLogfile);
        m_pfLogfile = NULL;
    }
}

//
// Open log file.
//
int CLog::openLogFile(const char *pszLogFileName)
{
    int iRet = 0;

    m_pfLogfile = fopen(pszLogFileName, "a+");

    if (NULL == m_pfLogfile)
    {
        iRet = -1;
    }

    return iRet;
}

//
// Open and reset log file.
//
int CLog::openResetLogFile(const char *pszLogFileName)
{
    int iRet = 0;

    m_pfLogfile = fopen(pszLogFileName, "w");

    if (NULL == m_pfLogfile)
    {
        iRet = -1;
    }

    return iRet;
}
