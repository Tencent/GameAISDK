/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef COMN_BASE_REG_H_
#define COMN_BASE_REG_H_

#include "Comm/ImgReg/Recognizer/IRecognizer.h"

// **************************************************************************************
//          IComnBaseRegParam Class Define
// **************************************************************************************

class IComnBaseRegParam : public IRegParam
{
public:
    IComnBaseRegParam() {}
    virtual ~IComnBaseRegParam() {}
};

// **************************************************************************************
//          IComnBaseRegResult Class Define
// **************************************************************************************

class IComnBaseRegResult : public IRegResult
{
public:
    IComnBaseRegResult() {}
    virtual ~IComnBaseRegResult() {}
};

// **************************************************************************************
//          IComnBaseReg Class Define
// **************************************************************************************

class IComnBaseReg : public IRecognizer
{
public:
    IComnBaseReg() {}
    virtual ~IComnBaseReg() {}
};

#endif /* COMN_BASE_REG_H_ */
