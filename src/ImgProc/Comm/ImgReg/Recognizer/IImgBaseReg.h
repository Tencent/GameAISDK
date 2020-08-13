/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef IMG_BASE_REG_H_
#define IMG_BASE_REG_H_

#include "Comm/ImgReg/Recognizer/IRecognizer.h"

// **************************************************************************************
//          IImgBaseRegParam Class Define
// **************************************************************************************

class IImgBaseRegParam : public IRegParam
{
public:
    IImgBaseRegParam() {}
    virtual ~IImgBaseRegParam() {}
};

// **************************************************************************************
//          IImgBaseRegResult Class Define
// **************************************************************************************

class IImgBaseRegResult : public IRegResult
{
public:
    IImgBaseRegResult() {}
    virtual ~IImgBaseRegResult() {}
};

// **************************************************************************************
//          CImgBaseReg Class
// **************************************************************************************

class CImgBaseReg : public IRecognizer
{
public:
    CImgBaseReg() {}
    virtual ~CImgBaseReg() {}
};

#endif /* IMG_BASE_REG_H_ */
