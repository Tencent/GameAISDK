/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGCLS_H_
#define GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGCLS_H_

#include <vector>

#include "Comm/ImgReg/ImgProcess/IImgProc.h"

// **************************************************************************************
//          IImgClsParam Class
// **************************************************************************************

class IImgClsParam : public IImgProcParam {
  public:
    IImgClsParam() {}
    virtual ~IImgClsParam() {}
};

// **************************************************************************************
//          CImgClsData Class
// **************************************************************************************

class CImgClsData : public IImgProcData {
  public:
    CImgClsData() {}
    virtual ~CImgClsData() {}
};

// **************************************************************************************
//          CImgClsResult Class
// **************************************************************************************

class CImgClsResult : public IImgProcResult {
  public:
    CImgClsResult() {}
    virtual ~CImgClsResult() {}

  public:
    std::vector<tagBBox> m_oVecBBoxes;
};

// **************************************************************************************
//          IImgClsFactory Class
// **************************************************************************************

class IImgClsFactory : public IImgProcFactory {
  public:
    IImgClsFactory() {}
    virtual ~IImgClsFactory() {}

    virtual IImgProc* CreateImgProc() = 0;
};

// **************************************************************************************
//          IImgCls Class
// **************************************************************************************

class IImgCls : public IImgProc {
  public:
    IImgCls() {}
    virtual ~IImgCls() {}
};

#endif  // GAME_AI_SDK_IMGPROC_COMM_IMGREG_IMGPROCESS_IIMGCLS_H_
