/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include <iostream>

#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskContext.h"

// extern LockFree::LockFreeQueue<CTaskResult> g_oTaskResultQueue;
extern ThreadSafeQueue<CTaskResult> g_oTaskResultQueue;
TaskContext::TaskContext()
{
    m_eTaskType              = TYPE_GAME;
    m_nLevel                 = -1;
    m_nOverload              = -1;
    m_stState.eTaskExecState = TASK_STATE_RUNNING;
    m_stState.bState         = true;
    m_pRecognizer            = NULL;
    m_bSendResult            = false;
}

TaskContext::~TaskContext()
{}

CTaskParam* TaskContext::GetParams()
{
    return &m_stParms;
}

IRecognizer*  TaskContext::GetRecognizer()
{
    return m_pRecognizer;
}

tagTaskState TaskContext::GetState()
{
    return m_stState;
}

int TaskContext::GetLevel()
{
    return m_nLevel;
}

int TaskContext::GetOverload()
{
    return m_nOverload;
}

void TaskContext::SetTaskType(ETaskType eTaskType)
{
    m_eTaskType = eTaskType;
}

ETaskType TaskContext::GetTaskType()
{
    return m_eTaskType;
}

bool TaskContext::CreateRecognizer(int nTaskID)
{
    switch (m_stParms.GetType())
    {
    // 创建fixobj识别器对象
    case TYPE_FIXOBJREG:
    {
        m_pRecognizer = new CFixObjReg();
        LOGI("create fixObj reg");
        break;
    }

    // 创建pix识别器对象
    case TYPE_PIXREG:
    {
        m_pRecognizer = new CPixReg();
        LOGI("create Pix reg");
        break;
    }

    // 创建stuck识别器对象
    case TYPE_STUCKREG:
    {
        m_pRecognizer = new CStuckReg();
        LOGI("create Stuck reg");
        break;
    }

    // 创建number识别器对象
    case TYPE_NUMBER:
    {
        m_pRecognizer = new CNumReg();
        LOGI("create Number reg");
        break;
    }

    // 创建deform识别器对象
    case TYPE_DEFORMOBJ:
    {
        m_pRecognizer = new CDeformObjReg();
        LOGI("create DeformObj reg");
        break;
    }

    // 创建fixblood识别器对象
    case TYPE_FIXBLOOD:
    {
        m_pRecognizer = new CFixBloodReg();
        LOGI("create FixBlood reg");
        break;
    }

    // 创建kinggloryblood识别器对象
    case TYPE_KINGGLORYBLOOD:
    {
        m_pRecognizer = new CKingGloryBloodReg();
        LOGI("create KingGloryBlood reg");
        break;
    }

    // 创建mapreg识别器对象
    case TYPE_MAPREG:
    {
        m_pRecognizer = new CMapReg();
        LOGI("create MakReg reg");
        break;
    }

    // 创建mapdirectionreg识别器对象
    case TYPE_MAPDIRECTIONREG:
    {
        m_pRecognizer = new CMapDirectionReg();
        LOGI("create MapDirectionReg reg");
        break;
    }

    // 创建multcolorvarreg识别器对象
    case TYPE_MULTCOLORVAR:
    {
        m_pRecognizer = new CMultColorVarReg();
        LOGI("create MultColorVar reg");
        break;
    }

    // 创建shootgameblood识别器对象
    case TYPE_SHOOTBLOOD:
    {
        m_pRecognizer = new CShootGameBloodReg();
        LOGI("create ShootGameBlood reg");
        break;
    }

    // 创建shootgamehurt识别器对象
    case TYPE_SHOOTHURT:
    {
        m_pRecognizer = new CShootGameHurtReg();
        LOGI("create ShootGameHurt reg");
        break;
    }

    // 创建locationreg识别器对象
    case TYPE_REFER_LOCATION:
    {
        m_pRecognizer = new CLocationReg();
        LOGI("create location reg");
        break;
    }

    // 创建referbloodreg识别器对象
    case TYPE_REFER_BLOODREG:
    {
        m_pRecognizer = new CBloodLengthReg();
        LOGI("create bloodlen reg");
        break;
    }

    default:
    {
        LOGW("type %d is invalid, please check", m_stParms.GetType());
        break;
    }
    }

    // 初始化识别器
    if (m_pRecognizer != NULL)
    {
        IRegParam *pRegParam = m_stParms.GetInstance(m_stParms.GetType());
        pRegParam->m_nTaskID = nTaskID;
        int nRst = m_pRecognizer->Initialize(pRegParam);
        if (1 == nRst)
        {
            return true;
        }
        else
        {
            return false;
        }
    }
    else
    {
        LOGE("new type %d failed", m_stParms.GetType());
        return false;
    }
}

void TaskContext::Release()
{
    // 释放资源
    ReleaseRecognizer();
    m_stParms.Release();
}

void TaskContext::ReleaseRecognizer()
{
    if (m_pRecognizer != NULL)
    {
        m_pRecognizer->Release();
        delete m_pRecognizer;
        m_pRecognizer = NULL;
    }
    else
    {
        LOGW("recognizer is NULL");
    }
}

void TaskContext::SetStateFirst(ETaskExecState eState)
{
    m_stState.eTaskExecState = eState;
}

void TaskContext::SetStateSecond(bool bState)
{
    m_stState.bState = bState;
}

void TaskContext::SetLevel(int nLevel)
{
    m_nLevel = nLevel;
}

void TaskContext::SetOverload(int nOverLoad)
{
    m_nOverload = nOverLoad;
}

void TaskContext::SetParam(const CTaskParam &stParms)
{
    m_stParms = stParms;
}

bool TaskContext::Process(tagRuntimeVar stRuntimeVar)
{
//    LOGI("exec process............... %d", stRuntimeVar.nFrameSeq);
    if (m_pRecognizer != NULL)
    {
        // 设置参数
        tagRegData stRegData;
        stRegData.nFrameIdx = stRuntimeVar.nFrameSeq;
        stRegData.oSrcImg   = stRuntimeVar.oSrcImage;

        CTaskResult oTaskResult;
        oTaskResult.SetTaskID(stRuntimeVar.nTaskID);
        IRegResult *pRegResult = oTaskResult.GetInstance(m_stParms.GetType());
//        printf("address:%p\n", pRegResult);
        if (pRegResult == NULL)
        {
            LOGW("get instance failed, FrameIdx: %d, taskID: %d", stRuntimeVar.nFrameSeq, stRuntimeVar.nTaskID);
            return false;
        }

        // 识别器执行检测
        int nRst = m_pRecognizer->Predict(stRegData, pRegResult);
        if (-1 == nRst)
        {
            pRegResult->m_nFrameIdx = stRuntimeVar.nFrameSeq;
            LOGE("predict failed, FrameIdx: %d, taskID: %d", stRuntimeVar.nFrameSeq, stRuntimeVar.nTaskID);
            // return false;
        }

        // 将结果push到线程安全队列
        g_oTaskResultQueue.Push(oTaskResult);
        LOGD("task finish, FrameIdx: %d, taskID: %d", stRuntimeVar.nFrameSeq, stRuntimeVar.nTaskID);
    }
    else
    {
        LOGW("recognizer is null, please check, taskID: %d", stRuntimeVar.nTaskID);
    }

//    LOGI("end process............... %d", stRuntimeVar.nFrameSeq);
    return true;
}
