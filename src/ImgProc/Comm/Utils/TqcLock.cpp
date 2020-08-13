/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/Utils/TqcLock.h"

CLock::CLock()
{
    Init();
}
CLock::~CLock()
{
    UnInit();
}

//
// Lock the conflict code.
//
bool CLock::Lock()
{
#ifdef WINDOWS
    EnterCriticalSection(&m_sect);
#else
    pthread_mutex_lock(&m_sect);
#endif

    return true;
}

//
// Release lock.
//
bool CLock::UnLock()
{
#ifdef WINDOWS
    LeaveCriticalSection(&m_sect);
#else
    // pthread_mutex_unlock(&mutexTheMutex);
    pthread_mutex_unlock(&m_sect);
#endif

    return true;
}

//
// Create lock.
//
bool CLock::Init()
{
#ifdef WINDOWS
    if (!::InitializeCriticalSectionAndSpinCount(&m_sect, 0))
    {
        return false;
    }

#else
    pthread_mutexattr_t Attr;

    pthread_mutexattr_init(&Attr);
    pthread_mutexattr_settype(&Attr, PTHREAD_MUTEX_RECURSIVE);
    pthread_mutex_init(&m_sect, &Attr);
#endif

    return true;
}

bool CLock::UnInit()
{
#ifdef WINDOWS
    ::DeleteCriticalSection(&m_sect);
#else
    pthread_mutex_destroy(&m_sect);
#endif

    return true;
}
