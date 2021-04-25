/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_POOL_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_POOL_H_

#include <stdint.h>
#include <stdio.h>
#include <boost/pool/object_pool.hpp>
#include <boost/pool/pool.hpp>

#include "Comm/Utils/TqcLock.h"
#include "Comm/Utils/TSingleton.h"
#include "UI/Src/Communicate/DataComm.h"


class CMemoryPool : public TSingleton<CMemoryPool> {
  public:
    DECLARE_SINGLETON_CLASS(CMemoryPool);

    CMemoryPool();
    ~CMemoryPool();

    // Plain Old Data
    unsigned char*  AllocateUChar(int nSize);
    unsigned int*   AllocateUInt(int nSize);
    char*           AllocateChar(int nSize);
    int*            AllocateInt(int nSize);
    bool*           AllocateBool(int nSize);

  private:
    // Plain Old Data
    // Includes int/char/bool/unsigned int/unsigned char.
    boost::pool<> *m_pUCharPool;
    CLock         m_ucharPoolLock;

    boost::pool<> *m_pUIntPool;
    CLock         m_uintPoolLock;

    boost::pool<> *m_pCharPool;
    CLock         m_charPoolLock;

    boost::pool<> *m_pIntPool;
    CLock         m_intPoolLock;

    boost::pool<> *m_pBoolPool;
    CLock         m_boolPoolLock;

    // msg
    // boost::object_pool<stGameMsg> m_msgPool;
    CLock                         m_msgPoolLock;
};

#define g_pMemoryPool CMemoryPool::getInstance()

char*           AllocateCharFromPool(int nSize);
bool*           AllocateBoolFromPool(int nSize);
int*            AllocateIntFromPool(int nSize);
unsigned char*  AllocateUCharFromPool(int nSize);
unsigned int*   AllocateUIntFromPool(int nSize);
// stGameMsg*      AllocateGameMsgFromPool();

#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_POOL_H_
