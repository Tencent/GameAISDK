/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <pthread.h>
#include <unistd.h>
#include <sys/select.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>

#include "Os/TqcOs.h"

typedef void* (*pfnAndroidThreadDecl)(void* pThreadData);

void* TqcOsCreateThread(void *threadMain, void *pThread) {
    pthread_t handle;

    pthread_create(&handle, NULL, (pfnAndroidThreadDecl)threadMain,
    reinterpret_cast<void*>(pThread));
    return reinterpret_cast<void*>(handle);
}

void TqcOsSleep(int millisecond) {
    usleep(1000 * millisecond);
}

LockerHandle TqcOsCreateMutex() {
    pthread_mutex_t *mutex = new pthread_mutex_t;

    if (pthread_mutex_init(mutex, NULL) != 0)
        return 0;

    return (LockerHandle)mutex;
}

void TqcOsDeleteMutex(LockerHandle handle) {
    pthread_mutex_destroy(reinterpret_cast<pthread_mutex_t*>(handle));
    delete reinterpret_cast<pthread_mutex_t*>(handle);
}

bool TqcOsAcquireMutex(LockerHandle handle) {
    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(handle));
    return true;
}

void TqcOsReleaseMutex(LockerHandle handle) {
    pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(handle));
}

unsigned int TqcOsGetMicroSeconds(void) {
    unsigned int time;
    struct timeval tv;

    /* Return the time of day in milliseconds. */
    gettimeofday(&tv, 0);
    time = (tv.tv_sec * 1000) + (tv.tv_usec / 1000);

    return time;
}
