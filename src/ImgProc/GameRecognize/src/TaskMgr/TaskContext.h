/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_CONTEXT_H_
#define TASK_CONTEXT_H_

#include <boost/thread/mutex.hpp>
#include <iostream>
#include <vector>

#include "Comm/Os/TqcOs.h"
#include "Comm/Utils/TqcThreadSafeQueue.h"
#include "GameRecognize/src/TaskMgr/TaskMessage.h"
#include "GameRecognize/src/TaskMgr/TaskResult.h"


/*!
@class : TaskContext
@brief : 任务的内容维护模块
*/

class TaskContext
{
public:
    TaskContext();
    ~TaskContext();

    /*!
    * @brief 获取任务参数
    * @return 任务参数(taskID, 识别类型，识别初始化所需要的参数)
    */
    CTaskParam* GetParams();

    /*!
    * @brief 设置任务参数
    * @param[in] 任务参数(taskID, 识别类型，识别初始化所需要的参数)
    * @return 任务参数
    */
    void SetParam(const CTaskParam &stParms);

    /*!
    * @brief 获取当前任务对应的识别器
    */
    IRecognizer* GetRecognizer();

    /*!
    * @brief 创建当前任务对应的识别器
    * @param[in] nTaskID
    */
    bool CreateRecognizer(int nTaskID);

	/*!
	 * @brief 释放上线文资源
	 */
    void Release();

    /*!
    * @brief 释放当前任务对应的识别器
    */
    void ReleaseRecognizer();

    /*!
    * @brief 获取当前任务的状态(TASK_RUNNING 和 true时, 需要执行;其他状态时, 暂时关闭)
    */
    tagTaskState GetState();

    /*!
    * @brief 设置当前任务的状态1
    */
    void SetStateFirst(ETaskExecState eState);

    /*!
    * @brief 设置当前任务的状态2
    */
    void SetStateSecond(bool bState);

    /*!
    * @brief 获取当前任务的等级
    */
    int GetLevel();

    /*!
    * @brief 设置当前任务的等级
    */
    void SetLevel(int nLevel);

    /*!
    * @brief 获取当前任务的overload
    */
    int GetOverload();

    /*!
    * @brief 设置当前任务的overload
    */
    void SetOverload(int nOverLoad);

    /*!
     * @brief 设置任务类别
     * @param eTaskType TYPE_REFER或者TYPE_GAME
     */
    void SetTaskType(ETaskType eTaskType);

    /*!
     * @brief 获取任务类别
     * @return TYPE_REFER或者TYPE_GAME
     */
    ETaskType GetTaskType();

    /*!
    * @brief 根据当前任务的识别器，处理当前帧，并保存结果
    */
    bool Process(tagRuntimeVar stRuntimeVar);

private:
    ETaskType    m_eTaskType;   // 任务类别（TASK_REFER表示参考任务，TASK_GAME表示游戏任务）
    int          m_nLevel;      // 任务级别
    int          m_nOverload;   // 任务负载
    tagTaskState m_stState;     // 任务状态
    CTaskParam m_stParms;       // 参数
    IRecognizer *m_pRecognizer; // 识别器
    bool         m_bSendResult;
};

#endif // TASK_CONTEXT_H_
