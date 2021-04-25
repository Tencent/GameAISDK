/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/Pool.h"
#include "Comm/Utils/TqcLog.h"

//
// Memory pool.
//
CMemoryPool::CMemoryPool() {
    int           nTmp  = 0;
    unsigned int  uTmp  = 0;
    unsigned char ucTmp = 0;
    char          cTmp  = 0;
    bool          bTmp  = false;

    m_pIntPool = new boost::pool<>(sizeof(nTmp));
    if (m_pIntPool == NULL) {
        LOGE("Cannot create int pool");
    }

    m_pBoolPool = new boost::pool<>(sizeof(bTmp));
    if (m_pBoolPool == NULL) {
        LOGE("Cannot create bool pool");
    }

    m_pUIntPool = new boost::pool<>(sizeof(uTmp));
    if (m_pUIntPool == NULL) {
        LOGE("Cannot create unsigned int pool");
    }

    m_pUCharPool = new boost::pool<>(sizeof(ucTmp));
    if (m_pUCharPool == NULL) {
        LOGE("Cannot create unsigned char pool");
    }

    m_pCharPool = new boost::pool<>(sizeof(cTmp));
    if (m_pCharPool == NULL) {
        LOGE("Cannot create char pool");
    }
}

CMemoryPool::~CMemoryPool() {
    if (m_pIntPool) {
        delete m_pIntPool;
    }

    if (m_pUIntPool) {
        delete m_pUIntPool;
    }

    if (m_pCharPool) {
        delete m_pCharPool;
    }

    if (m_pUCharPool) {
        delete m_pUCharPool;
    }

    if (m_pBoolPool) {
        delete m_pBoolPool;
    }
}

//
// Allocate memory for charater type.
//
char* CMemoryPool::AllocateChar(int nSize) {
    if (!m_pCharPool)
        return NULL;

    m_charPoolLock.Lock();
    char *pChar = reinterpret_cast<char*>(m_pCharPool->ordered_malloc(nSize));
    m_charPoolLock.UnLock();

    return pChar;
}

//
// Allocate memory for unsigned charater type.
//
unsigned char* CMemoryPool::AllocateUChar(int nSize) {
    if (!m_pUCharPool)
        return NULL;

    m_ucharPoolLock.Lock();
    unsigned char *pUChar = reinterpret_cast<unsigned char*>(m_pUCharPool->ordered_malloc(nSize));
    m_ucharPoolLock.UnLock();

    return pUChar;
}

//
// Allocate memory for integer type.
//
int* CMemoryPool::AllocateInt(int nSize) {
    if (!m_pIntPool)
        return NULL;

    m_intPoolLock.Lock();
    int *pInt = reinterpret_cast<int*>(m_pIntPool->ordered_malloc(nSize));
    m_intPoolLock.UnLock();

    return pInt;
}

//
// Allocate memory for unsigned integer type.
//
unsigned int* CMemoryPool::AllocateUInt(int nSize) {
    if (!m_pUIntPool)
        return NULL;

    m_uintPoolLock.Lock();
    unsigned int *pUInt = reinterpret_cast<unsigned int*>(m_pUIntPool->ordered_malloc(nSize));
    m_uintPoolLock.UnLock();

    return pUInt;
}

//
// Allocate memory for bool type.
//
bool* CMemoryPool::AllocateBool(int nSize) {
    if (!m_pBoolPool)
        return NULL;

    m_boolPoolLock.Lock();
    bool *pBool = reinterpret_cast<bool*>(m_pBoolPool->ordered_malloc(nSize));
    m_boolPoolLock.UnLock();

    return pBool;
}

//
// Allocate memory for game type.
//
// stGameMsg* CMemoryPool::AllocateGameMsg()
// {
//     m_msgPoolLock.Lock();
//     stGameMsg *pMsg = reinterpret_cast<stGameMsg*>(m_msgPool.construct());
//     m_msgPoolLock.UnLock();

//     return pMsg;
// }

//
// Allocate memory interface.
//
bool* AllocateBoolFromPool(int nSize) {
    return g_pMemoryPool->AllocateBool(nSize);
}

//
// Allocate memory interface.
//
int* AllocateIntFromPool(int nSize) {
    return g_pMemoryPool->AllocateInt(nSize);
}

//
// Allocate memory interface.
//
unsigned int* AllocateUIntFromPool(int nSize) {
    return g_pMemoryPool->AllocateUInt(nSize);
}

//
// Allocate memory interface.
//
char* AllocateCharFromPool(int nSize) {
    return g_pMemoryPool->AllocateChar(nSize);
}

//
// Allocate memory interface.
//
unsigned char* AllocateUCharFromPool(int nSize) {
    return g_pMemoryPool->AllocateUChar(nSize);
}

//
// Allocate memory interface.
//
// stGameMsg* AllocateGameMsgFromPool()
// {
//     return g_pMemoryPool->AllocateGameMsg();
// }
