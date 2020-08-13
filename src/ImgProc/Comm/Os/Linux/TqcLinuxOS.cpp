/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifdef LINUX

#include <dirent.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <sys/select.h>
#include <sys/syscall.h>
#include <sys/time.h>
#include <sys/types.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include <vector>
#include "Comm/Os/TqcOs.h"

typedef void*(*pfnLinuxThreadDecl)(void *pThreadData);

//
// Create Thread
//
void* TqcOsCreateThread(void *threadMain, void *pThread)
{
    pthread_t ThreadID;

    pthread_create(&ThreadID, NULL, (pfnLinuxThreadDecl)threadMain, reinterpret_cast<void*>(pThread));
    return reinterpret_cast<void*>(ThreadID);
}

//
// Wait for thread exit.
//
bool TqcCloseThread(PTHREDID ThreadID)
{
    if (NULL == ThreadID)
    {
        return false;
    }

    pthread_t *pThreadID = reinterpret_cast<pthread_t*>(ThreadID);
    // sleep(3);
    pthread_join((*pThreadID), NULL);
    return true;
}
// Sleep
void TqcOsSleep(int millisecond)
{
    usleep(1000 * millisecond);
}

// Create Mutex
LockerHandle TqcOsCreateMutex()
{
    pthread_mutex_t *mutex = new pthread_mutex_t;

    if (pthread_mutex_init(mutex, NULL) != 0)
        return 0;

    return (LockerHandle)mutex;
}

// Delete Mutex
void TqcOsDeleteMutex(LockerHandle handle)
{
    if (NULL == handle)
    {
        return;
    }

    pthread_mutex_destroy(reinterpret_cast<pthread_mutex_t*>(handle));
    delete reinterpret_cast<pthread_mutex_t*>(handle);
}

//
// Request mutex
//
bool TqcOsAcquireMutex(LockerHandle handle)
{
    if (NULL == handle)
    {
        return false;
    }

    pthread_mutex_lock(reinterpret_cast<pthread_mutex_t*>(handle));
    return true;
}

//
// Release mutex
//
void TqcOsReleaseMutex(LockerHandle handle)
{
    if (NULL == handle)
    {
        return;
    }

    pthread_mutex_unlock(reinterpret_cast<pthread_mutex_t*>(handle));
}

//
// Get current system time
//
unsigned int TqcOsGetMicroSeconds(void)
{
    unsigned int   time;
    struct timeval tv;

    /* Return the time of day in milliseconds. */
    gettimeofday(&tv, 0);
    time = (tv.tv_sec * 1000000) + tv.tv_usec;

    return time;
}

//
// Create screen capture.
//
// bool TqcOsCreateCapScreen(CapScreen *stCapScreen)
// {
//     XInitThreads();
//     Window *pWin = new Window;

//     stCapScreen->m_pFromHandle = reinterpret_cast<void*>(XOpenDisplay(NULL));
//     *pWin                      = (Window)RootWindow((reinterpret_cast<Display*>(stCapScreen->m_pFromHandle)), 0);
//     stCapScreen->m_pToHandle   = reinterpret_cast<void*>(pWin);

//     if (NULL == stCapScreen->m_pFromHandle || NULL == stCapScreen->m_pToHandle)
//     {
//         return false;
//     }
//     else
//     {
//         return true;
//     }
// }

// bool TqcOsReleaseCapScreen(CapScreen *stCapScreen)
// {
//     if (NULL != (stCapScreen->m_pFromHandle))
//     {
//         XCloseDisplay(reinterpret_cast<Display*>(stCapScreen->m_pFromHandle));
//     }

//     if (NULL != (stCapScreen->m_pToHandle))
//     {
//         delete (reinterpret_cast<Window*>(stCapScreen->m_pToHandle));
//         stCapScreen->m_pToHandle = NULL;
//     }

//     return true;
// }

// bool TqcOsCapScreen(const CapScreen stCapScreen, const int nColBegin, const int nRowBegin,
//                     const int nScissorWidth, const int nScissorHeight, unsigned char *pImageData,
//                     PixelFormat &ePixelFormat)
// {
//     if (NULL == pImageData || NULL == stCapScreen.m_pFromHandle || NULL == stCapScreen.m_pToHandle)
//     {
//         return false;
//     }

//     Window *pWin = reinterpret_cast<Window*>(stCapScreen.m_pToHandle);
//     XImage *img;
//     img = XGetImage(reinterpret_cast<Display*>(stCapScreen.m_pFromHandle), *pWin, nColBegin, nRowBegin,
//                     nScissorWidth, nScissorHeight, ~0, ZPixmap);
//     int nWindowWidth  = img->width;
//     int nWindowHeight = img->height;

//     memcpy(pImageData, img->data, nWindowWidth * nWindowHeight * 4);
//     XDestroyImage(img);
//     ePixelFormat = BGRA_8888;
//     return true;
// }

bool TqcOsReadFileList(std::string strPathName, std::vector<std::string> *poVecFileName)
{
    if (poVecFileName == NULL)
    {
        return false;
    }

    if (strPathName.empty())
    {
        return false;
    }

    DIR           *dir;
    struct dirent *ptr = NULL;
    char          base[1000];

    if ((dir = opendir(strPathName.c_str())) == NULL)
    {
        perror("Open dir error...");
        return false;
    }

    char          szName[256] = {0};
    struct dirent stEntry;

    while ((!readdir_r(dir, &stEntry, &ptr)) && (ptr != NULL))
    {
        if (strcmp(ptr->d_name, ".") == 0 || strcmp(ptr->d_name, "..") == 0) /// current dir OR parrent dir
            continue;
        else if (ptr->d_type == 8)    /// file
        {
            SNPRINTF(szName, sizeof(szName), "%s/%s", strPathName.c_str(), ptr->d_name);
            // for check
            printf("d_name:%s/%s\n", strPathName.c_str(), ptr->d_name);
            poVecFileName->push_back(std::string(szName));
            memset(szName,  0, sizeof(szName));
        }
    }

    closedir(dir);
    return true;
}

bool TqcOsStartProcess(const char *strWorkPath, const char *args)
{
    int childPid = fork();

    if (childPid == -1)
    {
        return false;
    }

    if (childPid != 0)
    {
        return true;
    }
    else
    {
        char buf[256];

        memset(buf, 0, 256);
        memcpy(buf, args, strlen(args));
        std::vector<std::string> resultVec;
        char                     *outerPtr = NULL;
        char                     *tmpStr   = strtok_r(buf, " ", &outerPtr);

        while (tmpStr != NULL)
        {
            resultVec.push_back(std::string(tmpStr));
            tmpStr = strtok_r(NULL, " ", &outerPtr);
        }

        int  size   = resultVec.size();
        char **argv = reinterpret_cast<char**>(malloc(sizeof(tmpStr) * (size + 1)));
        if (argv == NULL)
            return false;

        for (int i = 0; i < size; i++)
        {
            argv[i] = reinterpret_cast<char*>(malloc(256));
            memset(argv[i], 0, 256);
            memcpy(argv[i], resultVec[i].c_str(), strlen(resultVec[i].c_str()));
            // argv[i] = resultVec[i].c_str();
            printf("%s\n", argv[i]);
        }

        argv[size] = NULL;

        int err = execv(argv[0], argv);
        free(argv);
        abort();
    }

    return false;
}

bool  TqcOsGetCWD(char *buff, int nMaxLen)
{
    if (buff == NULL || nMaxLen <= 0)
    {
        return false;
    }

    getcwd(buff, nMaxLen);
    return true;
}


bool IsFileExist(const char *pszFileName)
{
    if (access(pszFileName, F_OK) == 0)
    {
        return true;
    }
    return false;
}
#endif /* LINUX */
