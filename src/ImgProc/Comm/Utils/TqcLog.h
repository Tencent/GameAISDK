/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCLOG_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCLOG_H_

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <string>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/Log.h"

// Todo: the zone do not support.
// We can also use zone to control output.
#define LOG_ZONE 0xFFFF

// Log level
// Default is warning level.
// Debug will output the most details.
#define FACE_ERROR   0x0001
#define FACE_WARNING 0x0002
#define FACE_INFO    0x0003
#define FACE_DEBUG   0x0004

// level of log
#define LOG_LEVEL 0x0003

// We can disable all log.
#ifdef TRACER_NO_LOG
#define TRACER_LOG(level, fmt, ...) {}
#else
#define TRACER_LOG(level, fmt, ...) FACE_LOG(level, FACE_TRACER, fmt, ##__VA_ARGS__)
#endif

// Using the following macro to output log.
#define LOGE(fmt, ...) FACE_LOG(FACE_ERROR, LOG_ZONE, fmt, ##__VA_ARGS__)
#define LOGW(fmt, ...) FACE_LOG(FACE_WARNING, LOG_ZONE, fmt, ##__VA_ARGS__)
#define LOGI(fmt, ...) FACE_LOG(FACE_INFO, LOG_ZONE, fmt, ##__VA_ARGS__)
#define LOGD(fmt, ...) FACE_LOG(FACE_DEBUG, LOG_ZONE, fmt, ##__VA_ARGS__)

// log level.
extern int g_logLevel;

// Windows and Mac use the same code.
#if defined(WIN32) || defined(__APPLE__) || defined(_WINDOWS)
#define FACE_LOG(level, zone, fmt, ...)                                                           \
    do {                                                                                          \
        if (zone & LOG_ZONE) {                                                                    \
            if (level == FACE_ERROR && level <= g_logLevel) {                                     \
                char szErrLogBuf[512];                                                            \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szErrLogBuf, sizeof(szErrLogBuf), "%s|%s|%s:%d|ERROR|%s\n",              \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szErrLogBuf);                                                        \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_ERROR, szErrLogBuf,              \
                          strlen(szErrLogBuf));                                                   \
            }                                                                                     \
            if (level == FACE_WARNING && level <= g_logLevel) {                                   \
                char szWarnLogBuf[512];                                                           \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szWarnLogBuf, sizeof(szWarnLogBuf), "%s|%s|%s:%d|WARN|%s\n",             \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szWarnLogBuf);                                                       \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_WARN, szWarnLogBuf,              \
                    strlen(szWarnLogBuf));                                                        \
            }                                                                                     \
            if (level == FACE_INFO && level <= g_logLevel) {                                      \
                char szRunLogBuf[512];                                                            \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szRunLogBuf, sizeof(szRunLogBuf), "%s|%s|%s:%d|INFO|%s\n",               \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szRunLogBuf);                                                        \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_RUN, szRunLogBuf,                \
                    strlen(szRunLogBuf));                                                         \
            }                                                                                     \
            if (level == FACE_DEBUG && level <= g_logLevel) {                                     \
                char szRunLogBuf[512];                                                            \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szRunLogBuf, sizeof(szRunLogBuf), "%s|%s|%s:%d|DEBUG|%s\n",              \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szRunLogBuf);                                                        \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_RUN, szRunLogBuf,                \
                    strlen(szRunLogBuf));                                                         \
            }                                                                                     \
        }                                                                                         \
    } while (0)

// Android has its own log code.
#elif defined(ANDROID)

#include <android/log.h>

#define FACE_LOG(level, zone, fmt, ...)                                                  \
    do {                                                                                 \
        if (zone & LOG_ZONE) {                                                           \
            if (level == FACE_ERROR && level <= g_logLevel) {                            \
                __android_log_print(ANDROID_LOG_ERROR, "TqcVision", fmt, ##__VA_ARGS__); \
            }                                                                            \
            if (level == FACE_WARNING && level <= g_logLevel) {                          \
                __android_log_print(ANDROID_LOG_WARN, "TqcVision", fmt, ##__VA_ARGS__);  \
            }                                                                            \
            if (level == FACE_INFO && level <= g_logLevel) {                             \
                __android_log_print(ANDROID_LOG_INFO, "TqcVision", fmt, ##__VA_ARGS__);  \
            }                                                                            \
            if (level == FACE_DEBUG && level <= g_logLevel) {                            \
                __android_log_print(ANDROID_LOG_DEBUG, "TqcVision", fmt, ##__VA_ARGS__); \
            }                                                                            \
        }                                                                                \
    } while (0)
#else
// Linux will use the following code.
#define FACE_LOG(level, zone, fmt, ...)                                                           \
    do {                                                                                          \
        if (zone & LOG_ZONE) {                                                                    \
            if (level == FACE_ERROR && level <= g_logLevel) {                                     \
                char szErrLogBuf[512];                                                            \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szErrLogBuf, sizeof(szErrLogBuf), "%s|%s|%s:%d|ERROR|%s\n",              \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szErrLogBuf);                                                        \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_ERROR, szErrLogBuf,              \
                    strlen(szErrLogBuf));                                                         \
            }                                                                                     \
            if (level == FACE_WARNING && level <= g_logLevel) {                                   \
                char szWarnLogBuf[512];                                                           \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szWarnLogBuf, sizeof(szWarnLogBuf), "%s|%s|%s:%d|WARN|%s\n",             \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szWarnLogBuf);                                                       \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_WARN, szWarnLogBuf,              \
                    strlen(szWarnLogBuf));                                                        \
            }                                                                                     \
            if (level == FACE_INFO && level <= g_logLevel) {                                      \
                char szRunLogBuf[512];                                                            \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szRunLogBuf, sizeof(szRunLogBuf), "%s|%s|%s:%d|INFO|%s\n",               \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szRunLogBuf);                                                        \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_RUN, szRunLogBuf,                \
                    strlen(szRunLogBuf));                                                         \
            }                                                                                     \
            if (level == FACE_DEBUG && level <= g_logLevel) {                                     \
                char szDeLogBuf[512];                                                             \
                char szTimeBuff[32];                                                              \
                char szContent[256];                                                              \
                SNPRINTF(szContent, sizeof(szContent), fmt, ##__VA_ARGS__);                       \
                SNPRINTF(szDeLogBuf, sizeof(szDeLogBuf), "%s|%s|%s:%d|DEBUG|%s\n",                \
                         CurTimeStamp(szTimeBuff, sizeof(szTimeBuff)),                            \
                         __FILE__, __FUNCTION__, __LINE__, szContent);                            \
                printf("%s", szDeLogBuf);                                                         \
                CLog::getInstance()->logWrite(CLog::LOG_PRIORITY_RUN, szDeLogBuf,                 \
                    strlen(szDeLogBuf));                                                          \
            }                                                                                     \
        }                                                                                         \
    }                                                                                             \
    while (0)
#endif

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_TQCLOG_H_
