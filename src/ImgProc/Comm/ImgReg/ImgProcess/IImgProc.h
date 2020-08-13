/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef IMG_PROC_H_
#define IMG_PROC_H_

#include "Comm/ImgReg/ImgProcess/ImgComn.h"

// **************************************************************************************
//          Parameter Class Define
// **************************************************************************************

class IImgProcParam
{
public:
    IImgProcParam()
    {
        m_nTaskID = -1;
        m_oROI = cv::Rect(-1, -1, -1, -1);
    }
    virtual ~IImgProcParam() {}

public:
    int m_nTaskID; // task ID
    cv::Rect m_oROI; // detection ROI
};

// **************************************************************************************
//          Data Class Define
// **************************************************************************************

class IImgProcData
{
public:
    IImgProcData()
    {
        m_oROI = cv::Rect(-1, -1, -1, -1);
    }
    virtual ~IImgProcData() {}

public:
    cv::Rect m_oROI; // detection ROI
    cv::Mat m_oSrcImg; // source image
};

// **************************************************************************************
//          Result Class Define
// **************************************************************************************

class IImgProcResult
{
public:
    IImgProcResult() {}
    virtual ~IImgProcResult() {}
};

// **************************************************************************************
//          IImgProc Class
// **************************************************************************************

class IImgProc
{
public:
    IImgProc()
    {
        m_nTaskID = -1;
        m_oROI = cv::Rect(-1, -1, -1, -1);
    }

    virtual ~IImgProc() {}

    virtual int Initialize(IImgProcParam *pParam) = 0;

    virtual int Predict(IImgProcData *pData, IImgProcResult *pResult) = 0;

    virtual int Release() = 0;

protected:
    int m_nTaskID; // task ID
    cv::Rect m_oROI; // detection ROI
};

// **************************************************************************************
//          IImgProcFactory Class
// **************************************************************************************

class IImgProcFactory
{
public:
    IImgProcFactory() {}
    virtual ~IImgProcFactory() {}

    virtual IImgProc* CreateImgProc() = 0;
};

#endif /* IMG_PROC_H_ */
