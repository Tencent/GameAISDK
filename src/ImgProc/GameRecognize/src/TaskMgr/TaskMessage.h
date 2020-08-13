/*
 * This source code file is licensed under the GNU General Public License Version 3.
 * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
 * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
 */

#ifndef TASK_MESSAGE_H_
#define TASK_MESSAGE_H_

#include <iostream>
#include <map>
#include <memory>
#include <vector>

#include "GameRecognize/src/TaskMgr/TaskDefine.h"


/*!
@class : CTaskMessage
@brief : 任务的消息模块
*/

class CTaskMessage
{
public:
    CTaskMessage();
    virtual ~CTaskMessage();

public:

    /*!
    * @brief 获取消息句柄
    * @param[in] eMsgID 消息类型
    * @return 消息句柄
    */
    tagCmdMsg *GetInstance(const EAgentMsgID eMsgID);

    /*!
    * @brief 设置消息类型
    * @param[in] eMsgID 消息类型
    */
    void SetMsgType(const EAgentMsgID eMsgID);

    /*!
    * @brief 获取消息类型
    */
    EAgentMsgID GetMsgType();

    void Release();

private:
    /*!
    * @brief 创建组任务消息
    */
    void CreateGroupMsg();

    /*!
    * @brief 创建 任务是否关闭消息
    */
    void CreateFlagMsg();

    /*!
    * @brief 创建 增加任务消息
    */
    void CreateAddTaskMsg();

    /*!
    * @brief 创建 删除任务消息
    */
    void CreateDelTaskMsg();

    /*!
    * @brief 创建 改变任务消息
    */
    void CreateChgTaskMsg();

    /*!
    * @brief 创建 配置文件任务消息
    */
    void CreateConfTaskMsg();

private:
    tagCmdMsg *m_pCmdMsg;      // 任务消息指针
    EAgentMsgID m_EAgentMsgID; // 消息类型
};

#endif // TASK_MESSAGE_H_
