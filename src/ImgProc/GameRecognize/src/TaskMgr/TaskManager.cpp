/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/IniConfig.h"
#include "Comm/Utils/TqcLog.h"
#include "GameRecognize/src/TaskMgr/TaskManager.h"


// extern LockFree::LockFreeQueue<CTaskResult> g_oTaskResultQueue;
extern ThreadSafeQueue<CTaskResult> g_oTaskResultQueue;
extern int                          g_nMaxResultSize;

CTaskManager::CTaskManager()
{
    m_bSendSDKTool     = false;
    m_bShouldRelease   = false;
    m_nSrcWidth        = 0;
    m_nSrcHeight       = 0;
    m_bShowSrcImage    = false;
    m_bShowResult      = false;
    m_nOutTimeMS       = INT_MAX;
    m_pThreadPoolMgr   = NULL;
    m_nLastTimeMS      = -1;
    m_nMaxResSize      = -1;
    m_bMultiResolution = true;
    m_oMapTaskCtx.clear();
}

CTaskManager::~CTaskManager()
{}

//  read and parser GAMEREG_PLATFORM_CFG config file
//  bSendSDKTool: Whether to send results to SDKTool
//  bMultiResolution: Whether to processing multi-resolution
bool CTaskManager::Initialize(CThreadPoolMgr *pThreadPoolMgr, bool bSendSDKTool, bool bMultiResolution)
{
    m_bSendSDKTool     = bSendSDKTool;
    m_bMultiResolution = bMultiResolution;
    if (NULL == pThreadPoolMgr)
    {
        LOGE("pThreadPoolMgr is NULL");
        return false;
    }

    m_pThreadPoolMgr = pThreadPoolMgr;

    CIniConfig oIniConfig;
    int        nRst = oIniConfig.loadFile(GAMEREG_PLATFORM_CFG);
    if (nRst != 0)
    {
        nRst = oIniConfig.loadFile(GAMEREG_PLATFORM_PRE_CFG);
        if (nRst != 0)
        {
            LOGE("load file %s and load file %s failed", GAMEREG_PLATFORM_CFG, GAMEREG_PLATFORM_PRE_CFG);
            return false;
        }
    }

    // the items [debug] :[imgshow],[resultshow], [maxResultQueueSize]
    // which in the old configuration(../cfg/platform/gameReg.ini) file are Discard
    // new items [DEBUG] : [ImgShow], [ResultShow] which in the
    // new configurationre(../cfg/platform/GameReg.ini) are Discard
    // move item [debug]: [maxResultQueueSize] from file ../cfg/platform/gameReg.ini
    // to file cfg/task/gameReg/GameRegMgr1.json [maxResultQueueSize]
    m_bShowSrcImage = oIniConfig.getPrivateBool("DEBUG", "ImgShow", false);
    if (false == m_bShowSrcImage)
    {
        m_bShowSrcImage = oIniConfig.getPrivateBool("debug", "imgshow", false);
    }

    // !!!! Attation: in tenc machine, there is no graphic interface, please set ResultShow as False
    m_bShowResult = oIniConfig.getPrivateBool("DEBUG", "ResultShow", false);
    if (false == m_bShowResult)
    {
        m_bShowResult = oIniConfig.getPrivateBool("debug", "resultshow", false);
    }

    // m_nMaxResSize = oIniConfig.getPrivateBool("debug", "maxResultQueueSize", 5);

    m_bShouldRelease = true;
    return true;
}

// obtain results of current frame and save it to  pFrameResult
bool CTaskManager::GetResult(tagFrameResult *pFrameResult, int nNeedFrameSeq, int nTimeOutMS)
{
    if (NULL == pFrameResult)
    {
        LOGE("pFrameResult is NULL");
        return false;
    }

    // 判断是否超时
    int nCurTimeMS;
    nCurTimeMS = CGameTime::getInstance()->GetCurMSecond();
    if (m_nOutTimeMS != INT_MAX)
    {
        // if waiting time is larger than nTimeOutMS, stop waiting, get the results which are arrived,
        // send the arrived results  to Agent. the later results are discarded.
        // set  m_nOutTimeMS as INT_MAX, which means  will set m_nOutTimeMS as 0(start statistics waiting time)
        // when GetResult() was called next time
        if (m_nOutTimeMS >= nTimeOutMS)
        {
            *pFrameResult = m_mpFrameResult[nNeedFrameSeq];
            LOGD("expect size: %d, size: %d", pFrameResult->nResNum, static_cast<int>(pFrameResult->mapTaskResult.size()));
            m_nOutTimeMS = INT_MAX;
            LOGW("out of time");
            return true;
        }
        else
        {
            // if waiting time is less than nTimeOutMS  go on waiting
            m_nOutTimeMS += (nCurTimeMS - m_nLastTimeMS);
            m_nLastTimeMS = nCurTimeMS;
        }
    }
    else
    {
        m_nLastTimeMS = nCurTimeMS;
        m_nOutTimeMS  = 0;
    }

    // 将全局队列中的任务结果pop出来，填入结果map
//    LOGI("Task Result Queue size is %d", g_oTaskResultQueue.GetLength());
    int         nFrameIdx;
    CTaskResult oTaskResult;

    while (!g_oTaskResultQueue.IsEmpty())
    {
        // pop task recongnize result from global variable
        // find the task index in m_mpFrameResult
        // save the task recongnize result in m_mpFrameResult
        g_oTaskResultQueue.TryPop(&oTaskResult);
        IRegResult *pRegResult = oTaskResult.GetInstance(oTaskResult.GetType());
        if (NULL == pRegResult)
        {
            LOGE("pRegResult is NULL");
            continue;
        }

        nFrameIdx = pRegResult->m_nFrameIdx;

        if (m_mpFrameResult.find(nFrameIdx) != m_mpFrameResult.end())
        {
            int nTaskID = oTaskResult.GetTaskID();
            m_mpFrameResult[nFrameIdx].mapTaskResult[nTaskID] = oTaskResult;
        }
        else
        {
            oTaskResult.Release();
        }
    }

    // 判断当前帧的所有任务结果是否返回
    tagFrameResult stTmpFrameResult = m_mpFrameResult[nNeedFrameSeq];
    if (stTmpFrameResult.mapTaskResult.size() == stTmpFrameResult.nResNum)
    {
        // get all task results of this frame,
        // set  m_nOutTimeMS as INT_MAX, which means  will set m_nOutTimeMS as 0(start statistics waiting time)
        // when GetResult() was called next time
        LOGD("expect size: %d, size: %d", stTmpFrameResult.nResNum, static_cast<int>(stTmpFrameResult.mapTaskResult.size()));
        *pFrameResult = stTmpFrameResult;
        m_nOutTimeMS  = INT_MAX;
        return true;
    }

    return false;
}

void CTaskManager::SetTestMode(bool bDebug, ETestMode eTestMode)
{
    if (bDebug && eTestMode == SDKTOOL_TEST)
    {
        m_bSendSDKTool = true;
    }
}

ESendTaskReportToMC CTaskManager::UpdateTaskInfo(const std::vector<CTaskMessage> *pVecTaskMsg)
{
    if (pVecTaskMsg == NULL)
    {
        LOGE("pVecTaskMsg is NULL");
        return SEND_NO;
    }

    if (pVecTaskMsg->empty())
    {
        LOGE("msg is empty");
        return SEND_NO;
    }

    // GameReg Process receieve task managers from Agent Process, Analyze the messages one by one
    ESendTaskReportToMC       eResCode;
    std::vector<CTaskMessage> oVecTaskMsg = *const_cast<std::vector<CTaskMessage>*>(pVecTaskMsg);

    for (size_t i = 0; i < oVecTaskMsg.size(); i++)
    {
        eResCode = UpdateOneMsg(&oVecTaskMsg[i]);
        if (eResCode == SEND_FALSE)
        {
            return SEND_FALSE;
        }
    }

    // deal task data(eg. task level et.)
    oTaskDataDeal.Update();
    return eResCode;
}

void CTaskManager::InitGameTaskState()
{
    // 遍历任务列表，根据refer任务来修改游戏任务的状态

    // If the current task is a reference task and status is active
    // set the object task state of current task as TASK_STATE_WAITING
    std::map<int, TaskContext>::iterator iter = m_oMapTaskCtx.begin();

    for (; iter != m_oMapTaskCtx.end(); ++iter)
    {
        if (iter->second.GetTaskType() == TYPE_REFER)
        {
            tagTaskState stTaskState = iter->second.GetState();
            if (stTaskState.IsActive())
            {
                int nObjTaskID = m_oMutiResMgr.GetObjTaskID(iter->first);
                if (m_oMapTaskCtx.find(nObjTaskID) == m_oMapTaskCtx.end())
                {
                    LOGW("Obj taskID of refer task is not in taskMap : %d", nObjTaskID);
                    continue;
                }

                m_oMapTaskCtx[nObjTaskID].SetStateFirst(TASK_STATE_WAITING);
            }
        }
    }
}

// receieve message and update recognizer
// get task results and update recognizer
int CTaskManager::Update(const std::vector<CTaskMessage> &oVecTaskMsg, const tagSrcImgInfo &stSrcImageInfo,
                         std::vector<tagTask> *pVecRst, \
                         tagFrameResult *pFrameResult, ESendTaskReportToMC *peSendTaskReportToMC)
{
    if (NULL == pVecRst)
    {
        LOGE("pVecRst is NULL");
        return -1;
    }

    if (NULL == pFrameResult)
    {
        LOGE("pFrameResult is NULL");
        return -1;
    }

    if (NULL == peSendTaskReportToMC)
    {
        LOGE("peSendTaskReportToMC is NULL");
        return -1;
    }

    int nResUpdate = 0;
    pVecRst->clear();
    pFrameResult->oFrame.release();
    *peSendTaskReportToMC = SEND_NO;

    // 如果收到任务相关消息，更新任务列表
    // receieve message from agent, update it
    if (!oVecTaskMsg.empty())
    {
        *peSendTaskReportToMC = UpdateTaskInfo(&oVecTaskMsg);
        nResUpdate            = 1;
    }

    // 如果帧序号队列不为空，说明结果还未返回，因此尝试获取结果
    // get task results
    if (!m_ResFrameSeqQueue.empty())
    {
        if (m_oMapTaskCtx.empty())
        {
            // only need source image, no recognize task
            *pFrameResult = m_mpFrameResult[m_ResFrameSeqQueue.front()];
            m_mpFrameResult.erase(m_ResFrameSeqQueue.front());
            m_ResFrameSeqQueue.pop();
        }
        else
        {
            // get task result and update task state(multi resolution)
            bool bFlag = GetResult(pFrameResult, m_ResFrameSeqQueue.front(), OUT_TIME);
            if (bFlag)
            {
                // proceed image is (1280, XXX), receieve image maybe not equal to it.
                // so there is a need to transfer  coordinate result from processed image to receieve image
                TransCoor(pFrameResult);

                if (m_bShowResult || m_bSendSDKTool)
                {
                    ShowResult(pFrameResult);
                }

                // 根据结果更新refer任务状态、以及游戏任务的参数和状态
                if (m_bMultiResolution)
                {
                    m_oMutiResMgr.UpdateGameTask(&m_oMapTaskCtx, *pFrameResult);
                }

                LOGI("map size:%d", static_cast<int>(m_mpFrameResult.size()));
                m_mpFrameResult.erase(m_ResFrameSeqQueue.front());
                m_ResFrameSeqQueue.pop();
                nResUpdate = 1;
            }
        }
    }

    // 如果收到图像帧且帧队列的大小小于g_nMaxResultSize，则获取线程池用到的oVecRst参数
    if (!stSrcImageInfo.oSrcImage.empty() && m_ResFrameSeqQueue.size() < g_nMaxResultSize)
    {
        if (!m_oMapTaskCtx.empty())
        {
            LOGD("recv a frame: %d", static_cast<int>(stSrcImageInfo.uFrameSeq));
            m_nSrcWidth  = stSrcImageInfo.oSrcImage.cols;
            m_nSrcHeight = stSrcImageInfo.oSrcImage.rows;
            // 绑定线程运行时需要用到的参数
            tagRuntimeVar stRuntimeVar;
            if (m_nSrcWidth < m_nSrcHeight)
            {
                // resize source image to (XXX, 1280)
                cv::resize(stSrcImageInfo.oSrcImage, stRuntimeVar.oSrcImage, \
                           cv::Size(static_cast<int>(STANDARD_LONG_EDGE * 1.0 / m_nSrcHeight * m_nSrcWidth), STANDARD_LONG_EDGE));
            }
            else
            {
                // resize source image to (1280, XXX)
                cv::resize(stSrcImageInfo.oSrcImage, stRuntimeVar.oSrcImage, \
                           cv::Size(STANDARD_LONG_EDGE, static_cast<int>(STANDARD_LONG_EDGE * 1.0 / m_nSrcWidth * m_nSrcHeight)));
            }

            stRuntimeVar.nFrameSeq    = stSrcImageInfo.uFrameSeq;
            stRuntimeVar.nDeviceIndex = stSrcImageInfo.uDeviceIndex;

            // get active task vector
            *pVecRst = GetActiveTask(stSrcImageInfo.uFrameSeq, stRuntimeVar);
            // LOGI("pVecRst size: %d", static_cast<int>(pVecRst->size()));
        }

        // 如果可执行的任务不为空，则向结果队列中插入一项
        m_ResFrameSeqQueue.push(stSrcImageInfo.uFrameSeq);
        tagFrameResult stFrameResult;
        stFrameResult.oFrame                      = stSrcImageInfo.oSrcImage;
        stFrameResult.nframeSeq                   = stSrcImageInfo.uFrameSeq;
        stFrameResult.ndeviceIndex                = stSrcImageInfo.uDeviceIndex;
        stFrameResult.strJsonData                 = stSrcImageInfo.strJsonData;
        stFrameResult.nResNum                     = GetNumActiveCtx();
        m_mpFrameResult[stSrcImageInfo.uFrameSeq] = stFrameResult;
        nResUpdate                                = 1;
    }

    return nResUpdate;
}

ESendTaskReportToMC CTaskManager::UpdateOneMsg(CTaskMessage *pMsg)
{
    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return SEND_NO;
    }

    unsigned int uCmdID = pMsg->GetMsgType();

    if (uCmdID <= MSG_RECV_ID_START || uCmdID >= MSG_RECV_ID_Max)
    {
        LOGE("recv invalid taskID %d", static_cast<int>(uCmdID));
        return SEND_NO;
    }

    tagCmdMsg *pCmdMsg = pMsg->GetInstance((EAgentMsgID)uCmdID);

    // receieve and process one of messages which in [MSG_RECV_GROUP_ID, MSG_RECV_TASK_FLAG, MSG_RECV_ADD_TASK,
    // MSG_RECV_DEL_TASK, MSG_RECV_CHG_TASK, MSG_RECV_CONF_TASK] and process it
    switch (uCmdID)
    {
    // process message MSG_RECV_GROUP_ID
    case  MSG_RECV_GROUP_ID:
        // before process a list task in group message, need to wait all previous tasks finish
        m_pThreadPoolMgr->WaitAllTaskFinish();
        LOGI("process group msg");
        if (!ProcessGroupMsg(pCmdMsg))
        {
            ReleaseGameTaskReger();
            LOGE("process group msg failed");
            return SEND_FALSE;
        }

        break;

    // process message MSG_RECV_TASK_FLAG
    case MSG_RECV_TASK_FLAG:
        LOGI("process task flag msg");
        if (!ProcessTaskFlag(pCmdMsg))
        {
            LOGE("process task flag msg failed");
            return SEND_NO;
        }

        break;

    // process message MSG_RECV_ADD_TASK
    case MSG_RECV_ADD_TASK:
        LOGI("process add task msg");
        if (!ProcessAddTask(pCmdMsg))
        {
            LOGE("process task add msg failed");
            return SEND_NO;
        }

        break;

    // process message MSG_RECV_DEL_TASK
    case MSG_RECV_DEL_TASK:
        m_pThreadPoolMgr->WaitAllTaskFinish();
        LOGI("process delete task msg");
        if (!ProcessDelTask(pCmdMsg))
        {
            LOGE("process task delete msg failed");
            return SEND_NO;
        }

        break;

    // process message MSG_RECV_CHG_TASK
    case MSG_RECV_CHG_TASK:
        m_pThreadPoolMgr->WaitAllTaskFinish();
        LOGI("process change task msg");
        if (!ProcessChgTask(pCmdMsg))
        {
            LOGE("process task change msg failed");
            return SEND_NO;
        }

        break;

    // process message MSG_RECV_CONF_TASK
    case MSG_RECV_CONF_TASK:
        m_pThreadPoolMgr->WaitAllTaskFinish();
        LOGI("process refer task msg");
        if (!ProcessConfTask(pCmdMsg))
        {
            ReleaseReferTaskReger();
            LOGE("process task conf msg failed");
            return SEND_FALSE;
        }

        break;

        // other types are invalid
        // default:
        //     LOGW("recv cmd id %d is invalid, please check", static_cast<int>(uCmdID));
    }

    return SEND_TRUE;
}

// process message MSG_RECV_GROUP_ID
bool CTaskManager::ProcessGroupMsg(tagCmdMsg *pCmdMsg)
{
    // release previous task recognizers
    ReleaseGameTaskReger();
    tagAgentMsg *pMsg = dynamic_cast<tagAgentMsg*>(pCmdMsg);
    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::map<int, CTaskParam>::iterator  iterParam;
    std::map<int, TaskContext>::iterator iterCtx;

    // analyze message, abstract mapTaskParams and create Recognizer
    // type of all tasks in group message are TYPE_GAME
    for (iterParam = pMsg->mapTaskParams.begin(); iterParam != pMsg->mapTaskParams.end(); iterParam++)
    {
        int nTaskID = iterParam->first;
        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx == m_oMapTaskCtx.end())
        {
            TaskContext oTaskCtx;
            oTaskCtx.SetParam(iterParam->second);
            m_oMapTaskCtx[nTaskID] = oTaskCtx;
            m_oMapTaskCtx[nTaskID].SetTaskType(TYPE_GAME);
        }
        else
        {
            m_oMapTaskCtx[nTaskID].SetParam(iterParam->second);
            LOGW("there is already taskID  %d", nTaskID);
        }

        if (!m_oMapTaskCtx[nTaskID].CreateRecognizer(nTaskID))
        {
            LOGW("create recognizer failed");
            return false;
        }
    }

    // 根据refer任务来初始化游戏任务的状态
    // init object task base on refer task(load before)
    if (m_bMultiResolution)
    {
        InitGameTaskState();
    }

    return true;
}

// process message MSG_RECV_TASK_FLAG
bool CTaskManager::ProcessTaskFlag(tagCmdMsg *pCmdMsg)
{
    tagTaskFlagMsg *pMsg = dynamic_cast<tagTaskFlagMsg*>(pCmdMsg);

    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::map<int, bool> *pMapTaskFlag = &(pMsg->mapTaskFlag);

    if (pMapTaskFlag->size() <= 0)
    {
        LOGW("there is no flag");
        return false;
    }

    std::map<int, bool>::iterator        iter;
    std::map<int, TaskContext>::iterator iterCtx;

    for (iter = pMapTaskFlag->begin(); iter != pMapTaskFlag->end(); iter++)
    {
        int  nTaskID = iter->first;
        bool bFlag   = iter->second;

        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx == m_oMapTaskCtx.end())
        {
            LOGE("input taskID %d is invalid, please check", nTaskID);
            return false;
        }
        else
        {
            // update task flag
            iterCtx->second.SetStateSecond(bFlag);
        }

        if (m_bMultiResolution)
        {
            std::vector<int> nVecReferID;
            bool             bFlag = m_oMutiResMgr.GetReferTaskID(nTaskID, &nVecReferID);
            if (!bFlag)
            {
                LOGE("get referID failed, taskID: %d", nTaskID);
                return false;
            }

            for (size_t nIdx = 0; nIdx < nVecReferID.size(); ++nIdx)
            {
                iterCtx = m_oMapTaskCtx.find(nVecReferID[nIdx]);
                if (iterCtx == m_oMapTaskCtx.end())
                {
                    LOGE("input taskID %d is invalid, please check", nVecReferID[nIdx]);
                    return false;
                }
                else
                {
                    // update task flag
                    iterCtx->second.SetStateSecond(bFlag);
                }
            }
        }
    }

    return true;
}

// process message MSG_RECV_ADD_TASK
bool CTaskManager::ProcessAddTask(tagCmdMsg *pCmdMsg)
{
    tagAgentMsg *pMsg = dynamic_cast<tagAgentMsg*>(pCmdMsg);

    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::map<int, CTaskParam> *pMapTaskParams = &(pMsg->mapTaskParams);

    std::map<int, CTaskParam>::iterator  iterParam;
    std::map<int, TaskContext>::iterator iterCtx;

    for (iterParam = pMapTaskParams->begin(); iterParam != pMapTaskParams->end(); iterParam++)
    {
        int nTaskID = iterParam->first;
        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx == m_oMapTaskCtx.end())
        {
            // add this task and create recognizer
            // type of all tasks in Add task message are TYPE_GAME
            TaskContext oTaskCtx;
            oTaskCtx.SetParam(iterParam->second);
            m_oMapTaskCtx[nTaskID] = oTaskCtx;
            m_oMapTaskCtx[nTaskID].SetTaskType(TYPE_GAME);
            if (!m_oMapTaskCtx[nTaskID].CreateRecognizer(nTaskID))
            {
                LOGE("create recognizer failed");
                return false;
            }
        }
        else
        {
            // there is a task have same taskid, show a log and ignore the task
            LOGW("ntaskID %d is already exist", nTaskID);
            return false;
        }
    }

    return true;
}

// receive and process message MSG_RECV_DEL_TASK
bool CTaskManager::ProcessDelTask(tagCmdMsg *pCmdMsg)
{
    tagDelTaskMsg *pMsg = dynamic_cast<tagDelTaskMsg*>(pCmdMsg);

    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::vector<int> *pnVecTask = &(pMsg->nVecTask);

    std::map<int, TaskContext>::iterator iterCtx;

    for (size_t nIdx = 0; nIdx < pnVecTask->size(); nIdx++)
    {
        int nTaskID = pnVecTask->at(nIdx);
        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx != m_oMapTaskCtx.end())
        {
            // release the task recognizer and erase task from m_oMapTaskCtx
            iterCtx->second.Release();
            m_oMapTaskCtx.erase(iterCtx);
        }
        else
        {
            LOGW("find taskID %d failed, can not delete it", nTaskID);
            return false;
        }
    }

    return true;
}

// process message MSG_RECV_CHG_TASK
bool CTaskManager::ProcessChgTask(tagCmdMsg *pCmdMsg)
{
    tagAgentMsg *pMsg = dynamic_cast<tagAgentMsg*>(pCmdMsg);

    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::map<int, CTaskParam> *pMapTaskParams = &(pMsg->mapTaskParams);

    std::map<int, CTaskParam>::iterator  iterParam;
    std::map<int, TaskContext>::iterator iterCtx;

    for (iterParam = pMapTaskParams->begin(); iterParam != pMapTaskParams->end(); iterParam++)
    {
        int nTaskID = iterParam->first;

        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx != m_oMapTaskCtx.end())
        {
            // release previous task recognizer and erase task from m_oMapTaskCtx
            tagTaskState stTaskState = m_oMapTaskCtx[nTaskID].GetState();
            m_oMapTaskCtx[nTaskID].Release();
            m_oMapTaskCtx.erase(iterCtx);

            // add new task and create recognizer
            TaskContext oTaskCtx;
            oTaskCtx.SetParam(iterParam->second);
            m_oMapTaskCtx[nTaskID] = oTaskCtx;
            m_oMapTaskCtx[nTaskID].SetStateFirst(stTaskState.eTaskExecState);
            m_oMapTaskCtx[nTaskID].SetStateSecond(stTaskState.bState);
            m_oMapTaskCtx[nTaskID].SetTaskType(TYPE_GAME);
            if (!m_oMapTaskCtx[nTaskID].CreateRecognizer(nTaskID))
            {
                LOGW("create recognizer failed");
                return false;
            }
        }
        else
        {
            LOGW("can not find taskID %d task", nTaskID);
            return false;
        }
    }

    return true;
}

// process message MSG_RECV_CONF_TASK
bool CTaskManager::ProcessConfTask(tagCmdMsg *pCmdMsg)
{
    ReleaseReferTaskReger();
    tagConfTaskMsg *pMsg = dynamic_cast<tagConfTaskMsg*>(pCmdMsg);
    if (NULL == pMsg)
    {
        LOGE("pMsg is NULL");
        return false;
    }

    std::string strReferName;
    if (pMsg->strVecConfName.size() == 2)
    {
        strReferName = pMsg->strVecConfName[1];
    }
    else
    {
        LOGW("can not load refer name");
    }

    std::map<int, CTaskParam> mpTaskParam;
    // 读取refer任务配置文件，并获取其参数
    if (m_bMultiResolution)
    {
        m_oMutiResMgr.LoadReferConfFile(&mpTaskParam, strReferName);
    }

    std::map<int, CTaskParam>::iterator  iterParam;
    std::map<int, TaskContext>::iterator iterCtx;

    for (iterParam = mpTaskParam.begin(); iterParam != mpTaskParam.end(); iterParam++)
    {
        // if there is a task have same taskid, show a log and ignore the task
        // else add new task to m_oMapTaskCtx and create recognizer
        // type of all refer tasks are TYPE_REFER
        int nTaskID = iterParam->first;
        iterCtx = m_oMapTaskCtx.find(nTaskID);
        if (iterCtx == m_oMapTaskCtx.end())
        {
            TaskContext oTaskCtx;
            oTaskCtx.SetParam(iterParam->second);
            m_oMapTaskCtx[nTaskID] = oTaskCtx;
            m_oMapTaskCtx[nTaskID].SetTaskType(TYPE_REFER);
        }
        else
        {
            m_oMapTaskCtx[nTaskID].SetParam(iterParam->second);
            LOGW("there is already taskID  %d", nTaskID);
        }

        if (!m_oMapTaskCtx[nTaskID].CreateRecognizer(nTaskID))
        {
            LOGW("create recognizer failed");
            return false;
        }
    }

    // 根据refer任务来初始化游戏任务的状态

    if (m_bMultiResolution)
    {
        // update task state
        InitGameTaskState();
    }

    return true;
}

// get active task vector
std::vector<tagTask> CTaskManager::GetActiveTask(int nFrameSeq, tagRuntimeVar stRuntimeVar)
{
    std::vector<tagTask>                 oVecTask;
    std::map<int, TaskContext>::iterator iterCtx;

    tagTask stTask;

    for (iterCtx = m_oMapTaskCtx.begin(); iterCtx != m_oMapTaskCtx.end(); iterCtx++)
    {
        TaskContext *poTaskCtx = &(iterCtx->second);

        // if task state is active, get it and push it to oVecTask.
        if (poTaskCtx->GetState().IsActive())
        {
            stRuntimeVar.nTaskID = iterCtx->first;
//            stTask.nFrameSeq = poTaskCtx->GetFrameSeq();
            stTask.nLevel    = poTaskCtx->GetLevel();
            stTask.nOverload = poTaskCtx->GetOverload();
            stTask.ofunc     = boost::bind(&TaskContext::Process, poTaskCtx, stRuntimeVar);
            oVecTask.push_back(stTask);
        }
    }

    return oVecTask;
}

void CTaskManager::Release()
{
    // release game task recognizer
    ReleaseGameTaskReger();

    // release refer task recognizer
    ReleaseReferTaskReger();

    // free memory poll
    std::map<int, tagFrameResult>::iterator iter = m_mpFrameResult.begin();

    for (; iter != m_mpFrameResult.end(); ++iter)
    {
        iter->second.Release();
    }
}

// release game task recognizer
void CTaskManager::ReleaseGameTaskReger()
{
    if (m_oMapTaskCtx.size() == 0)
    {
        return;
    }

    std::map<int, TaskContext>::iterator iter;
    iter = m_oMapTaskCtx.begin();

    for (; iter != m_oMapTaskCtx.end();)
    {
        if (iter->second.GetTaskType() == TYPE_GAME)
        {
            iter->second.Release();
            // erase it from m_oMapTaskCtx
            iter = m_oMapTaskCtx.erase(iter);
        }
        else
        {
            ++iter;
        }
    }
}

// release refer task recognizer
void CTaskManager::ReleaseReferTaskReger()
{
    if (m_oMapTaskCtx.size() == 0)
    {
        return;
    }

    std::map<int, TaskContext>::iterator iter;
    iter = m_oMapTaskCtx.begin();

    for (; iter != m_oMapTaskCtx.end();)
    {
        if (iter->second.GetTaskType() == TYPE_REFER)
        {
            iter->second.Release();
            // erase it from m_oMapTaskCtx
            iter = m_oMapTaskCtx.erase(iter);
        }
        else
        {
            ++iter;
        }
    }
}

int CTaskManager::GetNumActiveCtx()
{
    int                                  nRes = 0;
    std::map<int, TaskContext>::iterator iter;

    iter = m_oMapTaskCtx.begin();

    for (; iter != m_oMapTaskCtx.end(); ++iter)
    {
        if (iter->second.GetState().IsActive())
        {
            ++nRes;
        }
    }

    return nRes;
}

void TransFixObjCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    // get result from pRegResult, update ROI parameters and szBBoxs parameters
    CFixObjRegResult *pFixObjRegResult = dynamic_cast<CFixObjRegResult*>(pRegResult);
    if (NULL == pFixObjRegResult)
    {
        LOGE("pFixObjRegResult is NULL");
        return;
    }

    int                nSize;
    tagFixObjRegResult *pstFixObjRegResult = pFixObjRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstFixObjRegResult[idx].oROI.x      /= fScale;
        pstFixObjRegResult[idx].oROI.y      /= fScale;
        pstFixObjRegResult[idx].oROI.width  /= fScale;
        pstFixObjRegResult[idx].oROI.height /= fScale;

        for (int nIdx = 0; nIdx < pstFixObjRegResult[idx].nBBoxNum; ++nIdx)
        {
            pstFixObjRegResult[idx].szBBoxes[nIdx].oRect.x      /= fScale;
            pstFixObjRegResult[idx].szBBoxes[nIdx].oRect.y      /= fScale;
            pstFixObjRegResult[idx].szBBoxes[nIdx].oRect.width  /= fScale;
            pstFixObjRegResult[idx].szBBoxes[nIdx].oRect.height /= fScale;
        }
    }
}

void TransPixRegCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CPixRegResult *pPixRegResult = dynamic_cast<CPixRegResult*>(pRegResult);
    if (NULL == pPixRegResult)
    {
        LOGE("pPixRegResult is NULL");
        return;
    }

    int             nSize;
    tagPixRegResult *pstPixRegResult = pPixRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        for (int nIdx = 0; nIdx < pstPixRegResult[idx].nPointNum; ++nIdx)
        {
            pstPixRegResult[idx].szPoints[nIdx].x /= fScale;
            pstPixRegResult[idx].szPoints[nIdx].y /= fScale;
        }
    }
}

void TransStuckRegCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CStuckRegResult *pStuckRegResult = dynamic_cast<CStuckRegResult*>(pRegResult);
    if (NULL == pStuckRegResult)
    {
        LOGE("pStuckRegResult is NULL");
        return;
    }

    int               nSize;
    tagStuckRegResult *pstStuckRegResult = pStuckRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstStuckRegResult[idx].oROI.x      /= fScale;
        pstStuckRegResult[idx].oROI.y      /= fScale;
        pstStuckRegResult[idx].oROI.width  /= fScale;
        pstStuckRegResult[idx].oROI.height /= fScale;
    }
}

void TransNumRegCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CNumRegResult *pNumRegResult = dynamic_cast<CNumRegResult*>(pRegResult);
    if (NULL == pNumRegResult)
    {
        LOGE("pNumRegResult is NULL");
        return;
    }

    int             nSize;
    tagNumRegResult *pstNumRegResult = pNumRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstNumRegResult[idx].oROI.x      /= fScale;
        pstNumRegResult[idx].oROI.y      /= fScale;
        pstNumRegResult[idx].oROI.width  /= fScale;
        pstNumRegResult[idx].oROI.height /= fScale;
    }
}

void TransDeformObjCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CDeformObjRegResult *pDeformRegResult = dynamic_cast<CDeformObjRegResult*>(pRegResult);
    if (NULL == pDeformRegResult)
    {
        LOGE("pDeformRegResult is NULL");
        return;
    }

    int                   nSize;
    tagDeformObjRegResult *pstDeformRegResult = pDeformRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        for (int nIdx = 0; nIdx < pstDeformRegResult[idx].nBBoxNum; ++nIdx)
        {
            pstDeformRegResult[idx].szBBoxes[nIdx].oRect.x      /= fScale;
            pstDeformRegResult[idx].szBBoxes[nIdx].oRect.y      /= fScale;
            pstDeformRegResult[idx].szBBoxes[nIdx].oRect.width  /= fScale;
            pstDeformRegResult[idx].szBBoxes[nIdx].oRect.height /= fScale;
        }
    }
}

void TransFixBloodRegCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CFixBloodRegResult *pFixBloodRegResult = dynamic_cast<CFixBloodRegResult*>(pRegResult);
    if (NULL == pFixBloodRegResult)
    {
        LOGE("pFixBloodRegResult is NULL");
        return;
    }

    int                  nSize;
    tagFixBloodRegResult *pstFixBloodRegResult = pFixBloodRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstFixBloodRegResult[idx].oROI.x      /= fScale;
        pstFixBloodRegResult[idx].oROI.y      /= fScale;
        pstFixBloodRegResult[idx].oROI.width  /= fScale;
        pstFixBloodRegResult[idx].oROI.height /= fScale;

        pstFixBloodRegResult[idx].oRect.x      /= fScale;
        pstFixBloodRegResult[idx].oRect.y      /= fScale;
        pstFixBloodRegResult[idx].oRect.width  /= fScale;
        pstFixBloodRegResult[idx].oRect.height /= fScale;
    }
}

void TransKGBloodCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CKingGloryBloodRegResult *pKingGloryBloodRegResult = dynamic_cast<CKingGloryBloodRegResult*>(pRegResult);
    if (NULL == pKingGloryBloodRegResult)
    {
        LOGE("pKingGloryBloodRegResult is NULL");
        return;
    }

    int                        nSize;
    tagKingGloryBloodRegResult *pstKingGloryBloodRegResult = pKingGloryBloodRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstKingGloryBloodRegResult[idx].oROI.x      /= fScale;
        pstKingGloryBloodRegResult[idx].oROI.y      /= fScale;
        pstKingGloryBloodRegResult[idx].oROI.width  /= fScale;
        pstKingGloryBloodRegResult[idx].oROI.height /= fScale;

        for (int nIdx = 0; nIdx < pstKingGloryBloodRegResult[idx].nBloodNum; ++nIdx)
        {
            pstKingGloryBloodRegResult[idx].szBloods[nIdx].oRect.x      /= fScale;
            pstKingGloryBloodRegResult[idx].szBloods[nIdx].oRect.y      /= fScale;
            pstKingGloryBloodRegResult[idx].szBloods[nIdx].oRect.width  /= fScale;
            pstKingGloryBloodRegResult[idx].szBloods[nIdx].oRect.height /= fScale;
        }
    }
}

void TransMapRegCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CMapRegResult *pMapRegResult = dynamic_cast<CMapRegResult*>(pRegResult);
    if (NULL == pMapRegResult)
    {
        LOGE("pMapRegResult is NULL");
        return;
    }

    int             nSize;
    tagMapRegResult *pstMapRegResult = pMapRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstMapRegResult[idx].oROI.x      /= fScale;
        pstMapRegResult[idx].oROI.y      /= fScale;
        pstMapRegResult[idx].oROI.width  /= fScale;
        pstMapRegResult[idx].oROI.height /= fScale;

        pstMapRegResult[idx].oViewAnglePoint.x /= fScale;
        pstMapRegResult[idx].oViewAnglePoint.y /= fScale;
        pstMapRegResult[idx].oMyLocPoint.x     /= fScale;
        pstMapRegResult[idx].oMyLocPoint.y     /= fScale;

        for (int nIdx = 0; nIdx < pstMapRegResult[idx].nFreindsPointNum; ++nIdx)
        {
            pstMapRegResult[idx].szFriendsLocPoints[nIdx].x /= fScale;
            pstMapRegResult[idx].szFriendsLocPoints[nIdx].y /= fScale;
        }
    }
}

void TransMapDirCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CMapDirectionRegResult *pMapRegResult = dynamic_cast<CMapDirectionRegResult*>(pRegResult);
    if (NULL == pMapRegResult)
    {
        LOGE("pMapRegResult is NULL");
        return;
    }

    int                      nSize;
    tagMapDirectionRegResult *pstMapRegResult = pMapRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstMapRegResult[idx].oROI.x      /= fScale;
        pstMapRegResult[idx].oROI.y      /= fScale;
        pstMapRegResult[idx].oROI.width  /= fScale;
        pstMapRegResult[idx].oROI.height /= fScale;

        pstMapRegResult[idx].oViewAnglePoint.x /= fScale;
        pstMapRegResult[idx].oViewAnglePoint.y /= fScale;
        pstMapRegResult[idx].oMyLocPoint.x     /= fScale;
        pstMapRegResult[idx].oMyLocPoint.y     /= fScale;
    }
}

void TransSGBloodCoor(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CShootGameBloodRegResult *pShootGameBloodRegResult = dynamic_cast<CShootGameBloodRegResult*>(pRegResult);
    if (NULL == pShootGameBloodRegResult)
    {
        LOGE("pShootGameBloodRegResult is NULL");
        return;
    }

    int                        nSize;
    tagShootGameBloodRegResult *pstShootGameBloodRegResult = pShootGameBloodRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstShootGameBloodRegResult[idx].oROI.x      /= fScale;
        pstShootGameBloodRegResult[idx].oROI.y      /= fScale;
        pstShootGameBloodRegResult[idx].oROI.width  /= fScale;
        pstShootGameBloodRegResult[idx].oROI.height /= fScale;

        pstShootGameBloodRegResult[idx].stBlood.oRect.x      /= fScale;
        pstShootGameBloodRegResult[idx].stBlood.oRect.y      /= fScale;
        pstShootGameBloodRegResult[idx].stBlood.oRect.width  /= fScale;
        pstShootGameBloodRegResult[idx].stBlood.oRect.height /= fScale;
    }
}

void TransSGHurt(IRegResult *pRegResult, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pRegResult)
    {
        LOGE("input pointer to regResult is NULL, please check");
        return;
    }

    CShootGameHurtRegResult *pShootGameHurtRegResult = dynamic_cast<CShootGameHurtRegResult*>(pRegResult);
    if (NULL == pShootGameHurtRegResult)
    {
        LOGE("pShootGameHurtRegResult is NULL");
        return;
    }

    int                       nSize;
    tagShootGameHurtRegResult *pstShootGameHurtRegResult = pShootGameHurtRegResult->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        pstShootGameHurtRegResult[idx].oROI.x      /= fScale;
        pstShootGameHurtRegResult[idx].oROI.y      /= fScale;
        pstShootGameHurtRegResult[idx].oROI.width  /= fScale;
        pstShootGameHurtRegResult[idx].oROI.height /= fScale;
    }
}
// proceed image is (1280, XXX), receieve image maybe not equal to it.
// so there is a need to transfer  coordinate result from processed image to receieve image
bool CTaskManager::TransCoor(tagFrameResult *pFrameResult)
{
    std::map<int, CTaskResult>::iterator iter = pFrameResult->mapTaskResult.begin();

    for (; iter != pFrameResult->mapTaskResult.end(); ++iter)
    {
        EREGTYPE   eType       = iter->second.GetType();
        IRegResult *pRegResult = iter->second.GetInstance(eType);
        float      fScale;
        if (m_nSrcWidth < m_nSrcHeight)
        {
            fScale = STANDARD_LONG_EDGE * 1.0f / m_nSrcHeight;
        }
        else
        {
            fScale = STANDARD_LONG_EDGE * 1.0f / m_nSrcWidth;
        }

        switch (eType)
        {
        // transfer  coordinate result from processed image to receieve image in task type TYPE_FIXOBJREG
        case TYPE_FIXOBJREG:
        {
            // get result from pRegResult, update ROI parameters and szBBoxs parameters
            TransFixObjCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_PIXREG
        case TYPE_PIXREG:
        {
            // get result from pRegResult, update szPoints parameters
            TransPixRegCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_STUCKREG
        case TYPE_STUCKREG:
        {
            // get result from pRegResult, update ROI parameters
            TransStuckRegCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_NUMBER
        case TYPE_NUMBER:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            TransNumRegCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_DEFORMOBJ
        case TYPE_DEFORMOBJ:
        {
            // get result from pRegResult, update szBBox(x, y, width, height) parameters
            TransDeformObjCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_FIXBLOOD
        case TYPE_FIXBLOOD:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // and Rect(x, y, width, height) parameters
            TransFixBloodRegCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_KINGGLORYBLOOD
        case TYPE_KINGGLORYBLOOD:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // and Rect(x, y, width, height) parameters
            TransKGBloodCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_MAPREG
        case TYPE_MAPREG:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // ViewAnglePoint(x, y) parameters
            // oMyLocPoint(x, y) parameters
            // szFriendsLocPoints(x, y) parameters
            TransMapRegCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_MAPDIRECTIONREG
        case TYPE_MAPDIRECTIONREG:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // oViewAnglePoint(x, y)parameters
            // oMyLocPoint(x, y)parameters
            TransMapDirCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_MULTCOLORVAR
        case TYPE_MULTCOLORVAR:
        {
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_SHOOTBLOOD
        case TYPE_SHOOTBLOOD:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // oRect(x, y, width, height)parameters
            TransSGBloodCoor(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_SHOOTHURT
        case TYPE_SHOOTHURT:
        {
            // get result from pRegResult, update ROI(x, y, width, height) parameters
            // oRect(x, y, width, height)parameters
            TransSGHurt(pRegResult, fScale);
            break;
        }

        // transfer  coordinate result from processed image to receieve image in task type TYPE_REFER_LOCATION
        // transfer  coordinate result from processed image to receieve image in task type TYPE_REFER_BLOODREG
        case TYPE_REFER_LOCATION:
        case TYPE_REFER_BLOODREG:
        {
            break;
        }

        // other types are invalid
        default:
        {
            LOGE("wrong REGTYPE, %d", static_cast<int>(eType));
            return false;
        }
        }
    }

    return true;
}

void CTaskManager::ShowResult(tagFrameResult *pFrameResult)
{
    cv::Mat tmpImg;

    if (m_bSendSDKTool)
    {
        tmpImg = pFrameResult->oFrame;
    }
    else
    {
        tmpImg = pFrameResult->oFrame.clone();
    }

    float fScale;
    if (m_nSrcWidth < m_nSrcHeight)
    {
        fScale = STANDARD_LONG_EDGE * 1.0f / m_nSrcHeight;
    }
    else
    {
        fScale = STANDARD_LONG_EDGE * 1.0f / m_nSrcWidth;
    }

    // draw rectange of roi area in tmpImage
    // draw task ID text in tmpImage
    ShowResultScale(&tmpImg, fScale);

    // draw recognize results in tmpImg
    ShowResultPlaint(&tmpImg, pFrameResult);
}

void ShowFixObjScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CFixObjRegParam *pFixObjRegParam = dynamic_cast<CFixObjRegParam*>(pRegParam);
    if (NULL == pFixObjRegParam)
    {
        LOGE("pFixObjRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pFixObjRegParam->m_oVecElements.size(); ++nIdx)
    {
        tagFixObjRegElement stFixObjRegElement = pFixObjRegParam->m_oVecElements[nIdx];
        std::string         strTmp;
        std::stringstream   sstream;
        // get taskID and transfer type from it to string
        // adjust parameters apply to standard images
        sstream << nID;
        sstream >> strTmp;
        cv::Rect ROI;
        ROI.x      = stFixObjRegElement.oROI.x /= fScale;
        ROI.y      = stFixObjRegElement.oROI.y /= fScale;
        ROI.width  = stFixObjRegElement.oROI.width /= fScale;
        ROI.height = stFixObjRegElement.oROI.height /= fScale;
        cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(ROI.x, ROI.y), \
                    cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 0, 255), 2);

        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowDeforObjScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CDeformObjRegParam *pDeformObjRegParam = dynamic_cast<CDeformObjRegParam*>(pRegParam);
    if (NULL == pDeformObjRegParam)
    {
        LOGE("pDeformObjRegParam is NULL");
        return;
    }


    for (size_t nIdx = 0; nIdx < pDeformObjRegParam->m_oVecElements.size(); ++nIdx)
    {
        tagDeformObjRegElement stDeformObjRegElement = pDeformObjRegParam->m_oVecElements[nIdx];
        std::string            strTmp;
        std::stringstream      sstream;
        // get taskID and transfer type from it to string
        // adjust parameters apply to standard images
        sstream << nID;
        sstream >> strTmp;
        cv::Rect ROI;
        ROI.x      = stDeformObjRegElement.oROI.x /= fScale;
        ROI.y      = stDeformObjRegElement.oROI.y /= fScale;
        ROI.width  = stDeformObjRegElement.oROI.width /= fScale;
        ROI.height = stDeformObjRegElement.oROI.height /= fScale;
        cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(ROI.x, ROI.y), \
                    cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 0, 255), 2);
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowPixRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CPixRegParam *pPixRegParam = dynamic_cast<CPixRegParam*>(pRegParam);
    if (NULL == pPixRegParam)
    {
        LOGE("pPixRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pPixRegParam->m_oVecElements.size(); ++nIdx)
    {
        tagPixRegElement  stPixRegElement = pPixRegParam->m_oVecElements[nIdx];
        std::string       strTmp;
        std::stringstream sstream;
        // get taskID and transfer type from it to string
        // adjust parameters apply to standard images
        sstream << nID;
        sstream >> strTmp;
        cv::Rect ROI;
        ROI.x      = stPixRegElement.oROI.x /= fScale;
        ROI.y      = stPixRegElement.oROI.y /= fScale;
        ROI.width  = stPixRegElement.oROI.width /= fScale;
        ROI.height = stPixRegElement.oROI.height /= fScale;
        cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(ROI.x, ROI.y), \
                    cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 0, 255), 2);
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowStuckRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CStuckRegParam *pStuckRegParam = dynamic_cast<CStuckRegParam*>(pRegParam);
    if (NULL == pStuckRegParam)
    {
        LOGE("pStuckRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pStuckRegParam->m_oVecElements.size(); ++nIdx)
    {
        tagStuckRegElement stStuckRegElement = pStuckRegParam->m_oVecElements[nIdx];
        std::string        strTmp;
        std::stringstream  sstream;
        // get taskID and transfer type from it to string
        // adjust parameters apply to standard images
        sstream << nID;
        sstream >> strTmp;
        cv::Rect ROI;
        ROI.x      = stStuckRegElement.oROI.x /= fScale;
        ROI.y      = stStuckRegElement.oROI.y /= fScale;
        ROI.width  = stStuckRegElement.oROI.width /= fScale;
        ROI.height = stStuckRegElement.oROI.height /= fScale;
        cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(ROI.x, ROI.y), \
                    cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 0, 255), 2);
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowNumberRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CNumRegParam *pNumRegParam = dynamic_cast<CNumRegParam*>(pRegParam);
    if (NULL == pNumRegParam)
    {
        LOGE("pNumRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pNumRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagNumRegElement stNumRegElement = pNumRegParam->m_oVecElements[nIdx];
        cv::Rect         ROI;
        ROI.x      = stNumRegElement.oROI.x /= fScale;
        ROI.y      = stNumRegElement.oROI.y /= fScale;
        ROI.width  = stNumRegElement.oROI.width /= fScale;
        ROI.height = stNumRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowFixBloodRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CFixBloodRegParam *pFixBloodRegParam = dynamic_cast<CFixBloodRegParam*>(pRegParam);
    if (NULL == pFixBloodRegParam)
    {
        LOGE("pFixBloodRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pFixBloodRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagFixBloodRegParam stFixBloodRegElement = pFixBloodRegParam->m_oVecElements[nIdx];
        cv::Rect            ROI;
        ROI.x      = stFixBloodRegElement.oROI.x /= fScale;
        ROI.y      = stFixBloodRegElement.oROI.y /= fScale;
        ROI.width  = stFixBloodRegElement.oROI.width /= fScale;
        ROI.height = stFixBloodRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowKGBloodReg(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CKingGloryBloodRegParam *pKingGloryBloodRegParam = dynamic_cast<CKingGloryBloodRegParam*>(pRegParam);
    if (NULL == pKingGloryBloodRegParam)
    {
        LOGE("pKingGloryBloodRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pKingGloryBloodRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagKingGloryBloodRegParam stKingGloryBloodRegElement = pKingGloryBloodRegParam->m_oVecElements[nIdx];
        cv::Rect                  ROI;
        ROI.x      = stKingGloryBloodRegElement.oROI.x /= fScale;
        ROI.y      = stKingGloryBloodRegElement.oROI.y /= fScale;
        ROI.width  = stKingGloryBloodRegElement.oROI.width /= fScale;
        ROI.height = stKingGloryBloodRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowMapRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CMapRegParam *pMapRegParam = dynamic_cast<CMapRegParam*>(pRegParam);
    if (NULL == pMapRegParam)
    {
        LOGE("pMapRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pMapRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagMapRegParam stMapRegElement = pMapRegParam->m_oVecElements[nIdx];
        cv::Rect       ROI;
        ROI.x      = stMapRegElement.oROI.x /= fScale;
        ROI.y      = stMapRegElement.oROI.y /= fScale;
        ROI.width  = stMapRegElement.oROI.width /= fScale;
        ROI.height = stMapRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowMapDirRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CMapDirectionRegParam *pMapRegParam = dynamic_cast<CMapDirectionRegParam*>(pRegParam);
    if (NULL == pMapRegParam)
    {
        LOGE("pMapRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pMapRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagMapDirectionRegParam stMapRegElement = pMapRegParam->m_oVecElements[nIdx];
        cv::Rect                ROI;
        ROI.x      = stMapRegElement.oROI.x /= fScale;
        ROI.y      = stMapRegElement.oROI.y /= fScale;
        ROI.width  = stMapRegElement.oROI.width /= fScale;
        ROI.height = stMapRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowSGBloodRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CShootGameBloodRegParam *pShootGameBloodRegParam = dynamic_cast<CShootGameBloodRegParam*>(pRegParam);
    if (NULL == pShootGameBloodRegParam)
    {
        LOGE("pShootGameBloodRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pShootGameBloodRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagShootGameBloodRegParam stShootGameBloodRegElement = pShootGameBloodRegParam->m_oVecElements[nIdx];
        cv::Rect                  ROI;
        ROI.x      = stShootGameBloodRegElement.oROI.x /= fScale;
        ROI.y      = stShootGameBloodRegElement.oROI.y /= fScale;
        ROI.width  = stShootGameBloodRegElement.oROI.width /= fScale;
        ROI.height = stShootGameBloodRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void ShowSGHurtRegScale(cv::Mat *pTmpImage, IRegParam  *pRegParam, const int nID, const float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegParam)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CShootGameHurtRegParam *pShootGameHurtRegParam = dynamic_cast<CShootGameHurtRegParam*>(pRegParam);
    if (NULL == pShootGameHurtRegParam)
    {
        LOGE("pShootGameHurtRegParam is NULL");
        return;
    }

    for (size_t nIdx = 0; nIdx < pShootGameHurtRegParam->m_oVecElements.size(); ++nIdx)
    {
        // adjust parameters apply to standard images
        tagShootGameHurtRegParam stShootGameHurtRegElement = pShootGameHurtRegParam->m_oVecElements[nIdx];
        cv::Rect                 ROI;
        ROI.x      = stShootGameHurtRegElement.oROI.x /= fScale;
        ROI.y      = stShootGameHurtRegElement.oROI.y /= fScale;
        ROI.width  = stShootGameHurtRegElement.oROI.width /= fScale;
        ROI.height = stShootGameHurtRegElement.oROI.height /= fScale;
        cv::rectangle(*pTmpImage, ROI, cv::Scalar(0, 0, 255), 2, 1, 0);
    }
}

void CTaskManager::ShowResultScale(cv::Mat *pTmpImage, float fScale)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    std::map<int, TaskContext>::iterator iterCtx = m_oMapTaskCtx.begin();

    for (; iterCtx != m_oMapTaskCtx.end(); ++iterCtx)
    {
        ETaskType    eTaskType   = iterCtx->second.GetTaskType();
        tagTaskState stTaskState = iterCtx->second.GetState();
        if (eTaskType == TYPE_GAME && stTaskState.IsActive())
        {
            CTaskParam *pParam    = iterCtx->second.GetParams();
            EREGTYPE   eRegType   = pParam->GetType();
            IRegParam  *pRegParam = pParam->GetInstance(eRegType);
            int        nID        = iterCtx->first;

            switch (eRegType)
            {
            // For type TYPE_FIXOBJREG: draw rectange of roi area and task ID text in image
            case TYPE_FIXOBJREG:
            {
                ShowFixObjScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_DEFORMOBJ: draw rectange of roi area and task ID text in image
            case TYPE_DEFORMOBJ:
            {
                ShowDeforObjScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_PIXREG: draw rectange of roi area and task ID text in image
            case TYPE_PIXREG:
            {
                ShowPixRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_STUCKREG: draw rectange of roi area and task ID text in image
            case TYPE_STUCKREG:
            {
                ShowStuckRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_NUMBER: draw rectange of roi area
            case TYPE_NUMBER:
            {
                ShowNumberRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_FIXBLOOD: draw rectange of roi area
            case TYPE_FIXBLOOD:
            {
                ShowFixBloodRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_KINGGLORYBLOOD: draw rectange of roi area
            case TYPE_KINGGLORYBLOOD:
            {
                ShowKGBloodReg(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_MAPREG: draw rectange of roi area
            case TYPE_MAPREG:
            {
                ShowMapRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_MAPDIRECTIONREG: draw rectange of roi area
            case TYPE_MAPDIRECTIONREG:
            {
                ShowMapDirRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_MULTCOLORVAR: show nothing
            case TYPE_MULTCOLORVAR:
            {
                break;
            }

            // For type TYPE_SHOOTBLOOD: draw rectange of roi area
            case TYPE_SHOOTBLOOD:
            {
                ShowSGBloodRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // For type TYPE_SHOOTHURT: draw rectange of roi area
            case TYPE_SHOOTHURT:
            {
                ShowSGHurtRegScale(pTmpImage, pRegParam, nID, fScale);
                break;
            }

            // other types are invalid
            default:
            {
                LOGE("wrong REGTYPE: %d", static_cast<int>(eTaskType));
                return;
            }
            }
        }
    }
}

void ShowFixObjectResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CFixObjRegResult *pFixObjRegRst = dynamic_cast<CFixObjRegResult*>(pRegResult);
    if (NULL == pFixObjRegRst)
    {
        LOGE("pFixObjRegRst is NULL");
        return;
    }

    int                nSize;
    tagFixObjRegResult *pszFixObjRes = pFixObjRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszFixObjRes[idx].nState)
        {
            for (int nIdx = 0; nIdx < pszFixObjRes[idx].nBBoxNum; ++nIdx)
            {
                std::string       strTmp;
                std::stringstream sstream;
                sstream << static_cast<float>(static_cast<int>(pszFixObjRes[idx].szBBoxes[nIdx].fScore * 100)) / 100;
                sstream >> strTmp;
                cv::putText(*pTmpImage, strTmp.c_str(),                               \
                            cv::Point(pszFixObjRes[idx].szBBoxes[nIdx].oRect.x - 5,   \
                                      pszFixObjRes[idx].szBBoxes[nIdx].oRect.y - 30), \
                            cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
                cv::putText(*pTmpImage, pszFixObjRes[idx].szBBoxes[nIdx].szTmplName,  \
                            cv::Point(pszFixObjRes[idx].szBBoxes[nIdx].oRect.x - 5,   \
                                      pszFixObjRes[idx].szBBoxes[nIdx].oRect.y - 10), \
                            cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
                cv::rectangle(*pTmpImage, pszFixObjRes[idx].szBBoxes[nIdx].oRect, \
                              cv::Scalar(0, 255, 0), 2, 1, 0);
            }
        }
    }
}

void ShowDeformObjResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CDeformObjRegResult *pDeformRegRst = dynamic_cast<CDeformObjRegResult*>(pRegResult);
    if (NULL == pDeformRegRst)
    {
        LOGE("pDeformRegRst is NULL");
        return;
    }

    int                   nSize;
    tagDeformObjRegResult *pszDeformRes = pDeformRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszDeformRes[idx].nState)
        {
            for (int nIdx = 0; nIdx < pszDeformRes[idx].nBBoxNum; ++nIdx)
            {
                cv::putText(*pTmpImage, pszDeformRes[idx].szBBoxes[nIdx].szTmplName,  \
                            cv::Point(pszDeformRes[idx].szBBoxes[nIdx].oRect.x - 5,   \
                                      pszDeformRes[idx].szBBoxes[nIdx].oRect.y - 10), \
                            cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
                cv::rectangle(*pTmpImage, pszDeformRes[idx].szBBoxes[nIdx].oRect, \
                              cv::Scalar(0, 255, 0), 2, 1, 0);
            }
        }
    }
}

void ShowPixRegResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CPixRegResult *pPixRegRst = dynamic_cast<CPixRegResult*>(pRegResult);
    if (NULL == pPixRegRst)
    {
        LOGE("pPixRegRst is NULL");
        return;
    }

    int             nSize;
    tagPixRegResult *pszPixRes = pPixRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszPixRes[idx].nState)
        {
            for (int nIdx = 0; nIdx < pszPixRes[idx].nPointNum; ++nIdx)
            {
                cv::circle(*pTmpImage, pszPixRes[idx].szPoints[nIdx], 1, cv::Scalar(0, 255, 0), 1, 1, 0);
            }
        }
    }
}

void ShowStuckReg(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CStuckRegResult *pStuckRegRst = dynamic_cast<CStuckRegResult*>(pRegResult);
    if (NULL == pStuckRegRst)
    {
        LOGE("pStuckRegRst is NULL");
        return;
    }

    int               nSize;
    tagStuckRegResult *pszStuckRes = pStuckRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszStuckRes[idx].nState)
        {
            cv::putText(*pTmpImage, "stuck", cv::Point(pTmpImage->cols / 2, pTmpImage->rows / 2), \
                        cv::FONT_HERSHEY_DUPLEX, 1.5, cv::Scalar(0, 255, 0), 2);
        }
    }
}

void ShowNumReg(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CNumRegResult *pNumRegRst = dynamic_cast<CNumRegResult*>(pRegResult);
    if (NULL == pNumRegRst)
    {
        LOGE("pNumRegRst is NULL");
        return;
    }

    int             nSize;
    tagNumRegResult *pszNumberRes = pNumRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszNumberRes[idx].nState)
        {
            std::string       strTmp;
            std::stringstream sstream;
            sstream << pszNumberRes[idx].fNum;
            sstream >> strTmp;
            cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(pszNumberRes[idx].oROI.x - 5,   \
                                                              pszNumberRes[idx].oROI.y - 10), \
                        cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
        }
    }
}

void ShowFixBlood(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CFixBloodRegResult *pFixBloodRegRst = dynamic_cast<CFixBloodRegResult*>(pRegResult);
    if (NULL == pFixBloodRegRst)
    {
        LOGE("pFixBloodRegRst is NULL");
        return;
    }

    int                  nSize;
    tagFixBloodRegResult *pszFixBloodRes = pFixBloodRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszFixBloodRes[idx].nState)
        {
            std::string       strTmp;
            std::stringstream sstream;
            sstream << pszFixBloodRes[idx].fPercent;
            sstream >> strTmp;
            cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(pszFixBloodRes[idx].oRect.x - 5,   \
                                                              pszFixBloodRes[idx].oRect.y - 10), \
                        cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
            cv::rectangle(*pTmpImage, pszFixBloodRes[idx].oRect, cv::Scalar(0, 255, 0), 2, 1, 0);
        }
    }
}

void ShowKingGloryBlood(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CKingGloryBloodRegResult *pKingGloryBloodRegRst = dynamic_cast<CKingGloryBloodRegResult*>(pRegResult);
    if (NULL == pKingGloryBloodRegRst)
    {
        LOGE("pKingGloryBloodRegRst is NULL");
        return;
    }

    int                        nSize;
    tagKingGloryBloodRegResult *pszKingGloryBloodRes = pKingGloryBloodRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszKingGloryBloodRes[idx].nState)
        {
            for (int nIdx = 0; nIdx < pszKingGloryBloodRes[idx].nBloodNum; ++nIdx)
            {
                std::string       strTmp;
                std::stringstream sstream;
                int               nValue = static_cast<int>(pszKingGloryBloodRes[idx].szBloods[nIdx].fPercent * 100);
                sstream << static_cast<float>(nValue) / 100;
                sstream >> strTmp;
                cv::putText(*pTmpImage, strTmp.c_str(),                                       \
                            cv::Point(pszKingGloryBloodRes[idx].szBloods[nIdx].oRect.x - 5,   \
                                      pszKingGloryBloodRes[idx].szBloods[nIdx].oRect.y - 30), \
                            cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
                cv::putText(*pTmpImage, pszKingGloryBloodRes[idx].szBloods[nIdx].szName,      \
                            cv::Point(pszKingGloryBloodRes[idx].szBloods[nIdx].oRect.x - 5,   \
                                      pszKingGloryBloodRes[idx].szBloods[nIdx].oRect.y - 10), \
                            cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
                cv::rectangle(*pTmpImage, pszKingGloryBloodRes[idx].szBloods[nIdx].oRect, \
                              cv::Scalar(0, 255, 0), 2, 1, 0);
            }
        }
    }
}

void ShowMapRegResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CMapRegResult *pMapRegRst = dynamic_cast<CMapRegResult*>(pRegResult);
    if (NULL == pMapRegRst)
    {
        LOGE("pMapRegRst is NULL");
        return;
    }

    int             nSize;
    tagMapRegResult *pszMapRes = pMapRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszMapRes[idx].nState)
        {
            if (pszMapRes[idx].oMyLocPoint.x != -1)
            {
                cv::circle(*pTmpImage, pszMapRes[idx].oMyLocPoint, 2, cv::Scalar(255, 255, 0), 1, 1, 0);
            }

            if (pszMapRes[idx].oViewLocPoint.x != -1)
            {
                cv::circle(*pTmpImage, pszMapRes[idx].oViewLocPoint, 2, cv::Scalar(0, 255, 0), 1, 1, 0);
            }

            if (pszMapRes[idx].oMyLocPoint.x != -1 && pszMapRes[idx].oViewLocPoint.x != -1)
            {
                cv::line(*pTmpImage, pszMapRes[idx].oMyLocPoint, \
                         pszMapRes[idx].oViewLocPoint, cv::Scalar(0, 255, 0), 2, CV_AA);
            }

            for (int nIdx = 0; nIdx < pszMapRes[idx].nFreindsPointNum; ++nIdx)
            {
                cv::circle(*pTmpImage, pszMapRes[idx].szFriendsLocPoints[nIdx], \
                           2, cv::Scalar(0, 255, 255), 1, 1, 0);
            }
        }
    }
}

void ShowMapDirRegResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CMapDirectionRegResult *pMapRegRst = dynamic_cast<CMapDirectionRegResult*>(pRegResult);
    if (NULL == pMapRegRst)
    {
        LOGE("pMapRegRst is NULL");
        return;
    }

    int                      nSize;
    tagMapDirectionRegResult *pszMapRes = pMapRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszMapRes[idx].nState)
        {
            if (pszMapRes[idx].oMyLocPoint.x != -1)
            {
                cv::circle(*pTmpImage, pszMapRes[idx].oMyLocPoint, 2, cv::Scalar(255, 255, 0), 1, 1, 0);
            }

            if (pszMapRes[idx].oViewLocPoint.x != -1)
            {
                cv::circle(*pTmpImage, pszMapRes[idx].oViewLocPoint, 2, cv::Scalar(0, 255, 0), 1, 1, 0);
            }

            if (pszMapRes[idx].oMyLocPoint.x != -1 && pszMapRes[idx].oViewLocPoint.x != -1)
            {
                cv::line(*pTmpImage, pszMapRes[idx].oMyLocPoint, pszMapRes[idx].oViewLocPoint, \
                         cv::Scalar(0, 255, 0), 2, CV_AA);
            }
        }
    }
}

void ShowMultiColorVar(cv::Mat *pTmpImage, IRegResult *pRegResult, const int nWidth, const int nHeight)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CMultColorVarRegResult *pMultColorVarRegRst = dynamic_cast<CMultColorVarRegResult*>(pRegResult);
    if (NULL == pMultColorVarRegRst)
    {
        LOGE("pMultColorVarRegRst is NULL");
        return;
    }

    int                      nSize;
    tagMultColorVarRegResult *pszMultColorVarRes = pMultColorVarRegRst->GetResult(&nSize);
    if (NULL == pszMultColorVarRes)
    {
        LOGE("pszMultColorVarRes is NULL");
        return;
    }

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszMultColorVarRes[idx].nState)
        {
            float fTempRes = pszMultColorVarRes[idx].colorMeanVar[0];
            int   nRes     = 0;

            for (size_t nIdx = 1; nIdx < DIRECTION_SIZE; ++nIdx)
            {
                if (fTempRes > pszMultColorVarRes[idx].colorMeanVar[nIdx])
                {
                    fTempRes = pszMultColorVarRes[idx].colorMeanVar[nIdx];
                    nRes     = nIdx;
                }
            }

            std::string       strTmp;
            std::stringstream sstream;
            sstream << nRes;
            sstream >> strTmp;
            cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(nWidth / 2, nHeight / 2), \
                        cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
        }
    }
}

void ShowSGBloodRegResult(cv::Mat *pTmpImage, IRegResult *pRegResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CShootGameBloodRegResult *pShootGameBloodRegRst = dynamic_cast<CShootGameBloodRegResult*>(pRegResult);
    if (NULL == pShootGameBloodRegRst)
    {
        LOGE("pShootGameBloodRegRst is NULL");
        return;
    }

    int                        nSize;
    tagShootGameBloodRegResult *pszShootGameBloodRes = pShootGameBloodRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszShootGameBloodRes[idx].nState)
        {
            std::string       strTmp;
            std::stringstream sstream;
            sstream << pszShootGameBloodRes[idx].stBlood.fPercent;
            sstream >> strTmp;
            cv::putText(*pTmpImage, strTmp.c_str(), cv::Point(pszShootGameBloodRes[idx].oROI.x - 5,   \
                                                              pszShootGameBloodRes[idx].oROI.y - 10), \
                        cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
            cv::rectangle(*pTmpImage, pszShootGameBloodRes[idx].stBlood.oRect, cv::Scalar(0, 255, 0), 2, 1, 0);
        }
    }
}

void ShowShootHurtResult(cv::Mat *pTmpImage, IRegResult *pRegResult, const int nSrcWdith, const int nSrcHeight)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pRegResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    CShootGameHurtRegResult *pShootGameHurtRegRst = dynamic_cast<CShootGameHurtRegResult*>(pRegResult);
    if (NULL == pShootGameHurtRegRst)
    {
        LOGE("pShootGameHurtRegRst is NULL");
        return;
    }

    int                       nSize;
    tagShootGameHurtRegResult *pszShootGameHurtRes = pShootGameHurtRegRst->GetResult(&nSize);

    for (int idx = 0; idx < nSize; ++idx)
    {
        if (pszShootGameHurtRes[idx].nState)
        {
            cv::putText(*pTmpImage, "get hurt", cv::Point(nSrcWdith / 2, nSrcHeight / 2), \
                        cv::FONT_HERSHEY_DUPLEX, 0.7, cv::Scalar(0, 255, 0), 2);
        }
    }
}
void CTaskManager::ShowResultPlaint(cv::Mat *pTmpImage, tagFrameResult *pFrameResult)
{
    // 检查传入参数的合法性
    if (NULL == pTmpImage || NULL == pFrameResult)
    {
        LOGE("input pointer is NULL, please check");
        return;
    }

    std::map<int, CTaskResult>::iterator iter = pFrameResult->mapTaskResult.begin();

    for (; iter != pFrameResult->mapTaskResult.end(); ++iter)
    {
        EREGTYPE   eType       = iter->second.GetType();
        IRegResult *pRegResult = iter->second.GetInstance(eType);

        switch (eType)
        {
        // For type TYPE_FIXOBJREG: draw result of fScore in image
        // draw TmplName in image
        // draw result rectangle locations in image
        case TYPE_FIXOBJREG:
        {
            ShowFixObjectResult(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_DEFORMOBJ: draw result of TmplName in image
        // draw result of object rectangle locations in image
        case TYPE_DEFORMOBJ:
        {
            ShowDeformObjResult(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_PIXREG: draw result of object point in image
        case TYPE_PIXREG:
        {
            ShowPixRegResult(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_STUCKREG: draw text of "stuck" in image if state is not 0
        case TYPE_STUCKREG:
        {
            ShowStuckReg(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_NUMBER: draw result of Num value in image
        case TYPE_NUMBER:
        {
            ShowNumReg(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_FIXBLOOD: draw result of blood percent in image
        case TYPE_FIXBLOOD:
        {
            ShowFixBlood(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_KINGGLORYBLOOD: draw result of blood percent in image
        // draw result of blood percent in image
        // draw result of blood class name in image
        // draw result of blood rectangle location in image
        case TYPE_KINGGLORYBLOOD:
        {
            ShowKingGloryBlood(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_MAPREG: draw result of MyLocPoint in image
        // draw result of ViewLocPoint in image
        // draw result of FreindsPoint in image
        case TYPE_MAPREG:
        {
            ShowMapRegResult(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_MAPDIRECTIONREG: draw result of MyLocPoint in image
        // draw result of ViewLocPoint in image
        // draw result of FreindsPoint in image
        case TYPE_MAPDIRECTIONREG:
        {
            ShowMapDirRegResult(pTmpImage, pRegResult);
            break;
        }

        // For type TYPE_MULTCOLORVAR: draw result ID value in image
        case TYPE_MULTCOLORVAR:
        {
            ShowMultiColorVar(pTmpImage, pRegResult, m_nSrcWidth, m_nSrcHeight);
            break;
        }

        // For type TYPE_SHOOTBLOOD: draw result of blood percent in image
        // draw result of blood rectangle location in image
        case TYPE_SHOOTBLOOD:
        {
            ShowMultiColorVar(pTmpImage, pRegResult, m_nSrcWidth, m_nSrcHeight);
            break;
        }

        // For type TYPE_SHOOTHURT: putText "get hurt" in image if state is not 0
        case TYPE_SHOOTHURT:
        {
            ShowShootHurtResult(pTmpImage, pRegResult, m_nSrcWidth, m_nSrcHeight);
            break;
        }

        // For type TYPE_REFER_LOCATION , there is no show
        // For type TYPE_REFER_BLOODREG , there is no show
        case TYPE_REFER_LOCATION:
        case TYPE_REFER_BLOODREG:
        {
            break;
        }

        // other types are invalid
        default:
        {
            LOGE("wrong REGTYPE: %d", static_cast<int>(eType));
            return;
        }
        }
    }

    if (!m_bSendSDKTool)
    {
        cv::imshow("result", *pTmpImage);
        cv::waitKey(1);
    }
}
