/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include <iostream>

#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskResult.h"

// =========================================================================
// CTaskResult 成员函数的实现
// =========================================================================

CTaskResult::CTaskResult() {
    m_pRegRst = NULL;
    m_eType = TYPE_BEGIN;
    m_nTaskID = -1;
}

CTaskResult::~CTaskResult() {
}

// 释放资源
// 使用内存池的FreePoolMemory接口
void CTaskResult::Release() {
    if (m_pRegRst != NULL) {
        CGameRegMemPool::getInstance()->FreePoolMemory<IRegResult>(m_pRegRst);
        m_pRegRst = NULL;
    }
}

IRegResult* CTaskResult::GetInstance(EREGTYPE eType) {
    m_eType = eType;

    switch (eType) {
    case TYPE_STUCKREG:
    {
        // 创建stuck结果对象
        CreateStuckRst();
        break;
    }

    case TYPE_FIXOBJREG:
    {
        // 创建fixobj结果对象
        CreateFixObjRst();
        break;
    }

    case TYPE_PIXREG:
    {
        // 创建pix结果对象
        CreatePixRst();
        break;
    }

    case TYPE_NUMBER:
    {
        // 创建number结果对象
        CreateNumberRst();
        break;
    }

    case TYPE_DEFORMOBJ:
    {
        // 创建deform结果对象
        CreateDeformRst();
        break;
    }

    case TYPE_FIXBLOOD:
    {
        // 创建fixblood结果对象
        CreateFixBloodRst();
        break;
    }

    case TYPE_REFER_LOCATION:
    {
        // 创建location结果对象
        CreateLocationRst();
        break;
    }

    case TYPE_REFER_BLOODREG:
    {
        // 创建bloodreg结果对象
        CreateBloodRegRst();
        break;
    }

    case TYPE_KINGGLORYBLOOD:
    {
        // 创建kinggloryblood结果对象
        CreateKingGloryBloodRst();
        break;
    }

    case TYPE_MAPREG:
    {
        // 创建mapreg结果对象
        CreateMapRegRst();
        break;
    }

    case TYPE_MAPDIRECTIONREG:
    {
        // 创建mapdirectionreg结果对象
        CreateMapDirectionRegRst();
        break;
    }

    case TYPE_MULTCOLORVAR:
    {
        // 创建multcolorvarreg结果对象
        CreateMultColorVarRegRst();
        break;
    }

    case TYPE_SHOOTBLOOD:
    {
        // 创建shootblood结果对象
        CreateShootBloodRegRst();
        break;
    }

    case TYPE_SHOOTHURT:
    {
        // 创建shoothurt结果对象
        CreateShootHurtRegRst();
        break;
    }

    default:
    {
        LOGE("invalid type %d", eType);
        break;
    }
    }

    return m_pRegRst;
}

// ================================================================================================
// 以下内存分配均为内存池分配
// 使用AllocPoolMemory接口
// ================================================================================================

void CTaskResult::CreateShootBloodRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CShootGameBloodRegResult>();
    }
}

void CTaskResult::CreateShootHurtRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CShootGameHurtRegResult>();
    }
}

void CTaskResult::CreateMultColorVarRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CMultColorVarRegResult>();
    }
}

void CTaskResult::CreateMapDirectionRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CMapDirectionRegResult>();
    }
}

void CTaskResult::CreateMapRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CMapRegResult>();
    }
}

void CTaskResult::CreateKingGloryBloodRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CKingGloryBloodRegResult>();
    }
}

void CTaskResult::CreateFixBloodRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CFixBloodRegResult>();
    }
}

void CTaskResult::CreateLocationRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CLocationRegResult>();
    }
}

void CTaskResult::CreateBloodRegRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CBloodLengthRegResult>();
    }
}

void CTaskResult::CreatePixRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CPixRegResult>();
    }
}

void CTaskResult::CreateFixObjRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CFixObjRegResult>();
    }
}

void CTaskResult::CreateStuckRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CStuckRegResult>();
    }
}

void CTaskResult::CreateDeformRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CDeformObjRegResult>();
    }
}

void CTaskResult::CreateNumberRst() {
    if (NULL == m_pRegRst) {
        m_pRegRst = CGameRegMemPool::getInstance()->AllocPoolMemory<CNumRegResult>();
    }
}

void CTaskResult::SetType(EREGTYPE eType) {
    m_eType = eType;
}

EREGTYPE CTaskResult::GetType() {
    return m_eType;
}

void CTaskResult::SetTaskID(int nTaskID) {
    m_nTaskID = nTaskID;
}

int CTaskResult::GetTaskID() {
    return m_nTaskID;
}
