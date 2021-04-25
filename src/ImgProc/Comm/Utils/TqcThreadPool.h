/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef TQC_THREAD_POOL_H_
#define TQC_THREAD_POOL_H_

#pragma once

#include <stdio.h>
#include <queue>
#include <vector>

#include "boost/thread.hpp"
#include "Comm/Utils/TqcLock.h"
#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskDefine.h"


// number of threads.
#define TQC_DEFAULT_THREAD_NUM 8

class CMultiThreadResult {
  public:
    CMultiThreadResult() {
    }
    ~CMultiThreadResult() {
    }
};

//
// Thread pool manager
// GameReg uses this manager to create thread pool and
// dispatch task to multi threads.
//
template<typename Result>
class CThreadPool {
  public:
    inline explicit CThreadPool(int nThreadNum = TQC_DEFAULT_THREAD_NUM) {
        m_nNextIndex = 0;
        m_nMaxIndex = 0;
        m_nStepSize = 1;
        m_callPerIndex = boost::bind(&CThreadPool::CallPerIndexDefault, this);

        m_bRunning = true;
        m_nThreadNum = nThreadNum;  // number of workers of thread.

        // flag for synchronization between each worker.
        m_pIsDone = new bool[nThreadNum];
        m_pGotOne = new bool[nThreadNum];
        m_pWorkerThreads = new boost::thread[nThreadNum];

        if (m_pIsDone == NULL || m_pGotOne == NULL || m_pWorkerThreads == NULL) {
            LOGE("Cannot allocate resources for threads.");
            return;
        }

        // Initialize each worker to done state.
        for (int i = 0; i < m_nThreadNum; i++) {
            m_pIsDone[i] = true;
            m_pGotOne[i] = false;
            m_pWorkerThreads[i] = boost::thread(&CThreadPool::TaskWorker, this, i);
        }
    }

    ~CThreadPool() {
        m_bRunning = false;

        // before release thread pool, we should wait for all worker finish.
        // m_exMutex.lock();
        // m_todoSignal.notify_all();
        // m_exMutex.unlock();

        for (int i = 0; i < m_nThreadNum; i++)
            m_pWorkerThreads[i].join();

        if (m_pWorkerThreads != NULL) {
            delete[] m_pWorkerThreads;
        }

        if (m_pIsDone != NULL) {
            delete[] m_pIsDone;
        }

        if (m_pGotOne != NULL) {
            delete[] m_pGotOne;
        }

        LOGI("destroyed ThreadReduce\n");
    }

    inline void StartTask() {
        // go worker threads!
        for (int i = 0; i < m_nThreadNum; i++) {
            m_pIsDone[i] = false;
            m_pGotOne[i] = false;
        }

        // let them start!
        m_todoSignal.notify_all();
    }

    void Release() {
        // before release thread pool, we should wait for all worker finish.
        // m_exMutex.lock();
        m_todoSignal.notify_all();
        // m_exMutex.unlock();

        // for (int i = 0; i < m_nThreadNum; i++)
        // {
        //    m_pWorkerThreads[i].join();
        // }
    }

    inline void WaitAllTask() {
        boost::unique_lock<boost::mutex> lock(m_exMutex);

        // check if actually all are finished.
        bool allDone = true;

        for (int i = 0; i < m_nThreadNum; i++)
            allDone = allDone && m_pIsDone[i];

        lock.unlock();

        // all are finished! exit.
        if (allDone == true)
            return;

        // LOGI("reduce waiting for threads to finish\n");
        // wait for all worker threads to signal they are done.
        while (true) {
            // wait for at least one to finish
            // m_doneSignal.wait(lock);
            // LOGI("thread finished!\n");

            // check if actually all are finished.
            bool allDone = true;

            lock.lock();

            for (int i = 0; i < m_nThreadNum; i++)
                allDone = allDone && m_pIsDone[i];

            lock.unlock();

            TqcOsSleep(50);

            // all are finished! exit.
            if (allDone)
                break;
        }

        LOGI("All task finished.");
    }

    // Push task to wait queue.
    inline void PushTask(boost::function<void()> callPerIndex) {
        m_taskQueueLock.Lock();
        m_taskQueue.push(callPerIndex);
        m_taskQueueLock.UnLock();
    }

    inline void Reduce(boost::function<void(int, int, Result*, int)> callPerIndex, int first,
        int end, int m_nStepSize = 0) {
        memset(&m_stats, 0, sizeof(Result));

        if (m_pIsDone == NULL || m_pGotOne == NULL || m_pWorkerThreads == NULL) {
            LOGE("Cannot allocate resources for threads.");
            return;
        }

        if (m_nStepSize == 0)
            m_nStepSize = ((end - first) + m_nThreadNum - 1) / m_nThreadNum;

        boost::unique_lock<boost::mutex> lock(m_exMutex);

        // save
        m_callPerIndex = callPerIndex;
        m_nNextIndex = first;
        m_nMaxIndex = end;
        m_nStepSize = m_nStepSize;

        // go worker threads!
        for (int i = 0; i < m_nThreadNum; i++) {
            m_pIsDone[i] = false;
            m_pGotOne[i] = false;
        }

        // let them start!
        m_todoSignal.notify_all();

        // wait for all worker threads to signal they are done.
        while (true) {
            // wait for at least one to finish
            m_doneSignal.wait(lock);
            // LOGI("thread finished!\n");

            // check if actually all are finished.
            bool allDone = true;

            for (int i = 0; i < m_nThreadNum; i++)
                allDone = allDone && m_pIsDone[i];

            // all are finished! exit.
            if (allDone)
                break;
        }

        m_nNextIndex = 0;
        m_nMaxIndex = 0;
        m_callPerIndex = boost::bind(&CThreadPool::CallPerIndexDefault, this);
    }

  private:
    void CallPerIndexDefault() {
        LOGE("ERROR: should never be called....\n");
        assert(false);
    }

    // Get task from waiting queue to some worker.
    bool GetTask(boost::function<void()> &task) {
        bool bRes = false;

        m_taskQueueLock.Lock();
        if (m_taskQueue.size() > 0) {
            bRes = true;
            task = m_taskQueue.front();
            m_taskQueue.pop();
        }

        m_taskQueueLock.UnLock();

        return bRes;
    }

    void TaskWorker(int idx) {
        boost::unique_lock<boost::mutex> lock(m_exMutex);
        boost::function<void()>          task;

        while (m_bRunning) {
            // try to get something to do.
            bool bGotSomething = GetTask(task);

            // if got something: do it (unlock in the meantime)
            if (bGotSomething) {
                lock.unlock();

                assert(m_callPerIndex != 0);

                Result s;
                memset(&s, 0, sizeof(Result));

                task();

                m_pGotOne[idx] = true;
                lock.lock();
                m_stats = s;
            } else {
                m_pIsDone[idx] = true;
                lock.unlock();
                // m_doneSignal.notify_all();
                // m_todoSignal.wait(lock);
                TqcOsSleep(5);
                lock.lock();
            }
        }
    }

  public:
    Result m_stats;

  private:
    boost::thread *m_pWorkerThreads;
    bool          *m_pIsDone;
    bool          *m_pGotOne;
    int           m_nThreadNum;

    boost::mutex              m_exMutex;
    boost::condition_variable m_todoSignal;
    boost::condition_variable m_doneSignal;

    int  m_nNextIndex;
    int  m_nMaxIndex;
    int  m_nStepSize;
    bool m_bRunning;

    boost::function<void()>              m_callPerIndex;
    std::queue<boost::function<void()> > m_taskQueue;
    CLock                                m_taskQueueLock;
};

union FuncParam {
    int  x;
    char y;
};

enum FuncParamType {
    FUNC_PARAM_INT,
    FUNC_PARAM_CHAR,
    FUNC_PARAM_MAX
};

struct tagParam {
    FuncParam     param;
    FuncParamType type;

    tagParam() {
        param.x = 0;
        type = FUNC_PARAM_MAX;
    }
};

class CDefaultTask {
  public:
    CDefaultTask();
    ~CDefaultTask();

    void                    SetFunc(void *func);
    void*                   GetFunc();
    void                    PushParam(int x);
    void                    PushParam(char x);
    tagParam                PopParam();
    int                     ParamCount();
    void                    SetBindFunc(boost::function<void()> func);
    boost::function<void()> GetBindFunc();

  private:
    void                    *m_pFunc;
    std::queue<tagParam>    m_paramQueue;
    boost::function<void()> m_bindFunc;
};

class CDefaultTaskList {
  public:
    CDefaultTaskList();
    ~CDefaultTaskList();

    void Push(CDefaultTask *task);
    CDefaultTask* Pop();
    int TaskCount();

  private:
    std::queue<void*> m_funcQueue;
};

class CThreadPoolDispatch {
  public:
    CThreadPoolDispatch();
    ~CThreadPoolDispatch();

    enum TaskDispatchType {
        TASK_DISPATCH_FIFO,
        TASK_DISPATCH_MAX
    };

    CDefaultTask* PopDefaultTask();
    void PushDefaultTask(CDefaultTask *pTask, TaskDispatchType dispatchType = TASK_DISPATCH_FIFO);
    tagTask PopTask();
    void PushTask(const tagTask &task, TaskDispatchType dispatchType = TASK_DISPATCH_FIFO);

  private:
    void PushTaskToFIFO(CDefaultTask *pTask);
    void PushTaskToFIFO(tagTask task);

  private:
    std::queue<void*>   m_funcQueue;
    std::queue<tagTask> m_taskQueue;
};

class CThreadPoolMgr {
  public:
    CThreadPoolMgr();
    ~CThreadPoolMgr();

    bool Initialize(int nThreadNum = TQC_DEFAULT_THREAD_NUM);
    bool Release();
    void Update(CDefaultTaskList *pList);
    void Update(const std::vector<tagTask> &taskList);
    void WaitAllTaskFinish();
    bool GetSholdRelease() {
        return m_bShouldRelease;
    }

  private:
    CThreadPoolDispatch             m_threadPoolDispatch;
    CThreadPool<CMultiThreadResult> *m_pThreadPool;
    bool                            m_bShouldRelease;
};

#endif  // TQC_THREAD_POOL_H_
