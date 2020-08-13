/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef OBJ_REG_H_
#define OBJ_REG_H_

#include "Comm/ImgReg/Recognizer/IComnBaseReg.h"

// **************************************************************************************
//          IObjRegParam Class Define
// **************************************************************************************

class IObjRegParam : public IComnBaseRegParam
{
public:
    IObjRegParam() {}
    virtual ~IObjRegParam() {}
};

// **************************************************************************************
//          IObjRegResult Class Define
// **************************************************************************************

class IObjRegResult : public IComnBaseRegResult
{
public:
    IObjRegResult() {}
    virtual ~IObjRegResult() {}
};

// **************************************************************************************
//          IObjReg Class Define
// **************************************************************************************

class IObjReg : public IComnBaseReg
{
public:
    IObjReg() {}
    virtual ~IObjReg() {}
};

#endif /* OBJ_REG_H_ */
