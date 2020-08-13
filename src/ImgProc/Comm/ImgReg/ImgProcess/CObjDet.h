/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef OBJ_DET_H_
#define OBJ_DET_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/IImgProc.h"

// **************************************************************************************
//          CObjDetParam Class Define
// **************************************************************************************

class CObjDetParam : public IImgProcParam
{
public:
    CObjDetParam() {}
    virtual ~CObjDetParam() {}
};

// **************************************************************************************
//          CObjDetData Class Define
// **************************************************************************************

class CObjDetData : public IImgProcData
{
public:
    CObjDetData() {}
    virtual ~CObjDetData() {}
};

// **************************************************************************************
//          CObjDetResult Class Define
// **************************************************************************************

class CObjDetResult : public IImgProcResult
{
public:
    CObjDetResult() {}
    virtual ~CObjDetResult() {}

public:
    std::vector<tagBBox> m_oVecBBoxes;
};

// **************************************************************************************
//          IObjDetFactory Class Define
// **************************************************************************************

class IObjDetFactory : public IImgProcFactory
{
public:
    IObjDetFactory() {}
    virtual ~IObjDetFactory() {}

    virtual IImgProc* CreateImgProc() = 0;
};

// **************************************************************************************
//          CObjDet Class Define
// **************************************************************************************

class CObjDet : public IImgProc
{
public:
    CObjDet();
    ~CObjDet();

protected:
    int CheckPointer(IImgProcData *pData, IImgProcResult *pResult);
    int SetROI(CObjDetData *pD, cv::Rect *pROI);
    int SetResult(const cv::Rect &oROI, const std::vector<tagBBox> oVecBBoxes, CObjDetResult *pR);
};

#endif /* OBJ_DET_H_ */
