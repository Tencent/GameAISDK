/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_MANAGER_H_
#define TASK_MANAGER_H_

#include <map>
#include <queue>
#include <vector>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/GameTime.h"
#include "GameRecognize/src/TaskMgr/TaskContext.h"
#include "GameRecognize/src/TaskMgr/TaskDataDeal.h"
#include "GameRecognize/src/TaskMgr/TaskMultiResMgr.h"
/*!
@class : CTaskManager
@brief : 任务的管理模块
*/

class CTaskManager
{
public:
    CTaskManager();
    ~CTaskManager();
    /*!
    * @brief 初始化，读取识别模块的平台配置文件
    * @param[in] pThreadPoolMgr 线程池指针
    * @param[in] bSendSDKTool 是否给SDKTool发送结果
    * @param[in] bMultiResolution 是否进行多分辨率处理
    * @return True 成功， False失败
    */
    bool Initialize(CThreadPoolMgr *pThreadPoolMgr, bool bSendSDKTool, bool bMultiResolution);

    /*!
    * @brief  获取所有任务的识别结果
    * @param[out] pFrameResult 识别结果
    * @param[in] nTimeOutMS 超时时间
    * @return True 成功， False失败
    */
    bool GetResult(tagFrameResult *pFrameResult, int nFrameSeq, int nTimeOutMS = 4000);

    /*!
    * @brief  获取需要执行的任务列表
    * @return 任务列表，没有时为空
    */
    std::vector<tagTask> GetActiveTask(int nFrameSeq, tagRuntimeVar stRuntimeVar);

    /*!
     * @brief 更新Task任务
     * @param[in] oVecTaskMsg 可执行的任务
     * @param[in] stSrcImageInfo 传入的命令消息列表
     * @param[out] pVecMsg 给threadpool用的任务
     * @param[out] pFrameResult 每帧的结果
     * @param[out] peSendTaskReportToMC 是否发送初始化成功给MC
     * @return 0表示全都没有工作，1表示至少一项做了工作
     */
    int Update(const std::vector<CTaskMessage> &oVecTaskMsg, const tagSrcImgInfo &stSrcImageInfo, \
               std::vector<tagTask> *pVecRst, \
               tagFrameResult *pFrameResult, ESendTaskReportToMC *peSendTaskReportToMC);

    /*!
    * @brief  释放所有的游戏任务识别器
    */
    void ReleaseGameTaskReger();

    /*!
    * @brief  释放所有的参考任务识别器
    */
    void ReleaseReferTaskReger();

    /*!
     * @brief 是否应该release
     * return true or false
     */
    bool GetSholdRelease(){ return m_bShouldRelease;}

    /*!
     * @brief 释放资源
     */
    void Release();

    /*!
     * @brief 设置测试模式
     */
    void SetTestMode(bool bDebug, ETestMode eTestMode);


private:

    void ShowResultScale(cv::Mat *pTmpImage, float fScale);

    void ShowResultPlaint(cv::Mat *pTmpImage, tagFrameResult *pFrameResult);

    /*!
     * @brief 坐标转换
     * @param[in] pFrameResult
     * return true or false
     */
    bool TransCoor(tagFrameResult *pFrameResult);

    /*!
    * @brief  根据收到的消息，更新任务
    * @param[in] pVecTaskMsg 传入的命令消息列表
    * @return ESendTaskReportToMC 发送给MC的状态类型
    */
    ESendTaskReportToMC UpdateTaskInfo(const std::vector<CTaskMessage> *pVecTaskMsg);

    /*!
     * @brief 获取当前可执行的任务
     * @return int
     */
    int GetNumActiveCtx();

    /*!
    * @brief  根据某一个消息更新任务
    * @param[in] pMsg 收到的命令消息
    * @return ESendTaskReportToMC 发送给MC的状态类型
    */
    ESendTaskReportToMC UpdateOneMsg(CTaskMessage *pMsg);

    /*!
    * @brief  处理 重置一个group的消息
    * @param[in] pCmdMsg 收到的组任务消息
    * @return True 成功， False失败
    */
    bool ProcessGroupMsg(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  处理 任务是否关闭的消息
    * @param[in] pCmdMsg 收到的任务是否开关的消息
    * @return
    */
    bool ProcessTaskFlag(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  处理 增加任务的消息
    * @param[in] pCmdMsg 收到的增加任务的消息
    * @return
    */
    bool ProcessAddTask(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  处理 删除任务的消息
    * @param[in] pCmdMsg 收到的删除任务的消息
    * @return
    */
    bool ProcessDelTask(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  处理 改变任务的消息
    * @param[in] pCmdMsg 收到的改变任务的消息
    * @return
    */
    bool ProcessChgTask(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  处理 配置文件任务的消息
    * @param[in] pCmdMsg 收到的配置文件任务的消息
    * @return
    */
    bool ProcessConfTask(tagCmdMsg *pCmdMsg);

    /*!
    * @brief  显示识别结果
    * @param[in] pFrameResult 识别结果
    */
    void ShowResult(tagFrameResult *pFrameResult);

    /*!
     * @brief 根据参考任务来初始化游戏任务的状态
     */
    void InitGameTaskState();

private:
    int m_nSrcWidth;                                // 原图像的宽，用于坐标转换
    int m_nSrcHeight;                               // 原图像的高，用于坐标转换

    CThreadPoolMgr *m_pThreadPoolMgr;               // 线程池

    CMutiResMgr m_oMutiResMgr;                      // 多分辨率处理
    std::queue<int> m_ResFrameSeqQueue;             // 结果帧序号队列
    int m_nLastTimeMS;                              // 上次获取结果时的系统时间，单位ms
    int m_nOutTimeMS;                               // 已用时间，单位ms
    std::map<int, tagFrameResult> m_mpFrameResult;
    std::map<int, TaskContext> m_oMapTaskCtx;       // 所有任务的上下文， key为taskID.
    bool  m_bShowSrcImage;                          // 显示当前收到的帧
    bool  m_bShowResult;                            // 显示结果
    int   m_nMaxResSize;                            // 最大并发的帧数（结果队列的大小）
    bool  m_bMultiResolution;                       // 是否进行多分辨率处理
    TaskDataDeal oTaskDataDeal;
    bool m_bShouldRelease;                          // 是否应该release
    bool m_bSendSDKTool;                            // 是否给SDKTool发送结果
};
#endif // TASK_MANAGER_H_
