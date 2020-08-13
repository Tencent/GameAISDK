/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef  TQC_LOCK_H_
#define  TQC_LOCK_H_

#ifdef WINDOWS
#include <Windows.h>
#else
#include <pthread.h>
#include <semaphore.h>
#endif

class CLock
{
public:
    CLock();
    virtual ~CLock();

public:
    bool    Lock();
    bool    UnLock();

protected:
    bool    Init();
    bool    UnInit();

private:
#ifdef WINDOWS
    CRITICAL_SECTION m_sect;
#else
    pthread_mutex_t m_sect;
#endif
};

#endif // TQC_LOCK_H_
