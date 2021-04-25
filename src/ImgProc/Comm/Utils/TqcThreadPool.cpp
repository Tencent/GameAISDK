/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#include "Comm/Utils/TqcThreadPool.h"

CDefaultTask::CDefaultTask() {
    m_pFunc = NULL;
}

CDefaultTask::~CDefaultTask() {
}

//
// set the task.
//
void CDefaultTask::SetFunc(void *func) {
    m_pFunc = func;
}

void* CDefaultTask::GetFunc() {
    return m_pFunc;
}

//
// sample code to show task setting.
//
void CDefaultTask::PushParam(int x) {
    tagParam param;

    param.param.x = x;
    param.type = FUNC_PARAM_INT;

    m_paramQueue.push(param);
}

//
// sample code to show task setting.
//
void CDefaultTask::PushParam(char x) {
    tagParam param;

    param.param.y = x;
    param.type = FUNC_PARAM_INT;

    m_paramQueue.push(param);
}

//
// sample code to show task setting.
//
tagParam CDefaultTask::PopParam() {
    tagParam param;

    if (m_paramQueue.size() == 0)
        return param;

    param = m_paramQueue.front();
    m_paramQueue.pop();

    return param;
}

int CDefaultTask::ParamCount() {
    return m_paramQueue.size();
}

void CDefaultTask::SetBindFunc(boost::function<void()> func) {
    m_bindFunc = func;
}

boost::function<void()> CDefaultTask::GetBindFunc() {
    return m_bindFunc;
}

CDefaultTaskList::CDefaultTaskList() {
}

CDefaultTaskList::~CDefaultTaskList() {
}

//
// Push one task to task queue.
//
void CDefaultTaskList::Push(CDefaultTask *task) {
    m_funcQueue.push(reinterpret_cast<void*>(task));
}

//
// Pop one task from task queue
//
CDefaultTask* CDefaultTaskList::Pop() {
    CDefaultTask *pTask = NULL;

    if (m_funcQueue.size() == 0)
        return NULL;

    pTask = reinterpret_cast<CDefaultTask*>(m_funcQueue.front());
    m_funcQueue.pop();

    return pTask;
}

//
// Get number of task in the queue.
//
int CDefaultTaskList::TaskCount() {
    return m_funcQueue.size();
}

CThreadPoolDispatch::CThreadPoolDispatch() {
}

CThreadPoolDispatch::~CThreadPoolDispatch() {
}

//
// Push task to FIFO queue.
//
void CThreadPoolDispatch::PushTaskToFIFO(CDefaultTask *pTask) {
    m_funcQueue.push(pTask);
}

//
// Push task to the queue by specified dispatch type.
// Now default queue is FIFO.
//
void CThreadPoolDispatch::PushDefaultTask(CDefaultTask *pTask, TaskDispatchType dispatchType) {
    switch (dispatchType) {
    case TASK_DISPATCH_FIFO:
        PushTaskToFIFO(pTask);
        break;

    default:
        break;
    }
}

//
// sample code to show task setting.
//
CDefaultTask* CThreadPoolDispatch::PopDefaultTask() {
    CDefaultTask *pTask = NULL;

    if (m_funcQueue.size() == 0)
        return NULL;

    pTask = reinterpret_cast<CDefaultTask*>(m_funcQueue.front());
    m_funcQueue.pop();

    return pTask;
}

//
// Push task to FIFO queue.
//
void CThreadPoolDispatch::PushTaskToFIFO(tagTask task) {
    m_taskQueue.push(task);
}

void CThreadPoolDispatch::PushTask(const tagTask &task, TaskDispatchType dispatchType) {
    switch (dispatchType) {
    case TASK_DISPATCH_FIFO:
        PushTaskToFIFO(task);
        break;

    default:
        break;
    }
}

tagTask CThreadPoolDispatch::PopTask() {
    tagTask task;

    if (m_taskQueue.size() == 0)
        return task;

    task = m_taskQueue.front();
    m_taskQueue.pop();

    return task;
}

CThreadPoolMgr::CThreadPoolMgr() {
    m_bShouldRelease = false;
    m_pThreadPool = NULL;
}

CThreadPoolMgr::~CThreadPoolMgr() {
}

bool CThreadPoolMgr::Initialize(int nThreadNum) {
    m_pThreadPool = new CThreadPool<CMultiThreadResult>(nThreadNum);
    if (m_pThreadPool == NULL) {
        LOGE("Allocation failed for thread pool.");
        return false;
    }

    m_bShouldRelease = true;
    return true;
}

bool CThreadPoolMgr::Release() {
    if (m_pThreadPool == NULL)
        return true;

    m_pThreadPool->WaitAllTask();
    m_pThreadPool->Release();
    delete m_pThreadPool;
    m_pThreadPool = NULL;
    return true;
}

void CThreadPoolMgr::Update(CDefaultTaskList *pList) {
    int taskNum = pList->TaskCount();

    for (int i = 0; i < taskNum; i++) {
        CDefaultTask *pTask = pList->Pop();

        if (pTask == NULL)
            break;

        m_threadPoolDispatch.PushDefaultTask(pTask);
    }

    for (int i = 0; i < taskNum; i++) {
        CDefaultTask *pTask = m_threadPoolDispatch.PopDefaultTask();

        boost::function<void()> bindFunc = pTask->GetBindFunc();
        m_pThreadPool->PushTask(bindFunc);

        pList->Push(pTask);
    }

    m_pThreadPool->StartTask();
    return;
}

void CThreadPoolMgr::Update(const std::vector<tagTask> &taskList) {
    int taskNum = taskList.size();

    for (int i = 0; i < taskNum; i++) {
        tagTask task = taskList[i];

        m_threadPoolDispatch.PushTask(task);
    }

    for (int i = 0; i < taskNum; i++) {
        tagTask task = m_threadPoolDispatch.PopTask();

        boost::function<void()> bindFunc = task.ofunc;
        m_pThreadPool->PushTask(bindFunc);
    }

    m_pThreadPool->StartTask();
    return;
}

void CThreadPoolMgr::WaitAllTaskFinish() {
    LOGD("wait all task finish");
    m_pThreadPool->WaitAllTask();
    LOGD("all task finished");
}
