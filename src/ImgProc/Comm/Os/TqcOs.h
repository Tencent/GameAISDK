/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TQC_OS_H_
#define TQC_OS_H_

#if defined(_WINDOWS) || defined(WIN32) || defined(WIN64) || defined(WINDOWS)
#include <direct.h>
#include <io.h>
#include <tchar.h>
#include <Time.h>
#include <windows.h>
#elif defined(__APPLE__)

#elif defined(ANDROID)

#else
// #include <X11/Xlib.h>
// #include <X11/Xutil.h>
// #include <unistd.h>
#endif

#include <string>
#include <vector>

#ifdef WINDOWS
#define SNPRINTF _snprintf
#else
#define SNPRINTF snprintf
#endif

enum PixelFormat
{
    /* Bytes: 0 1 2 3 (Low to high)*/
    RGBA_8888 = 306,  /*        R G B A */
    BGRA_8888 = 212,  /*        B G R A */
    RGBX_8888 = 305,  /*        R G B - */
    BGRX_8888 = 211,  /*        B G R - */

    /* Bytes: 0 1 2 (Low to high) */
    RGB_888 = 303,  /*        R G B */
    BGR_888 = 210,  /*        B G R */

    /* Bits: 15 11 5  0 (MSB to LSB) */
    RGB_565 = 209,  /*         R  G  B */
    BGR_565 = 302,  /*         B  G  R */

    /* Bits: 15 12 8 4 0 (MSB to LSB) */
    RGBA_4444 = 205,  /*         R  G B A */
    BGRA_4444 = 313,  /*         B  G R A */

    /* Bits: 15 14 10 5  0 (MSB to LSB) */
    ARGB_1555 = 208,  /*        A   R  G  B */

    L8 = 801          /* L8 bit */
};


typedef void*LockerHandle;
struct CapScreen
{
    void *m_pFromHandle;
    void *m_pToHandle;
};

typedef void*PTHREDID;

bool            TqcOsStartProcess(const char *processPath, const char *args);
void*           TqcOsCreateThread(void *threadMain, void *pThread);
bool            TqcCloseThread(PTHREDID ThreadID);
void            TqcOsSleep(int millisecond);
LockerHandle    TqcOsCreateMutex();
void            TqcOsDeleteMutex(LockerHandle handle);
bool            TqcOsAcquireMutex(LockerHandle handle);
void            TqcOsReleaseMutex(LockerHandle handle);
unsigned int    TqcOsGetMicroSeconds(void);
bool            TqcOsGetCWD(char *buff, int nMaxLen);

/*
   capture part of screen image
   example:
   CapScreen stCapScreen;
   bool bresult = TqcOsCreateCapScreen(&stCapScreen);
   if(bresult)
   {
    for(int i = 0; i < 100; i++)
    {
        Mat oImage; // Mat is a type of  OPenCV
        oImage.create(100, 100, CV_8UC4);
        PixelFormat ePixelFormat;
        bool bCapres = TqcOsCapScreen(stCapScreen, 0, 0, 100, 100, oImage.data,ePixelFormat);
        if(!bCapres)
        {
            break;
        }
    }
    TqcOsReleaseCapScreen(&stCapScreen);
   }
 */
// bool TqcOsCreateCapScreen(CapScreen *stCapScreen);
// bool TqcOsReleaseCapScreen(CapScreen *stCapScreene);
// bool TqcOsCapScreen(const CapScreen stCapScreen, const int nColBegin, const int nRowBegin,
//                     const int nScissorWidth, const int nScissorHeight, unsigned char *pImageData,
//                     PixelFormat &ePixelFormat);

bool TqcOsReadFileList(std::string strPathName, std::vector<std::string> *poVecFileName);

bool IsFileExist(const char *pszFileName);

#endif // TQC_OS_H_
