/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <direct.h>
#include <io.h>
#include <stdio.h>
#include <stdlib.h>
#include <Windows.h>

#include "Comm/Os/TqcOs.h"


//
// Create thread
//
void* TqcOsCreateThread(void *threadMain, void *pThread)
{
    HANDLE ThreadID;

    ThreadID =
        CreateThread(NULL, 0, reinterpret_cast<LPTHREAD_START_ROUTINE>(threadMain), reinterpret_cast<void*>(pThread), 0,
                     NULL);
    return reinterpret_cast<void*>(ThreadID);
}

//
// Wait for thread exit.
//
bool TqcCloseThread(PTHREDID ThreadID)
{
    HANDLE pThreadID = (HANDLE)ThreadID;

    // sleep(3);
    WaitForSingleObject(pThreadID, INFINITE);
    return true;
}

//
// Sleep some milliseconds.
//
void TqcOsSleep(int millisecond)
{
    Sleep(millisecond);
}

//
// Create mutex.
//
LockerHandle TqcOsCreateMutex()
{
    CRITICAL_SECTION *sect = new CRITICAL_SECTION();

    ::InitializeCriticalSectionAndSpinCount(sect, 0);
    return (LockerHandle)sect;
}

//
// Delete mutex
//
void TqcOsDeleteMutex(LockerHandle handle)
{
    if (NULL == handle)
    {
        return;
    }

    ::DeleteCriticalSection(LPCRITICAL_SECTION(handle));
    delete reinterpret_cast<LPCRITICAL_SECTION>(handle);
    // delete handle;
}

//
// Acquire mutex
//
bool TqcOsAcquireMutex(LockerHandle handle)
{
    if (NULL == handle)
    {
        return false;
    }

    EnterCriticalSection(LPCRITICAL_SECTION(handle));
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

    LeaveCriticalSection(LPCRITICAL_SECTION(handle));
}

//
// Get current system time by microsecond.
//
unsigned int TqcOsGetMicroSeconds(void)
{
    LARGE_INTEGER t1;
    LARGE_INTEGER tc;
    unsigned int  time;

    QueryPerformanceFrequency(&tc);
    QueryPerformanceCounter(&t1);

    time = static_cast<unsigned int>((static_cast<double>(t1.QuadPart) / static_cast<double>(tc.QuadPart)) * 1000000);

    return time;
}

// bool TqcOsCreateCapScreen(CapScreen *stCapScreen)
// {
//     stCapScreen->m_pFromHandle = (HDC)CreateDC("DISPLAY", NULL, NULL, NULL);
//     stCapScreen->m_pToHandle   = (HDC)CreateCompatibleDC((HDC)(stCapScreen->m_pFromHandle));
//     if (NULL == stCapScreen->m_pFromHandle || NULL == stCapScreen->m_pToHandle)
//     {
//         return false;
//     }
//     else
//     {
//         return true;
//     }
// }

// bool TqcOsReleaseCapScreen(CapScreen *stCapScreene)
// {
//     if (NULL == stCapScreene->m_pFromHandle || stCapScreene->m_pToHandle)
//     {
//         return false;
//     }
//     else
//     {
//         DeleteDC((HDC)(stCapScreene->m_pFromHandle));
//         DeleteDC((HDC)(stCapScreene->m_pToHandle));
//         return true;
//     }
// }

// bool TqcOsCapScreen(const CapScreen stCapScreen, const int nColBegin, const int nRowBegin,
//                     const int nScissorWidth, const int nScissorHeight, unsigned char *pImageData,
//                     PixelFormat &ePixelFormat)
// {
//     if (NULL == stCapScreen.m_pFromHandle || NULL == stCapScreen.m_pToHandle)
//     {
//         return false;
//     }

//     if (NULL == pImageData)
//     {
//         return false;
//     }

//     HBITMAP hBmp    = CreateCompatibleBitmap((HDC)stCapScreen.m_pFromHandle, nScissorWidth, nScissorHeight);
//     HBITMAP hOld    = (HBITMAP)SelectObject((HDC)stCapScreen.m_pToHandle, hBmp);
//     BOOL    bResult = BitBlt((HDC)stCapScreen.m_pToHandle, 0, 0, nScissorWidth, nScissorHeight,
//                              (HDC)stCapScreen.m_pFromHandle, nColBegin, nRowBegin, SRCCOPY);
//     if (FALSE == bResult)
//     {
//         return false;
//     }

//     BITMAP bmp;
//     GetObject(hBmp, sizeof(BITMAP), &bmp);
//     int nChannels = bmp.bmBitsPixel == 1 ? 1 : bmp.bmBitsPixel / 8;
//     int nLen      = GetBitmapBits(hBmp, bmp.bmHeight * bmp.bmWidth * nChannels, pImageData);
//     DeleteObject(hOld);
//     DeleteObject(hBmp);
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

    poVecFileName->clear();
    std::string p;
    _finddata_t fileInfo;
    intptr_t    handle = _findfirst(p.assign(strPathName.c_str()).append("\\*").c_str(), &fileInfo);
    if (handle == -1L)
    {
        return false;
    }

    do
    {
        char szImageName[256] = { 0 };
        SNPRINTF(szImageName, sizeof(szImageName), "%s/%s", strPathName.c_str(), fileInfo.name);
        poVecFileName->push_back(std::string(szImageName));
    }
    while (_findnext(handle, &fileInfo) == 0);

    return true;
}

bool TqcOsStartProcess(const char *strWorkPath, const char *args)
{
    PROCESS_INFORMATION pi;
    STARTUPINFO         si;
    BOOL                bRes = FALSE;

    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));

    bRes = CreateProcess(NULL, (LPTSTR)(LPCTSTR)args, NULL, NULL, FALSE, CREATE_NEW_CONSOLE, NULL, (LPCSTR)strWorkPath,
                         &si, &pi);
    return static_cast<bool>(bRes);
}

bool  TqcOsGetCWD(char *buff, int nMaxLen)
{
    if (buff == NULL || nMaxLen <= 0)
    {
        return false;
    }

    char *pszBuff;
    pszBuff = getcwd(NULL, 0);
    if (NULL == pszBuff)
    {
        return false;
    }
    else
    {
        /* code */
        if (strlen(pszBuff) < nMaxLen)
        {
            memcpy(buff, pszBuff, strlen(pszBuff));
            free(pszBuff);
            return true;
        }
        else
        {
            free(pszBuff);
            return false;
        }
    }
}

bool IsFileExist(const char *pszFileName)
{
    if ((_access(pszFileName, 0)) != -1)
    {
        return true;
    }

    return false;
}
